import json
import logging
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
from fastapi import WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.websocket.connection_manager import connection_manager, ConnectionState
from app.db.database import get_db
from app.services.websocket_assessment_service import assessment_graph_service
from app.repositories.test_repo import TestRepository
from app.repositories.assessment_repo import AssessmentRepository
import logging
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
from fastapi import WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.websocket.connection_manager import connection_manager, ConnectionState
from app.db.database import get_db
from app.services.websocket_assessment_service import assessment_graph_service
from app.repositories.test_repo import TestRepository
from app.repositories.assessment_repo import AssessmentRepository
logger = logging.getLogger(__name__)


class WebSocketMessageType:

    CONNECT = "connect"
    DISCONNECT = "disconnect"

    # Authentication
    AUTH = "auth"
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILED = "auth_failed"

    START_ASSESSMENT = "start_assessment"
    ASSESSMENT_STARTED = "assessment_started"
    ASSESSMENT_ERROR = "assessment_error"
    ASSESSMENT_COMPLETED = "assessment_completed"
    ASSESSMENT_FINALIZED = "complete_assessment"

    GET_QUESTION = "get_question"
    QUESTION = "question"
    SUBMIT_ANSWER = "submit_answer"
    ANSWER_FEEDBACK = "answer_feedback"

    PROGRESS_UPDATE = "progress_update"
    TIME_WARNING = "time_warning"
    TIME_REMAINING = "time_remaining"

    ERROR = "error"
    HEARTBEAT = "heartbeat"
    PONG = "pong"
    CHAT_MESSAGE = "chat_message"
    SYSTEM_MESSAGE = "system_message"

    GET_TEST_INFO = "get_test_info"
    TEST_INFO = "test_info"


