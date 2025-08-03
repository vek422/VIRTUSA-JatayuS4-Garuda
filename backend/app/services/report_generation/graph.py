import json
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from .state import ReportState

import logging
from dotenv import load_dotenv
load_dotenv()
llm = ChatOpenAI(model="o3")


def generate_report_node(state: ReportState) -> Dict[str, Any]:
    """
    Generate a comprehensive assessment report using LLM.
    """

    system_prompt = """You are an AI assessment evaluator generating professional reports for recruiters and hiring managers. 

Your task is to analyze candidate performance data and generate a comprehensive, structured JSON report that provides clear insights for hiring decisions.

CRITICAL EVALUATION RULES:

Strengths Analysis:
- ONLY include skills where the candidate scored above 80%
- PRIORITIZE skills that are also mentioned in the candidate's resume (showing both competency and experience)
- Focus on top 3-5 performing skills - do not list every skill above threshold
- Consider skill priority level (H > M > L) when selecting which strengths to highlight
- Phrase as specific technical competencies, not generic statements

Weaknesses Analysis:
- ONLY include skills where the candidate scored below 40%
- PRIORITIZE weaknesses in skills that are critical to the role (marked as "H" priority in job description)
- Focus on 2-4 most critical gaps - do not list every low-scoring skill
- Consider impact on job performance when selecting which weaknesses to highlight
- Frame as areas for development, not character flaws

Skill Gap Analysis:
- Compare candidate performance against job depth requirements
- Identify critical mismatches between required skill levels and demonstrated competency
- Consider both missing skills and insufficient depth in existing skills

Technical Score Calculation:
- Base on overall performance across all skill categories
- Weight high-priority skills more heavily than low-priority skills
- Consider both correct answers and question difficulty levels
- Factor in skill depth requirements vs demonstrated capability

Recommendation Logic:
- "Highly Recommended": 80%+ technical score, strong performance in critical skills, minimal skill gaps
- "Recommended": 60-79% technical score, solid performance with manageable gaps
- "Not Recommended": <60% technical score or critical skill failures

Domain Mastery Assessment:
- "Expert": Consistently high performance (85%+) across multiple related skills with appropriate depth
- "Proficient": Good performance (70%+) in core domain skills meeting job requirements
- "Developing": Mixed performance (50-69%) with clear learning path
- "Novice": Below 50% or insufficient demonstration of domain knowledge

Behavioral Indicators:
- Use test behavior data (time spent, questions skipped) to assess:
  - Confidence and Focus: High = consistent pacing, few skips; Low = erratic timing, many skips
  - Curiosity and Learning: High = good time management, minimal skips; Low = many skips, rushed completion

Confidence Intervals:
- Add uncertainty measures for borderline scores (55-65% range)
- Consider sample size and question difficulty distribution
- Flag areas where more assessment might be needed

Return ONLY a valid JSON object with the following exact structure:
{
    "candidate_name": "string",
    "technical_score": "float (0-100)",
    "passed_H": "integer",
    "passed_M": "integer", 
    "strengths": ["array of specific technical skills where candidate excelled"],
    "weaknesses": ["array of critical skill gaps that impact job performance"],
    "recommendation": "string (Highly Recommended/Recommended/Not Recommended)",
    "domain_mastery": "string (Expert/Proficient/Developing/Novice)",
    "alignment_with_jd": "string (Excellent/Good/Fair/Poor)",
    "curiosity_and_learning": "string (High/Medium/Low)",
    "summary_text": "string (2-3 sentences summarizing overall assessment and fit for role)",
    "skill_gap_analysis": "string (brief analysis of critical gaps vs job requirements)",
    "learning_path_recommendations": ["array of specific areas for improvement with priority"],
    "interview_focus_areas": ["array of topics to probe deeper in interviews"],
    "confidence_intervals": "string (uncertainty assessment for borderline scores)"
}

Guidelines:
- Be objective and data-driven in your assessment
- Base all evaluations on concrete performance metrics and behavioral data
- Avoid mentioning specific scores or percentages in the narrative fields
- Focus on actionable insights for hiring decisions
- Keep assessments professional and constructive
- Cross-reference resume skills with assessment performance
- Consider job priority levels and required skill depths


STYLE AND TONE INSTRUCTIONS:

- Use complete, well-structured sentences in all narrative fields (summary_text, skill_gap_analysis, learning_path_recommendations, interview_focus_areas, confidence_intervals).
- Avoid shorthand phrases like "High-priority:" or "Medium-priority:"; instead, express them as full statements. Example: "The candidate is strongly advised to take an advanced Kubernetes course, as this is a high-priority requirement for the role."
- Maintain a professional tone, suitable for recruiters and hiring managers.
- Use smooth transitions and avoid list-like structures in paragraph fields unless explicitly asked.
- Do not write phrases like "validating key resume claims" — instead, explain clearly how resume and performance align.
- Ensure learning recommendations and interview topics are framed in natural, human-readable sentences.


"""

    human_prompt = f"""
Candidate Assessment Data Analysis:

Candidate Name: {state.candidate_name or "Not Provided"}

Job Description Analysis: 
{state.parsed_jd}

Resume Analysis:
{state.parsed_resume}

Performance Summary:
- Total Score: {state.performance_summary.total_score}
- Questions Answered: {state.performance_summary.correct_answers}/{state.performance_summary.total_questions}
- High Priority Skills Passed: {state.performance_summary.passed_skills_H}
- Medium Priority Skills Passed: {state.performance_summary.passed_skills_M}
- Low Priority Skills Passed: {state.performance_summary.passed_skills_L}
- Resume-Mentioned Strengths: {', '.join(state.performance_summary.strengths)}
- Critical Weaknesses: {', '.join(state.performance_summary.weaknesses)}


Detailed Skill Performance & Priority Mapping:
{json.dumps(state.skill_breakdown, indent=2)}

Skill Priority Analysis:
{f"- High Priority Skills: {[skill for skill, priority in (state.skill_priorities or {}).items() if priority == 'H']}" if state.skill_priorities else "- Skill priorities not mapped"}
{f"- Critical Skills Performance: {json.dumps({skill: next((s for s in state.skill_breakdown if s.get('skill_name') == skill), {}) for skill, priority in (state.skill_priorities or {}).items() if priority == 'H'}, indent=2)}" if state.skill_priorities else "- Critical skills analysis unavailable"}

Resume vs Performance Validation:
{f"- Skills Claimed in Resume: {', '.join(state.resume_skills_mentioned)}" if state.resume_skills_mentioned else "- Resume skills not extracted"}
{f"- Validated Skills: {[skill for skill in (state.resume_skills_mentioned or []) if skill in [s['skill_name'] for s in state.skill_breakdown if s.get('score', 0) > 70]]}" if state.resume_skills_mentioned else "- Skills validation unavailable"}
{f"- Unvalidated Claims: {[skill for skill in (state.resume_skills_mentioned or []) if skill in [s['skill_name'] for s in state.skill_breakdown if s.get('score', 0) < 40]]}" if state.resume_skills_mentioned else "- Claims verification unavailable"}

Job Requirement Matching:
{f"- Required Skills Analysis: {json.dumps(state.jd_skill_requirements, indent=2)}" if state.jd_skill_requirements else "- JD skill requirements not mapped"}
{f"- Critical Requirements Met: {len([skill for skill, req in (state.jd_skill_requirements or {}).items() if req.get('required', False) and any(s['skill_name'] == skill and s.get('score', 0) > 70 for s in state.skill_breakdown)])}" if state.jd_skill_requirements else "- Requirements matching unavailable"}

Enhanced Analysis (Additional Data):
{f"- Question Difficulty Breakdown: {json.dumps(state.question_difficulty_breakdown, indent=2)}" if state.question_difficulty_breakdown else "- Question difficulty analysis not available"}
{f"- Resume Skill Validation Results: {json.dumps(state.resume_skill_validation, indent=2)}" if state.resume_skill_validation else "- Resume skill validation not performed"}
{f"- Assessment Metadata: {json.dumps(state.assessment_metadata, indent=2)}" if state.assessment_metadata else "- Additional assessment context not available"}

Cross-Reference Analysis Instructions:
1. Compare skill performance with resume mentions to identify validated vs. claimed competencies
2. Map skill priorities from job description to candidate performance levels
3. Identify question difficulty patterns and response accuracy correlation
4. Assess skill depth requirements vs demonstrated capability levels
5. Use overall skip rate to assess candidate confidence and test-taking behavior

Assessment Context:
- Assessment Date: {state.assessment_date.strftime('%Y-%m-%d')}

Analysis Requirements:
- Skill Gap Analysis: Identify critical mismatches between job requirements and performance
- Learning Path: Prioritize improvement areas based on job criticality and current competency gaps
- Interview Focus: Recommend specific technical areas requiring deeper validation
- Confidence Assessment: Flag borderline scores and high skip rates requiring additional evaluation

INSTRUCTIONS: Perform comprehensive analysis integrating all data sources to generate a professional assessment report following the specified evaluation rules and enhanced output format.
"""

    try:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]

        response = llm.invoke(messages)
        report_content = response.content.strip()

        if "```json" in report_content:
            report_content = report_content.split(
                "```json")[1].split("```")[0].strip()
        elif "```" in report_content:
            report_content = report_content.split("```")[1].strip()

        try:
            report_json = json.loads(report_content)
        except json.JSONDecodeError:
            report_json = {
                "candidate_name": state.candidate_name or "Unknown",
                "technical_score": state.performance_summary.total_score,
                "passed_H": state.performance_summary.passed_skills_H,
                "passed_M": state.performance_summary.passed_skills_M,
                "strengths": state.performance_summary.strengths,
                "weaknesses": state.performance_summary.weaknesses,
                "recommendation": "Unable to generate recommendation due to parsing error",
                "domain_mastery": "Unable to assess",
                "alignment_with_jd": "Unable to assess",
                "curiosity_and_learning": "Unable to assess",
                "summary_text": "Report generation encountered an error. Please review raw performance data.",
                "skill_gap_analysis": "Analysis unavailable due to processing error",
                "learning_path_recommendations": ["Technical assessment review required"],
                "interview_focus_areas": ["Validate technical competencies mentioned in resume"],
                "confidence_intervals": "High uncertainty - manual review recommended"
            }

        return {"generated_report": report_json}

    except Exception as e:
        error_report = {
            "candidate_name": state.candidate_name or "Unknown",
            "technical_score": state.performance_summary.total_score,
            "passed_H": state.performance_summary.passed_skills_H,
            "passed_M": state.performance_summary.passed_skills_M,
            "strengths": state.performance_summary.strengths,
            "weaknesses": state.performance_summary.weaknesses,
            "recommendation": "Error in report generation",
            "domain_mastery": "Unable to assess",
            "alignment_with_jd": "Unable to assess",
            "curiosity_and_learning": "Unable to assess",
            "summary_text": f"Report generation failed: {str(e)}",
            "skill_gap_analysis": f"Analysis failed: {str(e)}",
            "learning_path_recommendations": ["Manual assessment review required"],
            "interview_focus_areas": ["Comprehensive technical validation needed"],
            "confidence_intervals": "Assessment reliability compromised - full re-evaluation recommended"
        }

        return {"generated_report": error_report}

# Create the StateGraph


def create_report_graph():

    workflow = StateGraph(ReportState)

    workflow.add_node("generate_report", generate_report_node)

    workflow.set_entry_point("generate_report")

    workflow.add_edge("generate_report", END)

    return workflow.compile()


graph = create_report_graph()
