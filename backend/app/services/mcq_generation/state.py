from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Tuple, Dict
from app.services.jd_parsing.state import JobDescriptionFields
from app.services.resume_parsing.state import ResumeFields
from app.services.skill_graph_generation.state import SkillGraph


class UserResponse(BaseModel):
    type: Literal["generate_question",
                  "submit_response", "exit"]
    payload: Optional[dict] = Field(
        default=None,
        description="Optional payload for the user response, such as question ID or selected option"
    )


class SubmitResponsePayloadData(BaseModel):
    question_id: str
    selected_option: str


class SubmitResponsePayload(BaseModel):
    type: Literal["submit_response"]
    payload: SubmitResponsePayloadData


class GenerateQuestionPayload(BaseModel):
    type: Literal["generate_question"]
    payload: Optional[dict] = Field(
        default=None,
        description="Optional payload for generating a question, such as node ID or context"
    )


class ExitPayload(BaseModel):
    type: Literal["exit"]
    payload: Optional[dict] = Field(
        default=None,
        description="Optional payload for exiting the process, such as a message or status"
    )


class Question(BaseModel):
    question_id: str
    node_id: str
    prompt: str
    correct_option: str
    options: list[str] = Field(
        default_factory=list,
        description="List of options for the question"
    )
    meta: Optional[dict] = Field(
        default=None,
        description="Optional metadata for the question, such as difficulty level or topic"
    )


class Response(BaseModel):
    question_id: str
    selected_option: str
    is_correct: bool


valid_goto_options = ["generate_question", "submit_response", "exit"]


class GraphNodeState(BaseModel):
    node_id: str
    priority: Literal["H", "M", "L"]

    asked_questions: list[str] = Field(
        default_factory=list,
        description="List of question_id's asked at this node"
    )
    responses: list[str] = Field(
        default_factory=list,
        description="List of response_id's received for the questions asked at this node"
    )
    score: Optional[float]
    status: Literal["not_started", "in_progress", "completed"] = Field(
        default="not_started",
        description="Current status of the node in the graph"
    )


class AgentState(BaseModel):
    parsed_jd: JobDescriptionFields
    parsed_resume: ResumeFields
    skill_graph: SkillGraph

    metadata: Optional[dict] = Field(
        default=None,
        description="Optional metadata for the agent state"
    )

    candidate_graph: List[GraphNodeState] = Field(
        default_factory=list,
        description="List of graph nodes representing the candidate's skills and their evaluation"
    )

    generated_questions: Dict[str, Question] = Field(
        default_factory=dict,
        description="Dictionary of generated questions keyed by question ID"
    )
    candidate_response: Dict[str, Response] = Field(
        default_factory=dict,
        description="Dictionary of responses keyed by question ID"
    )
    node_queue: List[str] = Field(
        default_factory=list,
        description="Queue of node IDs to be processed next in the skill graph"
    )
    processed_nodes: List[str] = Field(
        default_factory=list,
        description="List of processed nodes"
    )
    last_node_id: Optional[str] = Field(
        default=None,
        description="ID of the last processed node"
    )
    question_queue: List[str] = Field(
        default_factory=list,
        description="Queue of question IDs to be asked next"
    )

    # Global Metrics
    total_questions_asked: int = Field(
        default=0,
        description="Total number of questions asked across all nodes")
    overall_score: float = Field(
        default=0.0,
        description="Overall score of the candidate based on responses"
    )
    start_time: Optional[str] = Field(
        default=None,
        description="Timestamp when the evaluation started"
    )
    questions_per_difficulty: Optional[Dict[str, int]] = Field(
        default=None,
        description="Configuration for number of questions per priority level (H/M/L). If not provided, uses default values."
    )

    finalized: bool = Field(
        default=False,
        description="Flag to indicate if the agent state has been finalized"
    )
