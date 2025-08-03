import asyncio
import json
import logging
from datetime import datetime
from typing import Dict,  Optional, Set
from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import decode_token
from app.models.test import TestStatus
from app.repositories import user_repo
from app.repositories.test_repo import TestRepository
from app.repositories.assessment_repo import AssessmentRepository
from app.repositories.candidate_application_repo import CandidateApplicationRepository

logger = logging.getLogger(__name__)


class ConnectionState:

    def __init__(self, websocket: WebSocket, user_id: int, test_id: Optional[int] = None):
        self.websocket = websocket
        self.user_id = user_id
        self.test_id = test_id
        self.connected_at = datetime.now()
        self.last_activity = datetime.now()
        self.assessment_started_at: Optional[datetime] = None
        self.assessment_id: Optional[int] = None

        self.thread_id: Optional[str] = None
        self.is_authenticated = False
        self.is_in_assessment = False
        self.graph_initialized = False

    def update_activity(self):
        """
        Update the last activity timestamp

        This method should be called whenever any activity occurs on the connection
        (receiving messages, sending responses). It's used by the cleanup task to
        identify inactive connections that should be removed.
        """
        self.last_activity = datetime.utcnow()

    def start_assessment(self, test_id: int, assessment_id: int):
        """
        Mark the start of an assessment with actual assessment instance ID

        This method transitions the connection into assessment mode, storing the
        test blueprint ID and the specific assessment instance ID from the database.
        The assessment_id is also used as the thread_id for graph state persistence.

        Args:
            test_id: The test blueprint ID (defines questions, time limit, etc.)
            assessment_id: The specific assessment instance ID (tracks this user's attempt)
        """
        self.test_id = test_id
        self.assessment_id = assessment_id
        # Use assessment_id as thread_id for graph state persistence
        self.thread_id = str(assessment_id)
        self.assessment_started_at = datetime.utcnow()
        self.is_in_assessment = True

    def end_assessment(self):
        """
        Mark the end of an assessment

        This method transitions the connection out of assessment mode. The assessment_id
        and test_id are preserved for potential recovery scenarios, but is_in_assessment
        is set to False to indicate the session is no longer active.
        """
        self.is_in_assessment = False


