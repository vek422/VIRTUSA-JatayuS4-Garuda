"""
WebSocket Assessment Service - Updated for proper graph state management
Integrates MCQ generation graph with WebSocket communication for real-time assessments
"""

import asyncio
import json
import logging
from langgraph.types import Command
from datetime import datetime
from typing import Dict, Optional, Any, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.jd_parsing.state import JobDescriptionFields
from app.services.resume_parsing.state import ResumeFields
from app.services.mcq_generation.state import AgentState, Question, Response
from app.services.skill_graph_generation.state import SkillGraph
from app.models.test import Test
from app.models.assessment import AssessmentStatus
from app.repositories.test_repo import TestRepository
from app.repositories.candidate_application_repo import CandidateApplicationRepository
from app.repositories.assessment_repo import AssessmentRepository
from app.services.mcq_generation.graph import get_question_generation_graph

logger = logging.getLogger(__name__)


class StateEncoder(json.JSONEncoder):
    def default(self, o):
        if hasattr(o, 'model_dump'):
            return o.model_dump()
        elif hasattr(o, 'dict'):
            return o.dict()
        elif isinstance(o, datetime):
            return o.isoformat()
        return str(o)


class AssessmentGraphService:
    """
    Service for managing MCQ generation graph in WebSocket assessments
    Handles graph state, question generation, and answer processing with proper thread ID management

    Key Principles:
    - Each assessment gets a unique thread_id (same as assessment_id)
    - Graph state is persistent and recoverable using thread_id
    - Never reinitialize graph with existing thread_id to preserve state
    - Use Command(resume=...) for all graph interactions after initialization
    """

    def __init__(self):
        self.graph = None
        # Track which connections have initialized graphs to prevent re-initialization
        self.initialized_threads: Dict[str, bool] = {}

    async def _get_graph(self):
        """Get or create the MCQ generation graph"""
        if not self.graph:
            self.graph = await get_question_generation_graph()
        return self.graph

    async def initialize_assessment_graph(
        self,
        connection_id: str,
        test: Test,
        assessment_id: int,
        user_id: int,
        db: AsyncSession
    ):
        """
        Initialize MCQ generation graph for an assessment session

        CRITICAL: This method should only be called once per assessment_id (thread_id).
        If called again with the same thread_id, it will check for existing state
        and recover instead of reinitializing.

        Args:
            connection_id: WebSocket connection identifier
            test: Test model instance
            assessment_id: Assessment instance ID (used as thread_id)
            user_id: User taking the assessment
            db: Database session

        Returns:
            bool: True if initialization/recovery successful, False otherwise
        """
        try:
            thread_id = str(assessment_id)
            if not test:
                logger.error(f"Test not found for ID {test.test_id}")
                return None

            # Check if we've already initialized this thread
            if thread_id in self.initialized_threads:
                logger.info(
                    f"Thread {thread_id} already initialized, checking for existing state")
                recoverd_state = await self._check_and_recover_existing_state(thread_id, connection_id)
                return recoverd_state

            graph = await self._get_graph()

            # Check if graph already has state for this thread_id
            config = {
                "configurable": {"thread_id": thread_id}
            }

            existing_state = await graph.aget_state(config)  # type:ignore
            if existing_state.values:
                logger.info(
                    f"Found existing graph state for thread {thread_id}, recovering")
                self.initialized_threads[thread_id] = True
                return existing_state.values  # type:ignore

            # No existing state, initialize new assessment
            logger.info(
                f"Initializing new assessment graph for thread {thread_id}")

            # Fetch candidate application
            candidate_application = await CandidateApplicationRepository.get_by_user_and_test(
                db, user_id, test.test_id  # type: ignore
            )

            if not candidate_application:
                logger.error(
                    f"Candidate application not found for user {user_id}")
                return None

            # Prepare initial state data
            parsed_jd = JobDescriptionFields.model_validate_json(
                test.parsed_job_description)  # type: ignore
            parsed_resume = ResumeFields.model_validate_json(
                candidate_application.parsed_resume)  # type: ignore
            skill_graph = SkillGraph.model_validate_json(
                test.skill_graph)  # type: ignore
            questions_per_difficulty = {
                "H": test.high_priority_questions,
                "M": test.medium_priority_questions,
                "L": test.low_priority_questions
            }
            # Create initial agent state
            agent_state = AgentState(
                parsed_jd=parsed_jd,
                parsed_resume=parsed_resume,
                skill_graph=skill_graph,
                questions_per_difficulty=questions_per_difficulty,
            )

            # Initialize the graph with agent state
            state = await graph.ainvoke(agent_state, config=config)

            # Mark as initialized
            self.initialized_threads[thread_id] = True

            logger.info(
                f"Successfully initialized assessment graph for thread {thread_id}")
            return state  # type: ignore

        except Exception as e:
            logger.error(
                f"Error initializing assessment graph: {str(e)}", exc_info=True)
            return None

    async def _check_and_recover_existing_state(self, thread_id: str, connection_id: str) -> AgentState | None:
        """
        Check if existing state is valid and recoverable

        Args:
            thread_id: Thread ID to check
            connection_id: Connection requesting recovery

        Returns:
            bool: True if state is recoverable, False otherwise
        """
        try:
            graph = await self._get_graph()
            config = {
                "configurable": {"thread_id": thread_id}
            }

            state = await graph.aget_state(config)
            if state.values:
                logger.info(f"Recovered existing state for thread {thread_id}")
                return state.values  # type:ignore
            else:
                logger.warning(
                    f"No recoverable state found for thread {thread_id}")
                return None

        except Exception as e:
            logger.error(
                f"Error recovering state for thread {thread_id}: {str(e)}")
            return None

    async def generate_question(self, connection_id: str) -> Optional[Dict[str, Any]]:
        try:
            # Get thread_id from connection manager
            from app.websocket.connection_manager import connection_manager
            thread_id = connection_manager.get_connection_thread_id(
                connection_id)

            if not thread_id:
                logger.error(
                    f"No thread_id found for connection {connection_id}")
                return None

            graph = await self._get_graph()
            config = {
                "configurable": {"thread_id": thread_id}
            }

            # Check current state
            current_state = await graph.aget_state(config)
            if not current_state.values:
                logger.error(f"No state found for thread {thread_id}")
                return None

            # Use Command to request question generation
            command = Command(resume={"type": "generate_question"})

            # Invoke graph with command
            result = await graph.ainvoke(command, config=config)

            # Get updated state to check for generated questions
            updated_state = await graph.aget_state(config)
            generated_questions = updated_state.values.get(
                "generated_questions", {})

            if not generated_questions:
                logger.warning(
                    f"No questions generated for thread {thread_id}")
                return None

            # Get the latest question
            question_queue = updated_state.values.get(
                "question_queue", [])

            if not question_queue:
                logger.warning(
                    f"No questions in queue for thread {thread_id}")
                return None

            latest_question_id = question_queue[0]
            latest_question = generated_questions[latest_question_id]

            return {
                "question_id": latest_question_id,
                "question": latest_question.model_dump() if hasattr(latest_question, 'model_dump') else latest_question,
                "thread_id": thread_id
            }

        except Exception as e:
            logger.error(
                f"Error generating question for connection {connection_id}: {str(e)}", exc_info=True)
            return None

    async def process_answer(
        self,
        connection_id: str,
        question_id: str,
        selected_option: str
    ) -> Optional[Dict[str, Any]]:
        """
        Process candidate's answer using MCQ graph

        Args:
            connection_id: WebSocket connection identifier
            question_id: ID of the question being answered
            selected_option: Candidate's selected option

        Returns:
            Dict containing feedback and progress data or None if processing failed
        """
        try:
            # Get thread_id from connection manager
            from app.websocket.connection_manager import connection_manager
            thread_id = connection_manager.get_connection_thread_id(
                connection_id)

            if not thread_id:
                logger.error(
                    f"No thread_id found for connection {connection_id}")
                return None

            graph = await self._get_graph()
            config = {
                "configurable": {"thread_id": thread_id}
            }

            # Verify question exists
            current_state = await graph.aget_state(config)
            generated_questions = current_state.values.get(
                "generated_questions", {})

            if question_id not in generated_questions:
                logger.error(
                    f"Question {question_id} not found in thread {thread_id}")
                return None

            # Submit answer using Command
            command = Command(resume={
                "type": "submit_response",
                "payload": {
                    "question_id": question_id,
                    "selected_option": selected_option
                }
            })

            result = await graph.ainvoke(command, config=config)

            updated_state = await graph.aget_state(config)

            processed_nodes = updated_state.values.get("processed_nodes", [])
            candidate_graph = updated_state.values.get("candidate_graph", [])
            total_nodes = len(candidate_graph)

            completed_nodes = len(processed_nodes)
            progress = (completed_nodes / (total_nodes or 1)) * 100

            return {
                "question_id": question_id,
                "feedback": self._generate_feedback(question_id, selected_option, generated_questions),
                "progress": {
                    "completed_nodes": completed_nodes,
                    "total_nodes": total_nodes,
                    "percentage_complete": progress
                },
                "thread_id": thread_id
            }

        except Exception as e:
            logger.error(
                f"Error processing answer for connection {connection_id}: {str(e)}", exc_info=True)
            return None

    def _generate_feedback(self, question_id: str, selected_option: str, questions: Dict) -> Dict[str, Any]:
        """
        Generate feedback for the submitted answer

        Args:
            question_id: ID of the answered question
            selected_option: Selected option
            questions: Dictionary of all questions

        Returns:
            Dict containing feedback information
        """
        question = questions.get(question_id)
        if not question:
            return {"message": "Question not found"}

        # Extract correct answer (this depends on your Question model structure)
        correct_answer = getattr(question, 'correct_answer', None)
        is_correct = selected_option == correct_answer

        return {
            "correct": is_correct,
            "selected_option": selected_option,
            "correct_answer": correct_answer,
            "message": "Correct answer!" if is_correct else f"Incorrect. The correct answer is {correct_answer}"
        }

    async def get_assessment_progress(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current assessment progress

        Args:
            connection_id: WebSocket connection identifier

        Returns:
            Dict containing progress information or None if error
        """
        try:
            # Get thread_id from connection manager
            from app.websocket.connection_manager import connection_manager
            thread_id = connection_manager.get_connection_thread_id(
                connection_id)

            if not thread_id:
                logger.error(
                    f"No thread_id found for connection {connection_id}")
                return None

            graph = await self._get_graph()
            config = {
                "configurable": {"thread_id": thread_id}
            }

            updated_state = await graph.aget_state(config)

            processed_nodes = updated_state.values.get("processed_nodes", [])
            candidate_graph = updated_state.values.get("candidate_graph", [])
            total_nodes = len(candidate_graph)

            completed_nodes = len(processed_nodes)
            progress = (completed_nodes / (total_nodes or 1)) * 100

            return {
                "total_nodes": total_nodes,
                "processed_nodes": processed_nodes,
                "percentage_complete": progress,
                "thread_id": thread_id
            }

        except Exception as e:
            logger.error(
                f"Error getting progress for connection {connection_id}: {str(e)}")
            return None

    async def get_assessment_state(self, thread_id: str, db: AsyncSession) -> Optional[Dict[str, Any]]:
        """
        Get current assessment state including questions and responses

        Args:
            connection_id: WebSocket connection identifier
            db: Database session

        Returns:
            Dict containing current state or None if error
        """
        try:

            graph = await self._get_graph()
            config = {
                "configurable": {"thread_id": thread_id}
            }

            state = await graph.aget_state(config)
            serialized_state = json.loads(
                json.dumps(state.values, cls=StateEncoder))
            if not state.values:
                logger.error(f"No state found for thread {thread_id}")
                return None
            return {
                "state": serialized_state
            }
        except Exception as e:
            logger.error(
                f"Error getting assessment state for thread {thread_id}: {str(e)}")
            return None

    async def finalize_assessment(self, connection_id: str, db: AsyncSession) -> Optional[Dict[str, Any]]:
        """
        Finalize assessment and save results to database

        Args:
            connection_id: WebSocket connection identifier
            db: Database session

        Returns:
            Dict containing final results or None if error
        """
        try:
            # Get thread_id from connection manager
            from app.websocket.connection_manager import connection_manager
            thread_id = connection_manager.get_connection_thread_id(
                connection_id)

            if not thread_id:
                logger.error(
                    f"No thread_id found for connection {connection_id}")
                return None

            # Extract state from graph
            graph = await self._get_graph()
            config = {
                "configurable": {"thread_id": thread_id}
            }
            state = await graph.ainvoke(Command(resume={"type": "exit"}), config=config)

            state = await graph.aget_state(config)
            if not state.values:
                logger.error(f"No state found for thread {thread_id}")
                return None
            state_values = json.loads(
                json.dumps(state.values, cls=StateEncoder))

            if not state_values:
                logger.error(f"No state found for thread {thread_id}")
                return None

            # Extract candidate_graph (nodes with scores and priorities)
            candidate_graph = state_values.get("candidate_graph", [])
            if not candidate_graph:
                logger.error(
                    f"No candidate_graph found in state for thread {thread_id}")
                return None

            # Calculate weighted score using the specified formula
            # Weights for High, Medium, Low priority
            skill_weights = {"H": 3, "M": 2, "L": 1}

            skill_scores = {}

            # Group nodes by priority and calculate scores
            for node in candidate_graph:
                priority = node.get("priority")
                score = node.get("score")

                if priority and score is not None:
                    if priority not in skill_scores:
                        skill_scores[priority] = []
                    skill_scores[priority].append(score)

            # Calculate average score per skill level
            level_scores = {}
            for priority, scores in skill_scores.items():
                if scores:
                    level_scores[priority] = (sum(scores) / len(scores)) * 100

            # Calculate final weighted score
            if level_scores:
                numerator = sum(level_scores[priority] * skill_weights[priority]
                                for priority in level_scores)
                denominator = sum(skill_weights[priority]
                                  for priority in level_scores)
                final_percentage_score = numerator / denominator
            else:
                final_percentage_score = 0.0
              # Update assessment in database
            assessment_repo = AssessmentRepository(db)
            assessment_id = int(thread_id)

            current_time = datetime.utcnow()
            #
            candidate_graph = state_values.get("candidate_graph", [])
            generated_questions = state_values.get("generated_questions", {})
            candidate_response = state_values.get("candidate_response", {})
            result = {
                "candidate_graph": candidate_graph,
                "generated_questions": generated_questions,
                "candidate_response": candidate_response
            }

            success = await assessment_repo.update_assessment_status(
                assessment_id=assessment_id,
                status="completed",
                percentage_score=final_percentage_score,
                end_time=current_time,
                result=result
            )

            if not success:
                logger.error(f"Failed to update assessment {assessment_id}")
                return None

            # Clean up thread tracking
            if thread_id in self.initialized_threads:
                del self.initialized_threads[thread_id]

            # Prepare detailed results
            skill_breakdown = {}
            total_questions = 0
            total_correct = 0

            for node in candidate_graph:
                priority = node.get("priority")
                score = node.get("score", 0)
                node_id = node.get("node_id")
                asked_questions = node.get("asked_questions", [])

                if priority not in skill_breakdown:
                    skill_breakdown[priority] = {
                        "nodes": [],
                        "total_questions": 0,
                        "average_score": 0
                    }

                node_questions = len(asked_questions)
                node_correct = int(
                    score * node_questions) if score and node_questions > 0 else 0

                skill_breakdown[priority]["nodes"].append({
                    "skill": node_id,
                    "score": score * 100 if score else 0,
                    "questions_asked": node_questions,
                    "correct_answers": node_correct
                })

                skill_breakdown[priority]["total_questions"] += node_questions
                total_questions += node_questions
                total_correct += node_correct

            # Calculate average scores per priority level
            for priority in skill_breakdown:
                nodes = skill_breakdown[priority]["nodes"]
                if nodes:
                    skill_breakdown[priority]["average_score"] = sum(
                        node["score"] for node in nodes
                    ) / len(nodes)

            logger.info(
                f"Finalized assessment for thread {thread_id} with score {final_percentage_score:.2f}%")

            return {
                "assessment_id": assessment_id,
                "thread_id": thread_id,
                "final_percentage_score": round(final_percentage_score, 2),
                "total_questions": total_questions,
                "total_correct": total_correct,
                "skill_breakdown": skill_breakdown,
                "level_scores": {k: round(v, 2) for k, v in level_scores.items()},
                "completion_time": current_time.isoformat(),
                "status": "completed"
            }

        except Exception as e:
            logger.error(
                f"Error finalizing assessment for connection {connection_id}: {str(e)}", exc_info=True)
            return None

    def cleanup_connection(self, connection_id: str):
        logger.info(
            f"Cleaning up assessment resources for connection {connection_id}")
        # Note: Graph state persists via thread_id in langgraph's persistence layer


# Global assessment service instance
assessment_graph_service = AssessmentGraphService()