class AssessmentWebSocketHandler:
    def __init__(self):
        # Store active timer tasks for each connection
        self.assessment_timers: Dict[str, asyncio.Task] = {}

    async def handle_connection(
        self,
        websocket: WebSocket,
        token: Optional[str] = None,
        test_id: Optional[int] = None,
        db: AsyncSession = Depends(get_db)
    ):
        connection_id = None
        try:
            # Step 1: Authenticate the connection
            if not token:
                await websocket.close(code=4001, reason="Token required")
                return

            user_id = await connection_manager.authenticate_connection(websocket, token)

            if not user_id:
                await websocket.close(code=4001, reason="Authentication failed")
                logger.info(f"Authentication failed")
                return

            # Step 3: Send authentication success confirmation
            connection_id = await connection_manager.connect(websocket, user_id, test_id, db)
            connection_info = connection_manager.get_connection_info(
                connection_id)
            auth_data = {
                "user_id": user_id,
                "connection_id": connection_id,
                "timestamp": datetime.utcnow().isoformat()
            }

            assessment_repo = AssessmentRepository(db)
            is_completed = await assessment_repo.is_assessment_completed(user_id, test_id)
            if is_completed:
                await self._send_error(connection_id, "You have already completed this assessment.")
                await websocket.close(code=4002, reason="Assessment already completed")
            # Include recovery information if assessment was auto-recovered
            progress = await assessment_graph_service.get_assessment_progress(connection_id)

            if connection_info and connection_info.get("assessment_id"):
                auth_data["recovered_assessment"] = {
                    "assessment_id": connection_info["assessment_id"],
                    "test_id": connection_info["test_id"],
                    "thread_id": connection_info["thread_id"],
                    "is_in_assessment": connection_info["is_in_assessment"],
                    "progress": progress if progress else {}
                }

            await self._send_message(connection_id, {
                "type": WebSocketMessageType.AUTH_SUCCESS,
                "data": auth_data
            })

            # Step 4: If test_id provided, validate assessment access
            if test_id:
                access_granted = await connection_manager.validate_assessment_access(
                    connection_id, test_id, db
                )
                if not access_granted:
                    await self._send_error(connection_id, "Access denied for this assessment")
                    await websocket.close(code=4003, reason="Assessment access denied")
                    return            # Step 5: Start message handling loop
            await self._handle_messages(connection_id, websocket, db)

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: {connection_id}")
        except Exception as e:
            logger.error(f"Error in WebSocket handler: {str(e)}")
            if connection_id:
                await self._send_error(connection_id, f"Internal server error: {str(e)}")
        finally:
            # Cleanup: Always clean up resources on exit
            if connection_id:
                # Cancel any running assessment timer
                await self._cancel_assessment_timer(connection_id)
                await connection_manager.disconnect(connection_id)
                # Clean up assessment service state
                assessment_graph_service.cleanup_connection(connection_id)

    async def _handle_messages(self, connection_id: str, websocket: WebSocket, db: AsyncSession):
        while True:
            try:
                # Wait for message from client
                data = await websocket.receive_text()
                message = json.loads(data)

                message_type = message.get("type")
                message_data = message.get("data", {})

                if not message_type:
                    raise ValueError(
                        "Cannot Process the request without message_type")
                logger.info(
                    f"Received message: {message_type} from {connection_id}")

                # Route message to appropriate handler
                await self._route_message(connection_id, message_type, message_data, db)

            except WebSocketDisconnect:
                # Normal disconnection - exit loop
                break
            except json.JSONDecodeError:
                # Invalid JSON - notify client
                await self._send_error(connection_id, "Invalid JSON format")
            except Exception as e:
                # Unexpected error - log and notify client
                logger.error(f"Error handling message: {str(e)}")
                await self._send_error(connection_id, f"Error processing message: {str(e)}")

    async def _route_message(self, connection_id: str, message_type: str, data: Dict, db: AsyncSession):
        """
        Route messages to appropriate handlers based on message type

        This method implements the message dispatching logic, mapping message types
        to their corresponding handler methods. It provides a clean separation of
        concerns and makes it easy to add new message types.

        Supported Message Types:
        - START_ASSESSMENT: Initialize a new assessment session
        - GET_QUESTION: Request the next question in sequence
        - SUBMIT_ANSWER: Submit an answer for the current question
        - CHAT_MESSAGE: Send conversational message to AI
        - HEARTBEAT: Keep-alive ping message

        Args:
            connection_id: Identifier for the WebSocket connection
            message_type: String identifying the type of message
            data: Dictionary containing message payload
            db: Database session for data operations        Error Handling:
        If an unknown message type is received, an error is sent back to the client
        rather than raising an exception, allowing the connection to continue.
        """

        handlers = {
            WebSocketMessageType.START_ASSESSMENT: self._handle_start_assessment,
            WebSocketMessageType.GET_QUESTION: self._handle_get_question,
            WebSocketMessageType.SUBMIT_ANSWER: self._handle_submit_answer,
            WebSocketMessageType.CHAT_MESSAGE: self._handle_chat_message,
            WebSocketMessageType.HEARTBEAT: self._handle_heartbeat,
            WebSocketMessageType.GET_TEST_INFO: self._handle_get_test_info,
            WebSocketMessageType.ASSESSMENT_FINALIZED: self._finalize_assessment,

        }

        handler = handlers.get(message_type)
        if handler:
            await handler(connection_id, data, db)
        else:
            await self._send_error(connection_id, f"Unknown message type: {message_type}")

    async def _handle_start_assessment(self, connection_id: str, data: Dict, db: AsyncSession):
        """
        Handle assessment start request
        Initialize MCQ generation graph and begin assessment flow

        This method now properly handles thread_id management to ensure
        graph state persistence and recovery.
        """
        try:
            test_id = data.get("test_id")
            if not test_id:
                await self._send_error(connection_id, "test_id is required")
                return

            # Validate assessment access again
            access_granted = await connection_manager.validate_assessment_access(connection_id, test_id, db)
            if not access_granted:
                await self._send_error(connection_id, "Access denied for this assessment")
                return

            test_repo = TestRepository(db)

            test = await test_repo.get_test_by_id(test_id)
            if not test:
                await self._send_error(connection_id, "Test not found")
                return

            # Start assessment session and create assessment instance
            assessment_id, returned_connection_id = await connection_manager.start_assessment_session(connection_id, test_id, db)
            logger.info(
                f"Assessment ID: {assessment_id}, Connection ID: {returned_connection_id}")

            if not assessment_id or not returned_connection_id:
                await self._send_error(connection_id, "Failed to create assessment instance")
                return

            # Connection ID should remain the same with new approach
            assert returned_connection_id == connection_id, "Connection ID should not change"

            # Initialize MCQ generation graph with proper thread_id management
            graph_initialized = await assessment_graph_service.initialize_assessment_graph(
                connection_id, test, assessment_id,
                connection_manager.active_connections[connection_id].user_id, db
            )

            if not graph_initialized:
                await self._send_error(connection_id, "Failed to initialize assessment")
                return

            # Mark graph as initialized in connection state
            connection_manager.mark_graph_initialized(connection_id)

            await self._send_message(connection_id, {
                "type": WebSocketMessageType.ASSESSMENT_STARTED,
                "data": {
                    "test_id": test_id,
                    "assessment_id": assessment_id,
                    "thread_id": str(assessment_id),
                    "test_name": test.test_name,
                }
            })            # Generate first question automatically
            await self._generate_next_question(connection_id, test_id, db)

            # Start the assessment timer based on test schedule
            await self._start_assessment_timer_from_schedule(connection_id, test, db)

        except Exception as e:
            logger.error(f"Error starting assessment: {str(e)}", exc_info=True)
            await self._send_error(connection_id, f"Failed to start assessment: {str(e)}")

    async def _handle_get_question(self, connection_id: str, data: Dict, db: AsyncSession):
        """
        Handle request for next question
        Uses MCQ generation service to create contextual questions with proper thread_id management
        """
        try:
            question_data = await assessment_graph_service.generate_question(connection_id)

            if question_data:
                await self._send_message(connection_id, {
                    "type": WebSocketMessageType.QUESTION,
                    "data": question_data
                })
            else:
                # No more questions available - send message but don't auto-finalize
                await self._send_message(connection_id, {
                    "type": WebSocketMessageType.SYSTEM_MESSAGE,
                    "data": {
                        "message": "No more questions available. You may continue or complete the assessment manually.",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                })

        except Exception as e:
            logger.error(f"Error generating question: {str(e)}", exc_info=True)
            await self._send_error(connection_id, f"Failed to generate question: {str(e)}")

    async def _handle_submit_answer(self, connection_id: str, data: Dict, db: AsyncSession):
        """
        Handle answer submission
        Process the answer using proper thread_id management to maintain state
        """
        try:
            question_id = data.get("question_id")
            selected_option = data.get("selected_option")

            if not question_id or not selected_option:
                await self._send_error(connection_id, "question_id and selected_option are required")
                return

            # Process answer using the assessment service with thread_id
            feedback_data = await assessment_graph_service.process_answer(
                connection_id, question_id, selected_option
            )

            if not feedback_data:
                await self._send_error(connection_id, "Failed to process answer")
                return

            # Send feedback
            await self._send_message(connection_id, {
                "type": WebSocketMessageType.ANSWER_FEEDBACK,
                "data": feedback_data
            })            # Send progress update
            progress_data = await assessment_graph_service.get_assessment_progress(connection_id)
            if progress_data:
                await self._send_progress_update(connection_id, progress_data)

            # Note: Auto-finalization removed - assessment must be completed manually
            # Users can continue answering more questions or complete manually

        except Exception as e:
            logger.error(f"Error processing answer: {str(e)}", exc_info=True)
            await self._send_error(connection_id, f"Failed to process answer: {str(e)}")

    async def _handle_chat_message(self, connection_id: str, data: Dict, db: AsyncSession):
        """
        Handle general chat messages during assessment
        Provides contextual responses and guidance
        """
        try:
            user_message = data.get("message", "").strip()

            if not user_message:
                await self._send_error(connection_id, "Message cannot be empty")
                return

            # TODO: Implement AI chat functionality
            # This could use the same LLM to provide contextual help
            # without revealing answers to current questions            # Placeholder response
            response_message = f"I understand you said: '{user_message}'. I'm here to guide you through the assessment. Would you like me to generate the next question?"

            await self._send_message(connection_id, {
                "type": WebSocketMessageType.SYSTEM_MESSAGE,
                "data": {
                    "message": response_message,
                    "timestamp": datetime.utcnow().isoformat()
                }
            })

        except Exception as e:
            logger.error(f"Error handling chat message: {str(e)}")
            await self._send_error(connection_id, f"Failed to process message: {str(e)}")

    async def _handle_heartbeat(self, connection_id: str, data: Dict, db: AsyncSession):
        """Handle heartbeat/ping messages to keep connection alive"""
        await self._send_message(connection_id, {
            "type": WebSocketMessageType.PONG,
            "data": {"timestamp": datetime.utcnow().isoformat()}
        })

    async def _generate_next_question(self, connection_id: str, test_id: Optional[int], db: AsyncSession):
        try:
            question_data = await assessment_graph_service.generate_question(connection_id)

            if question_data:
                await self._send_message(connection_id, {
                    "type": WebSocketMessageType.QUESTION,
                    "data": question_data
                })
            else:
                # No more questions available - send message but don't auto-finalize
                await self._send_message(connection_id, {
                    "type": WebSocketMessageType.SYSTEM_MESSAGE,
                    "data": {
                        "message": "No more questions available at this time. You may continue or complete the assessment manually.",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                })
                thread_id = connection_manager.get_connection_thread_id(
                    connection_id)
                if not thread_id:
                    return
                # check if assessment can be finalized
                state = await assessment_graph_service.get_assessment_state(
                    thread_id=thread_id, db=db)

        except Exception as e:
            logger.error(f"Error generating question: {str(e)}", exc_info=True)
            await self._send_error(connection_id, f"Failed to generate question: {str(e)}")

    async def _send_message(self, connection_id: str, message: Dict):
        """Send a message to a specific connection"""
        success = await connection_manager.send_personal_message(connection_id, message)
        if not success:
            logger.warning(f"Failed to send message to {connection_id}")

    async def _send_error(self, connection_id: str, error_message: str):
        """Send an error message to a connection"""
        await self._send_message(connection_id, {
            "type": WebSocketMessageType.ERROR,
            "data": {
                "error": error_message,                "timestamp": datetime.utcnow().isoformat()
            }
        })

    async def _send_progress_update(self, connection_id: str, progress_data: Dict):
        """Send progress update to connection"""
        await self._send_message(connection_id, {
            "type": WebSocketMessageType.PROGRESS_UPDATE,
            "data": {
                **progress_data,
                "timestamp": datetime.utcnow().isoformat()
            }
        })

    async def _finalize_assessment(self, connection_id: str, data: str, db: AsyncSession):
        """
        Finalize assessment and save results using proper thread_id management
        """
        try:
            # Cancel the assessment timer if it's running
            await self._cancel_assessment_timer(connection_id)

            # Get final results from assessment service
            final_results = await assessment_graph_service.finalize_assessment(connection_id, db)

            if final_results:
                # Send completion message with results
                await self._send_message(connection_id, {
                    "type": WebSocketMessageType.ASSESSMENT_COMPLETED,
                    "data": {
                        "message": "Assessment completed! Thank you for participating.",
                        "next_steps": "Your results will be reviewed and you'll be contacted if shortlisted."
                    }
                })

                # Clean up assessment session
                await connection_manager.end_assessment_session(connection_id)

                logger.info(f"Assessment finalized for {connection_id}")
            else:
                await self._send_error(connection_id, "Failed to finalize assessment")

        except Exception as e:
            logger.error(
                f"Error finalizing assessment: {str(e)}", exc_info=True)
            await self._send_error(connection_id, f"Failed to complete assessment: {str(e)}")

    async def _handle_get_test_info(self, connection_id: str, data: Dict, db: AsyncSession):
        """
        Handle request for test information using thread_id (for testing/debugging purposes)

        This method retrieves and returns comprehensive test information based on the 
        connection's thread_id. Useful for debugging assessment state and recovery.
        """
        try:
            # Get connection info
            connection_info = connection_manager.get_connection_info(
                connection_id)
            if not connection_info:
                await self._send_error(connection_id, "Connection not found")
                return

            # Check if connection has an active assessment
            if not connection_info.get("thread_id") or not connection_info.get("assessment_id"):
                await self._send_error(connection_id, "No active assessment found for this connection")
                return

            thread_id = connection_info["thread_id"]
            assessment_id = connection_info["assessment_id"]
            test_id = connection_info["test_id"]
            user_id = connection_info["user_id"]

            # Get test details from repository
            test_repo = TestRepository(db)
            test = await test_repo.get_test_by_id(test_id)

            if not test:
                await self._send_error(connection_id, f"Test {test_id} not found")
                return

            # Get assessment details
            from app.repositories.assessment_repo import AssessmentRepository
            assessment_repo = AssessmentRepository(db)
            assessment = await assessment_repo.get_assessment_by_id(assessment_id)

            # Prepare comprehensive test info
            test_info = {
                "connection_info": {
                    "connection_id": connection_id,
                    "user_id": user_id,
                    "thread_id": thread_id,
                    "assessment_id": assessment_id,
                    "is_authenticated": connection_info.get("is_authenticated"),
                    "is_in_assessment": connection_info.get("is_in_assessment"),
                    "graph_initialized": connection_info.get("graph_initialized"),
                    "connected_at": connection_info.get("connected_at"),
                    "last_activity": connection_info.get("last_activity"),
                    "assessment_started_at": connection_info.get("assessment_started_at")
                },
                "assessment_details": None
            }

            # Add assessment deta`ils if available
            if assessment:
                test_info["assessment_details"] = {
                    "assessment_id": assessment.assessment_id,
                    "status": getattr(assessment, 'status', None),
                    "started_at": assessment.started_at.isoformat() if hasattr(assessment, 'started_at') and assessment.started_at else None,
                    "completed_at": assessment.completed_at.isoformat() if hasattr(assessment, 'completed_at') and assessment.completed_at else None,
                    "score": getattr(assessment, 'score', None),
                    "total_questions_answered": getattr(assessment, 'total_questions_answered', 0)
                }            # Get graph state information using the assessment service
            try:
                graph_state_info = await assessment_graph_service.get_assessment_state(thread_id, db)
                if graph_state_info:
                    test_info["graph_state"] = graph_state_info

                else:
                    test_info["graph_state"] = {
                        "has_state": False,
                        "note": "No graph state found for this connection"
                    }
            except Exception as e:
                test_info["graph_state"] = {
                    "error": f"Failed to get graph state: {str(e)}"}

            # Send the comprehensive test info
            await self._send_message(connection_id, {
                "type": WebSocketMessageType.TEST_INFO,
                "data": {
                    "message": f"Test information retrieved for thread_id: {thread_id}",
                    "test_info": test_info,
                    "timestamp": datetime.utcnow().isoformat()
                }
            })

            logger.info(
                f"Test info retrieved for connection {connection_id}, thread_id: {thread_id}")

        except Exception as e:
            logger.error(
                f"Error handling get_test_info: {str(e)}", exc_info=True)
            await self._send_error(connection_id, f"Failed to retrieve test info: {str(e)}")

    async def _start_assessment_timer_from_schedule(self, connection_id: str, test, db: AsyncSession):
        """
        Start a timer for assessment auto-finalization based on test schedule

        Args:
            connection_id: WebSocket connection identifier
            test: Test object with scheduled_at and assessment_deadline
            db: Database session
        """
        try:
            scheduled_at = getattr(test, 'scheduled_at', None)
            assessment_deadline = getattr(test, 'assessment_deadline', None)

            if not scheduled_at or not assessment_deadline:
                logger.info(
                    f"No timer set for {connection_id}: missing schedule or deadline")
                return

            # Calculate total assessment duration
            total_duration = assessment_deadline - scheduled_at
            total_duration_seconds = int(total_duration.total_seconds())

            if total_duration_seconds <= 0:
                logger.warning(
                    f"Invalid assessment duration for {connection_id}: {total_duration_seconds} seconds")
                return

            # Calculate time remaining from now until deadline
            now = datetime.now(timezone.utc)
            time_until_deadline = assessment_deadline - now
            remaining_seconds = int(time_until_deadline.total_seconds())

            if remaining_seconds <= 0:
                logger.info(
                    f"Assessment deadline already passed for {connection_id}, auto-finalizing immediately")
                await self._finalize_assessment(connection_id, "", db)
                return

            logger.info(
                f"Starting assessment timer for {connection_id}: {remaining_seconds} seconds until deadline")

            # Create and store the timer task
            timer_task = asyncio.create_task(
                self._assessment_timer_task(
                    connection_id, remaining_seconds, db)
            )
            self.assessment_timers[connection_id] = timer_task

        except Exception as e:
            logger.error(
                f"Error starting schedule-based assessment timer: {str(e)}")

    async def _start_assessment_timer(self, connection_id: str, time_limit_minutes: int, db: AsyncSession):
        """
        Legacy method - kept for backward compatibility
        Start a timer for assessment auto-finalization

        Args:
            connection_id: WebSocket connection identifier
            time_limit_minutes: Test time limit in minutes
            db: Database session
        """
        try:
            if time_limit_minutes and time_limit_minutes > 0:
                # Convert minutes to seconds
                time_limit_seconds = time_limit_minutes * 60

                logger.info(
                    f"Starting assessment timer for {connection_id}: {time_limit_minutes} minutes")

                # Create and store the timer task
                timer_task = asyncio.create_task(
                    self._assessment_timer_task(
                        connection_id, time_limit_seconds, db)
                )
                self.assessment_timers[connection_id] = timer_task

        except Exception as e:
            logger.error(f"Error starting assessment timer: {str(e)}")

    async def _assessment_timer_task(self, connection_id: str, time_limit_seconds: int, db: AsyncSession):
        """
        Timer task that runs in the background and auto-finalizes assessment when time is up

        Args:
            connection_id: WebSocket connection identifier
            time_limit_seconds: Time limit in seconds
            db: Database session
        """
        try:
            # Wait for the specified time
            await asyncio.sleep(time_limit_seconds)

            # Check if connection is still active and assessment is still in progress
            connection_info = connection_manager.get_connection_info(
                connection_id)
            if not connection_info or not connection_info.get("is_in_assessment"):
                logger.info(
                    f"Assessment timer expired but connection {connection_id} no longer active")
                return

            logger.info(
                f"Assessment time limit reached for connection {connection_id}, auto-finalizing...")

            # Send time-up notification to client
            await self._send_message(connection_id, {
                "type": WebSocketMessageType.SYSTEM_MESSAGE,
                "data": {
                    "message": "⏰ Time's up! Your assessment is being automatically submitted.",
                    "is_time_up": True,
                    "timestamp": datetime.utcnow().isoformat()
                }
            })
            # Auto-finalize the assessment
            await self._finalize_assessment(connection_id, "", db)

        except asyncio.CancelledError:
            # Timer was cancelled (assessment finished before time limit)
            logger.info(
                f"Assessment timer cancelled for connection {connection_id}")
        except Exception as e:
            logger.error(f"Error in assessment timer task: {str(e)}")

    async def _cancel_assessment_timer(self, connection_id: str):
        """
        Cancel the assessment timer for a connection (called when assessment is completed manually)

        Args:
            connection_id: WebSocket connection identifier
        """
        if connection_id in self.assessment_timers:
            timer_task = self.assessment_timers[connection_id]
            if not timer_task.done():
                timer_task.cancel()
                logger.info(
                    f"Assessment timer cancelled for connection {connection_id}")
            del self.assessment_timers[connection_id]

    async def _check_assessment_time_remaining(self, connection_id: str, db: AsyncSession) -> Optional[int]:
        """
        Check how much time is remaining for the assessment based on test schedule

        Args:
            connection_id: WebSocket connection identifier
            db: Database session

        Returns:
            Remaining time in seconds until assessment deadline, or None if no deadline or assessment not found
        """
        try:
            connection_info = connection_manager.get_connection_info(
                connection_id)
            if not connection_info:
                return None

            test_id = connection_info.get("test_id")

            if not test_id:
                return None  # Get test details for schedule
            test_repo = TestRepository(db)
            test = await test_repo.get_test_by_id(test_id)

            assessment_deadline = getattr(
                test, 'assessment_deadline', None) if test else None
            if not test or not assessment_deadline:
                return None

            # Calculate remaining time until deadline
            now = datetime.now(timezone.utc)
            time_until_deadline = assessment_deadline - now
            remaining_seconds = max(
                0, int(time_until_deadline.total_seconds()))

            return remaining_seconds

        except Exception as e:
            logger.error(f"Error checking remaining time: {str(e)}")
            return None


websocket_handler = AssessmentWebSocketHandler()