class WebSocketConnectionManager:
    """
    Manages WebSocket connections for the assessment system

    This is the central orchestrator for all WebSocket connections in the application.
    It handles authentication, connection lifecycle, state management, and provides
    utilities for message routing and broadcast capabilities.

    CONNECTION IDENTITY STRATEGY:
    This system uses a consistent connection_id format throughout the connection lifecycle:
    - Format: "{user_id}_{test_id}" for assessment connections
    - Format: "{user_id}_general" for general connections without specific test
    - This enables robust state recovery across reconnections for the same user/test combination

    Key responsibilities:
    - Authenticate and establish secure connections
    - Enforce connection consistency per user/test combination
    - Track connection state and user sessions  
    - Manage assessment session lifecycle
    - Enable message routing (personal, assessment-wide)
    - Automatic cleanup of inactive connections
    - Support seamless reconnection with state recovery

    Data Structures:
    - active_connections: Maps connection_id -> ConnectionState
    - user_connections: Maps user_id -> connection_id (current active connection per user)    - assessment_sessions: Maps test_id -> Set[connection_ids] (assessment participants)
    """

    def __init__(self):
        # Active connections indexed by connection_id
        # Format: "{user_id}_{test_id}" -> ConnectionState
        self.active_connections: Dict[str, ConnectionState] = {}

        # Current active connection per user - maps user_id to connection_id
        # Allows tracking the most recent connection for each user
        self.user_connections: Dict[int, str] = {}

        # Assessment sessions - maps test_id to active connection_ids
        # Enables broadcasting messages to all participants in an assessment
        self.assessment_sessions: Dict[int, Set[str]] = {}

        # Connection cleanup interval (in seconds)
        # 5 minutes        # Maximum idle time before connection cleanup (in seconds)
        self.cleanup_interval = 300
        self.max_idle_time = 1800  # 30 minutes

        # Start cleanup task
        asyncio.create_task(self._cleanup_inactive_connections())

    async def authenticate_connection(self, websocket: WebSocket, token: str) -> Optional[int]:
        """
        Authenticate WebSocket connection using JWT token

        This method validates the provided JWT token and extracts the user identity.
        It's the first step in the connection establishment process.

        Args:
            websocket: The WebSocket connection object
            token: JWT token containing user credentials

        Returns:
            user_id if authentication successful, None otherwise

        Security Note:
            This method only validates the token structure and signature.
            Additional validation (user existence, account status) should be
            added based on business requirements.
        """
        try:
            payload = decode_token(token)
            print(f"Decoded token payload: {payload}")
            if not payload:
                print(
                    "Invalid token provided for WebSocket authentication")
                return None

            # Check for user_id first (new token format)
            user_id = payload.get("user_id")
            if user_id:
                print(f"found user_id in token payload: {user_id}")
                return user_id
            return None

        except Exception as e:
            logger.error(f"Error during WebSocket authentication: {str(e)}")
            return None

    async def connect(self, websocket: WebSocket, user_id: int, test_id: Optional[int] = None, db: Optional[AsyncSession] = None) -> str:
        # Generate connection ID using user_id and test_id
        if not test_id:
            logger.error(f"Cannot Start Assessment without the test_id")
        if not user_id:
            logger.error(f"Cannot Start the assessment without user_id")
        connection_id = f"{user_id}_{test_id}"

        # Check for existing connection with same connection_id and disconnect it
        if connection_id in self.active_connections:
            logger.info(
                f"Disconnecting existing connection {connection_id} for user {user_id}")
            await self.disconnect(connection_id)

        await websocket.accept()

        # Create connection state object
        connection_state = ConnectionState(websocket, user_id, test_id)

        connection_state.is_authenticated = True

        # Store in primary connection registry
        self.active_connections[connection_id] = connection_state

        # Store single connection per user (update to allow multiple tests per user)
        self.user_connections[user_id] = connection_id

        # If joining an assessment, add to assessment session tracking and check for existing assessment
        if test_id:
            if test_id not in self.assessment_sessions:
                self.assessment_sessions[test_id] = set()
            self.assessment_sessions[test_id].add(connection_id)

            # Auto-recover existing assessment session if available
            if db is not None:
                existing_assessment_id = await self.check_existing_assessment(user_id, test_id, db)
                if existing_assessment_id:
                    logger.info(
                        f"Auto-recovering assessment {existing_assessment_id} for reconnection {connection_id}")
                    recovery_success = await self.recover_assessment_session(connection_id, existing_assessment_id, db)
                    if recovery_success:
                        logger.info(
                            f"Successfully auto-recovered assessment state for {connection_id}")
                    else:
                        logger.warning(
                            f"Failed to auto-recover assessment state for {connection_id}")

        logger.info(
            f"WebSocket connection established: {connection_id} (user: {user_id}, test: {test_id})")
        return connection_id

    async def disconnect(self, connection_id: str):
        """
        Disconnect and clean up a WebSocket connection

        This method handles both graceful disconnections (user closes browser) and
        ungraceful disconnections (network issues, timeouts). It ensures all
        tracking data structures are properly cleaned up to prevent memory leaks.

        Args:
            connection_id: The connection identifier to disconnect

        Cleanup Process:
        1. Remove from active_connections registry
        2. Remove from user_connections mapping  
        3. Remove from assessment_sessions if in assessment
        4. Clean up empty sets to prevent memory accumulation
        """
        if connection_id not in self.active_connections:
            return

        connection_state = self.active_connections[connection_id]
        user_id = connection_state.user_id
        test_id = connection_state.test_id

        # Close the WebSocket connection if still open
        try:
            await connection_state.websocket.close()
        except Exception:
            pass  # Connection might already be closed

        # Remove from active connections registry
        # Clean up user connection mapping
        del self.active_connections[connection_id]
        # Only remove if this connection_id matches the current active connection for the user
        if user_id in self.user_connections and self.user_connections[user_id] == connection_id:
            del self.user_connections[user_id]

        # Clean up assessment session tracking
        if test_id and test_id in self.assessment_sessions:
            self.assessment_sessions[test_id].discard(connection_id)
            # Remove empty sets to prevent memory accumulation
            if not self.assessment_sessions[test_id]:
                del self.assessment_sessions[test_id]

        logger.info(f"WebSocket connection closed: {connection_id}")

    async def send_personal_message(self, connection_id: str, message: dict):
        """Send a message to a specific connection"""
        if connection_id not in self.active_connections:
            logger.warning(
                f"Attempted to send message to non-existent connection: {connection_id}")
            return False

        try:
            connection_state = self.active_connections[connection_id]
            connection_state.update_activity()

            await connection_state.websocket.send_text(json.dumps(message))
            return True

        except Exception as e:
            logger.error(f"Error sending message to {connection_id}: {str(e)}")
            await self.disconnect(connection_id)
            return False

    async def send_to_user(self, user_id: int, message: dict):
        """
        Send a message to the user's active connection

        Since we enforce single connection per user, this method sends the message
        to the user's one active connection if it exists.

        Args:
            user_id: ID of the user to send message to
            message: Dictionary containing the message data

        Returns:
            1 if message sent successfully, 0 if user has no active connection
        """
        if user_id not in self.user_connections:
            return 0

        connection_id = self.user_connections[user_id]
        if await self.send_personal_message(connection_id, message):
            return 1
        return 0

    def get_connection_info(self, connection_id: str) -> Optional[Dict]:
        """Get information about a specific connection"""
        if connection_id not in self.active_connections:
            return None

        connection_state = self.active_connections[connection_id]
        return {
            "connection_id": connection_id,
            "user_id": connection_state.user_id,
            "test_id": connection_state.test_id,
            "assessment_id": connection_state.assessment_id,
            "thread_id": connection_state.thread_id,
            "connected_at": connection_state.connected_at.isoformat(),
            "last_activity": connection_state.last_activity.isoformat(),
            "is_authenticated": connection_state.is_authenticated,
            "is_in_assessment": connection_state.is_in_assessment,
            "graph_initialized": connection_state.graph_initialized,
            "assessment_started_at": connection_state.assessment_started_at.isoformat() if connection_state.assessment_started_at else None
        }

    def get_active_connections_count(self) -> int:
        """Get total number of active connections"""
        return len(self.active_connections)

    def get_user_connections_count(self, user_id: int) -> int:
        """
        Get number of active connections for a specific user

        Since we enforce single connection per user, this will return either 0 or 1.
        """
        return 1 if user_id in self.user_connections else 0

    def get_assessment_participants_count(self, test_id: int) -> int:
        """Get number of active participants in an assessment"""
        return len(self.assessment_sessions.get(test_id, set()))

    def has_active_connection(self, user_id: int) -> bool:
        """
        Check if a user has an active connection

        Args:
            user_id: ID of the user to check

        Returns:
            True if user has an active connection, False otherwise
        """
        return user_id in self.user_connections

    def get_user_connection_id(self, user_id: int) -> Optional[str]:
        """
        Get the connection ID for a user's active connection

        Args:
            user_id: ID of the user

        Returns:
            connection_id if user has active connection, None otherwise
        """
        return self.user_connections.get(user_id)

    def get_connection_thread_id(self, connection_id: str) -> Optional[str]:
        """
        Get the thread ID for a connection's assessment graph

        Args:
            connection_id: The connection identifier

        Returns:
            thread_id if connection exists and has assessment, None otherwise
        """
        if connection_id not in self.active_connections:
            logger.info("Connection not found for thread ID retrieval")
            return None

        connection_state = self.active_connections[connection_id]
        return connection_state.thread_id

    def mark_graph_initialized(self, connection_id: str):
        """
        Mark that the MCQ generation graph has been initialized for this connection

        Args:
            connection_id: The connection identifier
        """
        if connection_id in self.active_connections:
            self.active_connections[connection_id].graph_initialized = True

    async def validate_assessment_access(self, connection_id: str, test_id: int, db: AsyncSession) -> bool:
        """
        Validate if a user can access a specific assessment
        TODO: Implement proper authorization logic based on your business rules
        """
        print("Validating assessment access...")
        if connection_id not in self.active_connections:
            return False

        connection_state = self.active_connections[connection_id]
        user_id = connection_state.user_id

        try:
            # Get test repository
            test_repo = TestRepository(db)

            # Check if test exists and is in valid state
            test = await test_repo.get_test_by_id(test_id)
            if not test:
                print(f"Test {test_id} not found")
                return False

            # Check test status
            if test.status not in [TestStatus.LIVE, TestStatus.SCHEDULED]:
                print(
                    f"Test {test_id} is not available for assessment (status: {test.status})")
                return False

            # TODO: Add test scheduler validation
            # Check if the test is within valid time window
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)

            # Check if test has started (if scheduled)
            scheduled_at = getattr(test, 'scheduled_at', None)
            if scheduled_at is not None and scheduled_at > now:
                print(f"Test {test_id} has not started yet")
                return False

            # Check if assessment deadline has passed
            assessment_deadline = getattr(test, 'assessment_deadline', None)
            if assessment_deadline is not None and assessment_deadline < now:
                logger.warning(
                    f"Test {test_id} assessment deadline has passed")
                return False

            # TODO: Add additional checks:
            # - Check if user has applied for this test
            # - Check if user is shortlisted
            # - Check if user has already completed the assessment
            # - Check maximum attempts allowed
            # - Check if user is blocked/suspended

            return True

        except Exception as e:
            logger.error(f"Error validating assessment access: {str(e)}")
            return False

    async def start_assessment_session(self, connection_id: str, test_id: int, db: AsyncSession) -> tuple[Optional[int], Optional[str]]:

        if connection_id not in self.active_connections:
            logger.error(f"Connection {connection_id} not found")
            return None, None

        connection_state = self.active_connections[connection_id]
        user_id = connection_state.user_id

        try:
            # Check for existing recoverable assessment first
            existing_assessment_id = await self.check_existing_assessment(user_id, test_id, db)

            if existing_assessment_id:
                # Recover existing assessment with same connection_id
                recovery_success = await self.recover_assessment_session(
                    connection_id, existing_assessment_id, db
                )
                if recovery_success:
                    logger.info(
                        f"Recovered existing assessment {existing_assessment_id} for connection {connection_id}")
                    return existing_assessment_id, connection_id

            # Create new assessment instance if no existing one found
            # Fetch application_id for this user and test
            application = await CandidateApplicationRepository.get_by_user_and_test(db, user_id, test_id)

            if not application:
                logger.warning(
                    f"No application found for user {user_id}, test {test_id}")
                # In some cases, we might want to create an application on the fly
                # For now, we'll use None and let the assessment creation handle it
                application_id = None
            else:
                application_id = application.application_id

            # Create assessment instance in database
            assessment_repo = AssessmentRepository(db)
            assessment_id = await assessment_repo.create_assessment_instance(
                application_id=application_id,  # type:ignore
                user_id=user_id,
                test_id=test_id
            )

            if not assessment_id:
                logger.error(
                    f"Failed to create assessment instance for user {user_id}, test {test_id}")
                return None, None

            # Update connection state with assessment instance
            connection_state.start_assessment(test_id, assessment_id)

            logger.info(
                f"Assessment instance {assessment_id} started for connection {connection_id} (user: {user_id}, test: {test_id})")
            return assessment_id, connection_id

        except Exception as e:
            logger.error(f"Error starting assessment session: {str(e)}")
            return None, None

    async def end_assessment_session(self, connection_id: str):
        """End an assessment session for a connection"""
        if connection_id not in self.active_connections:
            return

        connection_state = self.active_connections[connection_id]
        test_id = connection_state.test_id
        connection_state.end_assessment()

        # Remove from assessment session
        if test_id and test_id in self.assessment_sessions:
            self.assessment_sessions[test_id].discard(connection_id)
            if not self.assessment_sessions[test_id]:
                del self.assessment_sessions[test_id]

        logger.info(f"Assessment session ended: {connection_id}")

    async def check_existing_assessment(self, user_id: int, test_id: int, db: AsyncSession) -> Optional[int]:
        """
        Check if user has an existing in-progress assessment for this test

        This method enables seamless reconnection by checking if the user has an
        assessment that can be recovered. This is crucial for handling network
        disconnections, browser refreshes, or device switches during an assessment.

        Args:
            user_id: ID of the user to check
            test_id: ID of the test to check  
            db: Database session

        Returns:
            assessment_id if found and recoverable, None otherwise

        Recoverable States:
            - 'started': Assessment has begun but no questions answered yet
            - 'in_progress': Assessment is actively being taken

        Non-Recoverable States:
            - 'completed': Assessment finished successfully
            - 'abandoned': Assessment was abandoned by user
            - 'timed_out': Assessment exceeded time limit
        """
        try:
            assessment_repo = AssessmentRepository(db)
            existing_assessment = await assessment_repo.get_user_assessment_for_test(user_id, test_id)

            if existing_assessment:
                # Check if assessment is in a recoverable state
                status = getattr(existing_assessment, 'status', None)
                assessment_id = getattr(existing_assessment, 'assessment_id')
                if status in ['completed', 'abandoned', 'timed_out']:
                    logger.info(
                        f"Assessment {assessment_id} for user {user_id}, test {test_id} is not recoverable (status: {status})")
                    return None

                if status in ['started', 'in_progress']:
                    logger.info(
                        f"Found existing recoverable assessment {assessment_id} for user {user_id}, test {test_id}")
                    return assessment_id
                elif status in ['completed', 'abandoned', 'timed_out']:
                    logger.info(
                        f"Assessment {assessment_id} already finalized with status: {status}")
                    return None

            return None

        except Exception as e:
            logger.error(f"Error checking existing assessment: {str(e)}")
            return None

    async def recover_assessment_session(self, connection_id: str, assessment_id: int, db: AsyncSession) -> bool:
        """
        Recover an existing assessment session for a reconnected user
        """
        try:
            if connection_id not in self.active_connections:
                logger.error(
                    f"Connection {connection_id} not found for recovery")
                return False

            connection_state = self.active_connections[connection_id]

            # Get assessment details
            assessment_repo = AssessmentRepository(db)
            assessment = await assessment_repo.get_assessment_by_id(assessment_id)

            if not assessment:
                logger.error(
                    f"Assessment {assessment_id} not found for recovery")
                return False

            test_id = getattr(assessment, 'test_id')

            # Update connection state
            # Add to assessment session tracking
            connection_state.start_assessment(test_id, assessment_id)
            if test_id not in self.assessment_sessions:
                self.assessment_sessions[test_id] = set()
            self.assessment_sessions[test_id].add(connection_id)

            logger.info(
                f"Recovered assessment session {assessment_id} for connection {connection_id}")
            return True

        except Exception as e:
            logger.error(f"Error recovering assessment session: {str(e)}")
            return False

    async def _cleanup_inactive_connections(self):
        """
        Background task to clean up inactive connections

        This critical maintenance task runs every 5 minutes to identify and remove
        connections that have become inactive. This prevents memory leaks and
        resource exhaustion in long-running server instances.

        Cleanup Process:
        1. Identify connections idle for more than max_idle_time (30 minutes)
        2. Gracefully disconnect them using the standard disconnect method
        3. Log cleanup operations for monitoring

        Network Resilience:
        This task ensures the server remains responsive even if clients disconnect
        ungracefully (network issues, browser crashes, device power loss).

        Note: Assessment state is preserved in the database, so users can reconnect
        and recover their progress even after cleanup.
        """
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)

                current_time = datetime.utcnow()
                inactive_connections = []

                # Identify inactive connections
                for connection_id, connection_state in self.active_connections.items():
                    time_since_activity = (
                        current_time - connection_state.last_activity).total_seconds()

                    if time_since_activity > self.max_idle_time:
                        inactive_connections.append(connection_id)

                # Clean up inactive connections using standard disconnect method
                for connection_id in inactive_connections:
                    logger.info(
                        f"Cleaning up inactive connection: {connection_id}")
                    await self.disconnect(connection_id)

                if inactive_connections:
                    logger.info(
                        f"Cleaned up {len(inactive_connections)} inactive connections")

            except Exception as e:
                logger.error(f"Error in connection cleanup task: {str(e)}")

    def has_active_assessment(self, connection_id: str) -> bool:
        """
        Check if a connection has an active assessment session

        Args:
            connection_id: The connection identifier

        Returns:
            True if connection has active assessment, False otherwise
        """
        if connection_id not in self.active_connections:
            return False

        connection_state = self.active_connections[connection_id]
        return connection_state.is_in_assessment and connection_state.assessment_id is not None

    def get_assessment_status(self, connection_id: str) -> Optional[Dict]:
        """
        Get the assessment status for a connection

        Args:
            connection_id: The connection identifier

        Returns:
            Dictionary with assessment status information or None
        """
        if connection_id not in self.active_connections:
            return None

        connection_state = self.active_connections[connection_id]

        if not connection_state.assessment_id:
            return None

        return {
            "assessment_id": connection_state.assessment_id,
            "test_id": connection_state.test_id,
            "thread_id": connection_state.thread_id,
            "is_in_assessment": connection_state.is_in_assessment,
            "graph_initialized": connection_state.graph_initialized,
            "assessment_started_at": connection_state.assessment_started_at.isoformat() if connection_state.assessment_started_at else None
        }


connection_manager = WebSocketConnectionManager()
