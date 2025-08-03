"""
Report Generation Service - Extracts assessment data and generates reports using LangGraph
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.report_generation.state import ReportState, PerformanceSummary
from app.services.report_generation.graph import graph as report_graph
from app.services.websocket_assessment_service import assessment_graph_service
from app.repositories.assessment_repo import AssessmentRepository

logger = logging.getLogger(__name__)


class ReportGenerationService:
    """Service for generating assessment reports using LangGraph"""

    def __init__(self):
        self.report_graph = report_graph

    async def generate_assessment_report(
        self,
        assessment_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Generate assessment report by extracting MCQ state and invoking report generation graph

        Args:
            assessment_id: Assessment ID (same as thread_id)
            db: Database session

        Returns:
            Dict containing generated report data

        Raises:
            ValueError: If assessment data is invalid
            Exception: If report generation fails
        """
        try:
            thread_id = str(assessment_id)

            # Get assessment data from repository
            repo = AssessmentRepository(db)
            assessment_data = await repo.get_assessment_with_relations(assessment_id)

            if not assessment_data:
                raise ValueError(f"Assessment {assessment_id} not found")

            # Get MCQ generation state
            mcq_state = await assessment_graph_service.get_assessment_state(thread_id, db)

            if not mcq_state or not mcq_state.get("state"):
                raise ValueError(
                    f"No MCQ state found for assessment {assessment_id}")

            # Extract and prepare report state
            report_state = await self._prepare_report_state(assessment_data, mcq_state["state"])

            # Generate report using LangGraph
            result = await self.report_graph.ainvoke(report_state)

            generated_report = result.get("generated_report")
            if not generated_report:
                raise Exception(
                    "Report generation failed - no report returned")

            # Store report in database
            success = await repo.update_assessment_report(assessment_id, generated_report)
            if not success:
                logger.warning(
                    f"Failed to store report in database for assessment {assessment_id}")

            return {
                "assessment_id": assessment_id,
                "report_generated": True,
                "generated_at": datetime.utcnow().isoformat(),
                "report": generated_report
            }

        except Exception as e:
            logger.error(
                f"Error generating report for assessment {assessment_id}: {str(e)}", exc_info=True)
            raise

    async def _prepare_report_state(
        self,
        assessment_data: Dict[str, Any],
        mcq_state: Dict[str, Any]
    ) -> ReportState:
        """
        Prepare ReportState from assessment data and MCQ state

        Args:
            assessment_data: Assessment with related data from repository
            mcq_state: MCQ generation graph state

        Returns:
            ReportState object ready for report generation
        """
        try:
            # Extract basic info
            candidate_name = self._extract_candidate_name(assessment_data)
            parsed_resume = assessment_data.get(
                "application", {}).get("parsed_resume", "")
            parsed_jd = assessment_data.get("test", {}).get(
                "parsed_job_description", "")

            # Extract performance summary from MCQ state
            performance_summary = self._extract_performance_summary(mcq_state)

            # Extract skill breakdown
            skill_breakdown = self._extract_skill_breakdown(mcq_state)

            # Extract additional analysis data
            skill_priorities = self._extract_skill_priorities(mcq_state)
            resume_skills = self._extract_resume_skills(mcq_state)
            question_difficulty_breakdown = self._extract_question_difficulty_breakdown(
                mcq_state)
            jd_skill_requirements = self._extract_jd_skill_requirements(
                mcq_state)
            resume_skill_validation = self._validate_resume_skills(mcq_state)

            # Create assessment metadata
            assessment_metadata = {
                "assessment_id": assessment_data.get("assessment", {}).get("assessment_id"),
                "test_id": assessment_data.get("test", {}).get("test_id"),
                "test_name": assessment_data.get("test", {}).get("test_name"),
                "total_questions_asked": mcq_state.get("total_questions_asked", 0),
                "overall_score": mcq_state.get("overall_score", 0.0),
                "start_time": mcq_state.get("start_time"),
                "finalized": mcq_state.get("finalized", False)
            }

            # Create ReportState
            report_state = ReportState(
                candidate_name=candidate_name,
                parsed_resume=parsed_resume,
                parsed_jd=parsed_jd,
                performance_summary=performance_summary,
                assessment_date=datetime.utcnow(),
                skill_breakdown=skill_breakdown,
                skill_priorities=skill_priorities,
                resume_skills_mentioned=resume_skills,
                question_difficulty_breakdown=question_difficulty_breakdown,
                jd_skill_requirements=jd_skill_requirements,
                resume_skill_validation=resume_skill_validation,
                assessment_metadata=assessment_metadata
            )

            return report_state

        except Exception as e:
            logger.error(
                f"Error preparing report state: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to prepare report state: {str(e)}")

    def _extract_candidate_name(self, assessment_data: Dict[str, Any]) -> str:
        """Extract candidate name from assessment data"""
        user_data = assessment_data.get("user", {})
        return user_data.get("username") or user_data.get("email") or "Unknown Candidate"

    def _extract_performance_summary(self, mcq_state: Dict[str, Any]) -> PerformanceSummary:
        """Extract performance summary from MCQ state"""
        candidate_graph = mcq_state.get("candidate_graph", [])

        # Calculate totals
        total_questions = mcq_state.get("total_questions_asked", 0)
        total_correct = 0
        passed_h = 0
        passed_m = 0
        passed_l = 0
        strengths = []
        weaknesses = []

        for node in candidate_graph:
            priority = node.get("priority", "L")
            score = node.get("score", 0)
            node_id = node.get("node_id", "")
            asked_questions = node.get("asked_questions", [])

            # Count correct answers
            node_correct = int(score * len(asked_questions)
                               ) if score and asked_questions else 0
            total_correct += node_correct

            # Count passed skills by priority
            if score and score >= 0.6:  # 60% pass threshold
                if priority == "H":
                    passed_h += 1
                elif priority == "M":
                    passed_m += 1
                elif priority == "L":
                    passed_l += 1

            # Identify strengths and weaknesses
            if score and score >= 0.8:  # 80% for strengths
                strengths.append(node_id)
            elif score and score <= 0.4:  # 40% for weaknesses
                weaknesses.append(node_id)

        # Calculate overall score
        total_score = (total_correct / total_questions *
                       100) if total_questions > 0 else 0

        return PerformanceSummary(
            total_score=total_score,
            total_questions=total_questions,
            correct_answers=total_correct,
            passed_skills_H=passed_h,
            passed_skills_M=passed_m,
            passed_skills_L=passed_l,
            strengths=strengths,
            weaknesses=weaknesses
        )

    def _extract_skill_breakdown(self, mcq_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract detailed skill breakdown from candidate graph"""
        candidate_graph = mcq_state.get("candidate_graph", [])
        skill_breakdown = []

        for node in candidate_graph:
            skill_info = {
                "skill_name": node.get("node_id", ""),
                "priority": node.get("priority", "L"),
                "score": node.get("score", 0),
                "questions_asked": len(node.get("asked_questions", [])),
                "status": node.get("status", "not_started"),
                "responses": node.get("responses", [])
            }
            skill_breakdown.append(skill_info)

        return skill_breakdown

    def _extract_skill_priorities(self, mcq_state: Dict[str, Any]) -> Dict[str, str]:
        """Extract skill priorities mapping from candidate graph"""
        candidate_graph = mcq_state.get("candidate_graph", [])
        skill_priorities = {}

        for node in candidate_graph:
            skill_id = node.get("node_id")
            priority = node.get("priority", "L")
            if skill_id:
                skill_priorities[skill_id] = priority

        return skill_priorities

    def _extract_resume_skills(self, mcq_state: Dict[str, Any]) -> List[str]:
        """Extract skills mentioned in resume from parsed resume data"""
        # This would need to be extracted from parsed_resume in the state
        # For now, return skills from candidate graph as placeholder
        candidate_graph = mcq_state.get("candidate_graph", [])
        return [node.get("node_id", "") for node in candidate_graph if node.get("node_id")]

    def _extract_question_difficulty_breakdown(self, mcq_state: Dict[str, Any]) -> Dict[str, Dict[str, int]]:
        """Extract question difficulty breakdown by skill"""
        generated_questions = mcq_state.get("generated_questions", {})
        difficulty_breakdown = {}

        for question_id, question in generated_questions.items():
            if isinstance(question, dict):
                node_id = question.get("node_id", "unknown")
                difficulty = question.get("meta", {}).get(
                    "difficulty", "intermediate")

                if node_id not in difficulty_breakdown:
                    difficulty_breakdown[node_id] = {
                        "basic": 0, "intermediate": 0, "advanced": 0}

                if difficulty in difficulty_breakdown[node_id]:
                    difficulty_breakdown[node_id][difficulty] += 1

        return difficulty_breakdown

    def _extract_jd_skill_requirements(self, mcq_state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Extract job description skill requirements"""
        # This would need to be derived from parsed_jd and skill_graph
        # For now, use candidate graph data as baseline
        candidate_graph = mcq_state.get("candidate_graph", [])
        jd_requirements = {}

        for node in candidate_graph:
            skill_id = node.get("node_id")
            priority = node.get("priority", "L")

            if skill_id:
                jd_requirements[skill_id] = {
                    "priority": priority,
                    "required": priority in ["H", "M"],
                    "depth": "intermediate"  # Could be extracted from skill_graph
                }

        return jd_requirements

    def _validate_resume_skills(self, mcq_state: Dict[str, Any]) -> Dict[str, bool]:
        """Validate resume skills against assessment performance"""
        candidate_graph = mcq_state.get("candidate_graph", [])
        skill_validation = {}

        for node in candidate_graph:
            skill_id = node.get("node_id")
            score = node.get("score", 0)

            if skill_id:
                # Consider skill validated if score >= 70%
                skill_validation[skill_id] = score >= 0.7 if score else False

        return skill_validation


# Global service instance
report_generation_service = ReportGenerationService()
