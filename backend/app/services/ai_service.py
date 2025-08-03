"""
AI Service for OpenAI integration
Handles job description parsing and skill graph generation
"""
import os
import json
import logging
from typing import Dict, Any, Optional
import openai
from app.services.jd_parsing import jd_parsing_graph
from app.services.skill_graph_generation import graph as skill_graph_generation_graph
from app.services.jd_parsing.state import State as JDState
from app.services.skill_graph_generation.state import State as SkillGraphState
from app.core.config import settings


logger = logging.getLogger(__name__)

class AIService:
    """AI Service for OpenAI integration following Single Responsibility Principle"""
    
    def __init__(self):
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key or api_key == "your-openai-api-key-here":
            logger.warning("OPENAI_API_KEY is missing or not set properly! AI features will not work.")
        elif not api_key.startswith("sk-"):
            logger.warning("OPENAI_API_KEY does not look like a valid OpenAI key.")
        openai.api_key = api_key
        self.model = "gpt-3.5-turbo"
    
    async def parse_job_description(self, job_description: str) -> Dict[str, Any]:
        """
        Parse job description using the jd_parsing graph
        Returns structured job data
        """
        try:
            state = JDState(raw_job_description=job_description)
            result_state = jd_parsing_graph.invoke(state)
            if result_state.get("error"):
                logger.error(f"JD Parsing error: {result_state['error']}")
                return {"error": result_state["error"]}
            parsed = result_state.get("parsed_job_description")
            return parsed.model_dump() if parsed and hasattr(parsed, 'model_dump') else parsed or {}
        except Exception as e:
            logger.error(f"Exception in parse_job_description: {str(e)}", exc_info=True)
            return {"error": f"Exception: {str(e)}"}

    async def generate_skill_graph(self, parsed_job_description: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate skill graph from parsed job description using the skill_graph_generation graph
        Returns structured skill hierarchy
        """
        try:
            jd_text = json.dumps(parsed_job_description)
            state = SkillGraphState(raw_job_description=jd_text)
            result_state = skill_graph_generation_graph.invoke(state)
            if result_state.get("error"):
                logger.error(f"Skill Graph Generation error: {result_state['error']}")
                return {"error": result_state["error"]}
            skill_graph = result_state.get("skill_graph")
            output = skill_graph.model_dump() if skill_graph and hasattr(skill_graph, 'model_dump') else skill_graph or {}
            print("[DEBUG] Skill graph output:", json.dumps(output, indent=2))  # Debug print
            return output
        except Exception as e:
            logger.error(f"Exception in generate_skill_graph: {str(e)}", exc_info=True)
            return {"error": f"Exception: {str(e)}"}

    async def process_job_description(self, job_description: str) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Complete AI processing pipeline
        Returns (parsed_job_description, skill_graph)
        """
        try:
            # Step 1: Parse job description
            parsed_jd = await self.parse_job_description(job_description)
            
            # Step 2: Generate skill graph
            skill_graph = await self.generate_skill_graph(parsed_jd)
            
            return parsed_jd, skill_graph
            
        except Exception as e:
            logger.error(f"Error in AI processing pipeline: {str(e)}")
            raise Exception(f"AI processing failed: {str(e)}")

# Singleton instance
ai_service = AIService()

def get_ai_service() -> AIService:
    """Dependency injection for AI service"""
    return ai_service
