from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from app.services.mcq_generation.state import AgentState, GraphNodeState, Question, Response, UserResponse, SubmitResponsePayload
from app.services.jd_parsing.state import JobDescriptionFields
from app.services.skill_graph_generation.state import SkillGraph, SkillNode
from typing import List, Dict, Tuple, Optional
from langgraph.graph import StateGraph, END, START
from langgraph.types import interrupt, Command
from datetime import datetime
import json
from langchain_core.messages import HumanMessage
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row
import os
from dotenv import load_dotenv
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
load_dotenv()


def get_llm():
    return ChatOpenAI(
        model="gpt-4o",
        temperature=0.1,
    )


DEFAULT_QUESTIONS_PER_DIFFICULTY = {
    "H": 5,
    "M": 5,
    "L": 3
}


def get_questions_per_difficulty(state: AgentState) -> Dict[str, int]:
    """
    Get the questions per difficulty configuration from state or return default.

    Args:
        state: The agent state containing optional questions_per_difficulty config

    Returns:
        Dict[str, int]: Questions per priority level configuration
    """
    if state.questions_per_difficulty:
        return state.questions_per_difficulty
    return DEFAULT_QUESTIONS_PER_DIFFICULTY


def calculate_node_score(node_state: GraphNodeState, candidate_responses: Dict[str, Response]) -> float:
    """
    Calculate the score for a node based on correct responses.

    Args:
        node_state: The node state containing response IDs
        candidate_responses: Dictionary of responses keyed by question ID

    Returns:
        float: Score as a percentage (0.0 to 1.0)
    """
    if not node_state.responses:
        return 0.0

    correct_count = 0
    for response_id in node_state.responses:
        response = candidate_responses.get(response_id)
        if response and response.is_correct:
            correct_count += 1

    return correct_count / len(node_state.responses)


def generate_question_for_node(
    context: Dict,
    resume_text: str = "",
    job_description: Optional[JobDescriptionFields] = None,
    questions_per_difficulty: Optional[Dict[str, int]] = None
) -> Dict:
    """
    Generate MCQ for a skill node using the assembled context
    """
    current_skill = context["current_skill"]
    priority = context["priority"]
    node_history = context["node_history"]
    node_qa_history = context.get("node_qa_history", [])

    # Extract difficulty from job description's skill_depths, not from priority
    difficulty = "intermediate"  # Default fallback
    if job_description and job_description.skill_depths:
        for skill_depth in job_description.skill_depths:
            if skill_depth.skill.lower() == current_skill.lower():
                difficulty = skill_depth.depth
                break    # Include recent performance context if available
    performance_context = ""
    questions_asked_count = len(node_history["questions_asked"])
    questions_config = questions_per_difficulty or DEFAULT_QUESTIONS_PER_DIFFICULTY
    max_questions_for_priority = questions_config.get(priority, 5)

    if questions_asked_count > 0:
        performance_context = f"\nCandidate has answered {questions_asked_count}/{max_questions_for_priority} questions on this skill with current score: {node_history['current_score']:.1%}"

    # Add previous Q&A context to avoid duplicates
    previous_qa_context = ""
    if node_qa_history:
        previous_qa_context = "\n\nPrevious questions asked for this skill:"
        for i, qa in enumerate(node_qa_history, 1):
            status = "✓ Correct" if qa["is_correct"] else "✗ Incorrect"
            previous_qa_context += f"\n{i}. {qa['question']}"
            previous_qa_context += f"\n   Selected: {qa['selected_answer']} | Correct: {qa['correct_answer']} | {status}"
        previous_qa_context += "\n\nIMPORTANT: Generate a NEW question that is different from the above. Avoid similar topics, concepts, or question patterns."

    prompt = f"""
You are an AI MCQ generator for technical assessments.

Generate one multiple-choice question (MCQ) about the skill: "{current_skill}".
The question should match {difficulty} difficulty level (based on job requirements).

Context about candidate's session:
- Total questions asked: {context['overall_metrics']['total_questions_asked']}
- Session start: {context['overall_metrics']['session_start']}
{performance_context}{previous_qa_context}

Personalize the question using the candidate's resume if related experience is found.

Requirements:
- Provide exactly 4 answer options
- Only one correct answer
- Keep the question scenario-based or applied when possible
- Include a field for "matched_resume_info" (if resume mentions this skill or a related project/tool)

Skill Notes (if any): {current_skill}
Resume:
\"\"\"
{resume_text}
\"\"\"

Return only valid JSON in this format:
{{
  "question_text": "...",
  "options": ["A", "B", "C", "D"],
  "correct_answer": "",
  "difficulty": "{difficulty}",
  "node": "{current_skill}",
  "matched_resume_info": "..."
}}
"""

    try:
        llm = get_llm()
        response = llm.invoke([HumanMessage(content=prompt)])
        raw_content = response.content
        if isinstance(raw_content, list):
            if raw_content and isinstance(raw_content[0], str):
                raw = raw_content[0].strip()
            elif raw_content and isinstance(raw_content[0], dict):
                raw = json.dumps(raw_content[0])
            else:
                raw = ""
        elif isinstance(raw_content, str):
            raw = raw_content.strip()
        else:
            raw = str(raw_content).strip()

        if raw.startswith("```json"):
            raw = raw.removeprefix("```json").removesuffix("```").strip()
        elif raw.startswith("```"):
            raw = raw.removeprefix("```").removesuffix("```").strip()
        return json.loads(raw)

    except Exception as e:
        return {
            "question_text": f"ERROR: {e}",
            "options": [],
            "correct_answer": None,
            "difficulty": "error",
            "node": current_skill,
            "matched_resume_info": ""
        }


def flatten_graph(skill_nodes: List[SkillNode], depth: int = 0, parent: Optional[str] = None):
    flat = []
    for node in skill_nodes:
        flat.append({
            "node_id": node.skill,
            "priority": node.priority,
            "depth": depth,
            "children": [child.skill for child in node.subskills]
        })
        flat.extend(flatten_graph(node.subskills, depth + 1, node.skill))
    return flat


def compute_assessment_order(skill_graph: SkillGraph) -> List[str]:
    flat = flatten_graph(skill_graph.root_nodes)
    seen = set()
    unique = []
    for item in flat:
        if item["node_id"] not in seen:
            seen.add(item["node_id"])
            unique.append(item)
    unique.sort(key=lambda x: ("HML".index(x["priority"]), x["depth"]))
    return [u["node_id"] for u in unique]


def initialize(state: AgentState):
    """
    Initialize the agent state with:
    1. Flattened and ordered skill nodes
    2. Candidate graph with empty node states
    3. Node queue for processing order
    4. Metadata and counters
    """
    print("Initializing agent state...")
    # Ensure the skill graph is valid
    if state.start_time:
        print("Agent state already initialized, skipping.")
        print(state)
        return state

    # Get ordered nodes based on priority and depth
    ordered_nodes = compute_assessment_order(state.skill_graph)

    # Create a lookup map for efficient node finding
    node_lookup = {}

    def build_lookup(nodes):
        for node in nodes:
            node_lookup[node.skill] = node
            build_lookup(node.subskills)

    build_lookup(state.skill_graph.root_nodes)

    # Initialize candidate_graph with proper GraphNodeState objects
    candidate_graph = []
    for node_id in ordered_nodes:
        ref_node = node_lookup.get(node_id)
        if ref_node:
            candidate_graph.append(
                GraphNodeState(
                    node_id=node_id,
                    priority=ref_node.priority,
                    score=0.0,
                    status="not_started",
                    asked_questions=[],
                    responses=[]
                )
            )    # Set up the processing queue
    node_queue = [node.node_id for node in candidate_graph]

    # Set default questions_per_difficulty if not provided
    questions_per_difficulty = state.questions_per_difficulty or DEFAULT_QUESTIONS_PER_DIFFICULTY

    # Return updated state using .copy(update={...}) for proper persistence
    return state.model_copy(deep=True, update={
        "start_time": datetime.now().isoformat(),
        "total_questions_asked": 0,
        "last_node_id": None,
        "candidate_graph": candidate_graph,
        "node_queue": node_queue,
        "questions_per_difficulty": questions_per_difficulty
    }).model_dump()


def generate_question(state: AgentState):

    print("Generating question for current node...")

    # Step 1: Determine current node to work with
    current_node_id = None
    current_node_state = None

    # Check if we're continuing with an existing node
    if state.last_node_id:
        # Find the current node state
        for node_state in state.candidate_graph:
            if node_state.node_id == state.last_node_id:
                current_node_state = node_state
                current_node_id = state.last_node_id
                break        # Check if current node is completed
        if current_node_state:
            questions_config = get_questions_per_difficulty(state)
            max_questions_for_difficulty = questions_config.get(
                current_node_state.priority, 5)
            questions_asked = len(current_node_state.asked_questions)

            # Node is completed if:
            # 1. Reached max questions for difficulty, OR
            # 3. Status is already completedscore is not None else 0.0
            if (questions_asked >= max_questions_for_difficulty or
                    current_node_state.status == "completed"):                # Mark as completed and move to next node
                updated_candidate_graph = []
                for node_state in state.candidate_graph:
                    if node_state.node_id == current_node_state.node_id:
                        # Calculate the score of the node using helper function
                        node_score = calculate_node_score(
                            node_state, state.candidate_response)
                        # Mark this node as completed
                        updated_node = GraphNodeState(
                            node_id=node_state.node_id,
                            priority=node_state.priority,
                            score=node_score,
                            status="completed",
                            asked_questions=node_state.asked_questions.copy(),
                            responses=node_state.responses.copy()
                        )
                        updated_candidate_graph.append(updated_node)
                    else:
                        updated_candidate_graph.append(node_state)
                processed_nodes = state.processed_nodes + [current_node_id]
                # Update state and clear current node
                state = state.model_copy(deep=True, update={
                    "candidate_graph": updated_candidate_graph,
                    "last_node_id": None,
                    "processed_nodes": processed_nodes,
                })
                current_node_id = None
                current_node_state = None

    # Step 2: If no current node, get next node from queue
    if not current_node_id:
        if not state.node_queue:
            # No more nodes to process
            return state.model_copy(deep=True, update={"last_node_id": None})

        # Get next node from queue - create new queue without first element
        current_node_id = state.node_queue[0]
        new_node_queue = state.node_queue[1:]

        # Find the node state and update its status
        updated_candidate_graph = []
        for node_state in state.candidate_graph:
            if node_state.node_id == current_node_id:
                # Update this node's status to in_progress
                updated_node = GraphNodeState(
                    node_id=node_state.node_id,
                    priority=node_state.priority,
                    score=node_state.score,
                    status="in_progress",
                    asked_questions=node_state.asked_questions.copy(),
                    responses=node_state.responses.copy()
                )
                updated_candidate_graph.append(updated_node)
                current_node_state = updated_node
            else:
                updated_candidate_graph.append(node_state)

        # Update state with new queue and candidate graph
        state = state.model_copy(deep=True, update={
            "node_queue": new_node_queue,
            "last_node_id": current_node_id,
            "candidate_graph": updated_candidate_graph
        })

    if not current_node_state:
        # Skip if node not found in candidate graph
        # Step 3: Check if we can ask more questions for this node
        return Command(goto="generate_question", update=state.model_dump())
    questions_config = get_questions_per_difficulty(state)
    max_questions_for_difficulty = questions_config.get(
        current_node_state.priority, 5)
    questions_asked = len(current_node_state.asked_questions)

    # This node is done, mark completed and try next
    if questions_asked >= max_questions_for_difficulty:
        updated_candidate_graph = []
        for node_state in state.candidate_graph:
            if node_state.node_id == current_node_state.node_id:
                # Calculate the score of the node using helper function
                node_score = calculate_node_score(
                    node_state, state.candidate_response)
                updated_node = GraphNodeState(
                    node_id=node_state.node_id,
                    priority=node_state.priority,
                    score=node_score,
                    status="completed",
                    asked_questions=node_state.asked_questions.copy(),
                    responses=node_state.responses.copy()
                )
                updated_candidate_graph.append(updated_node)
            else:
                updated_candidate_graph.append(node_state)

        updated_state = state.model_copy(deep=True, update={
            "candidate_graph": updated_candidate_graph,
            "last_node_id": None
        })    # Step 4: Assemble Context for question generation

    # Extract actual questions and responses for current node to avoid duplicates
    node_qa_history = []
    for i, question_id in enumerate(current_node_state.asked_questions):
        question = state.generated_questions.get(question_id)
        if question and i < len(current_node_state.responses):
            response_id = current_node_state.responses[i]
            response = state.candidate_response.get(response_id)
            if response:
                node_qa_history.append({
                    "question": question.prompt,
                    "options": question.options,
                    "correct_answer": question.correct_option,
                    "selected_answer": response.selected_option,
                    "is_correct": response.is_correct
                })

    context = {
        "current_skill": current_node_id,
        "priority": current_node_state.priority,
        "node_history": {
            "questions_asked": current_node_state.asked_questions,
            "responses": current_node_state.responses,
            "current_score": current_node_state.score
        },
        "node_qa_history": node_qa_history,
        "overall_metrics": {
            "total_questions_asked": state.total_questions_asked,
            "session_start": state.start_time}
    }    # Step 5: Generate MCQ for current node
    resume_text = ""
    if state.parsed_resume and hasattr(state.parsed_resume, "model_dump"):
        parsed_resume = state.parsed_resume.model_dump()
        resume_text = f"Experience: {json.dumps(parsed_resume.get('experience', [],), indent=2)} Projects : {json.dumps(parsed_resume.get('projects', []))}"

    generated_mcq = generate_question_for_node(
        context=context,
        resume_text=resume_text,
        job_description=state.parsed_jd,
        questions_per_difficulty=get_questions_per_difficulty(state)
    )

    print(f"Generated MCQ: {generated_mcq}")
    # Create a Question object from the generated MCQ
    question = None
    if generated_mcq and "question_text" in generated_mcq:
        question = Question(
            question_id=f"{current_node_id}_{len(current_node_state.asked_questions) + 1}",
            node_id=current_node_id,
            prompt=generated_mcq["question_text"],
            correct_option=generated_mcq.get("correct_answer", "A"),
            options=generated_mcq.get("options", []),            meta={
                "difficulty": generated_mcq.get("difficulty", "intermediate"),
                "matched_resume_info": generated_mcq.get("matched_resume_info", "")
            }
        )

        # Update state with new question and candidate graph
        updated_candidate_graph = []
        for node_state in state.candidate_graph:
            if node_state.node_id == current_node_id:
                # Add question to this node's asked_questions
                updated_node = GraphNodeState(
                    node_id=node_state.node_id,
                    priority=node_state.priority,
                    score=node_state.score,
                    status=node_state.status,
                    asked_questions=node_state.asked_questions +
                    [question.question_id],
                    responses=node_state.responses.copy()
                )
                updated_candidate_graph.append(updated_node)
            else:
                updated_candidate_graph.append(node_state)

        # Update state with all changes
        state = state.model_copy(deep=True, update={
            "candidate_graph": updated_candidate_graph,
            "generated_questions": {**state.generated_questions, question.question_id: question},
            "total_questions_asked": state.total_questions_asked + 1,
            "question_queue": state.question_queue + [question.question_id]})

    # Update metadata
    final_state = state.model_copy(deep=True, update={
        "metadata": {
            "message": f"Generated question for node {current_node_id}: {question.prompt if question else 'No question generated.'}",
            "total_questions_asked": state.total_questions_asked,
            "current_node_id": current_node_id,
            "current_node_state": current_node_state,
            "generated_question_id": question.question_id if question else None,
        }
    })
    return Command(
        goto="interrupt_node",
        update=final_state.model_dump(),
    )


def interrupt_node(state: AgentState):
    """
    """
    print("Handling interrupt node...")
    # check if test can be submitted
    if state.finalized:
        print("Assessment already finalized, cannot interrupt.")
        return Command(goto="finalize_assessment", update=state.model_dump())

    # End conditions
    # 1. If no nodes in node_queue and last_node_id is None and question_queue is empty, finalize assessment
    if not state.node_queue and not state.last_node_id and not state.question_queue:
        state.metadata = {
            "message": "No more nodes or questions to process, finalizing assessment."
        }
        print("No more nodes or questions to process, finalizing assessment.")
        return Command(goto="finalize_assessment", update=state.model_dump())

    user_response = interrupt({
        "metadata": state.metadata,
    })

    try:
        user_response = UserResponse.model_validate(user_response)
    except Exception as e:
        print(f"Error validating user response: {e}")
        print("Invalid user response format, expected a dictionary.")
        error_state = state.model_copy(deep=True, update={
            "metadata": {
                "error": "Invalid user response format. Expected a dictionary."
            }
        })
        return Command(
            goto="interrupt_node",
            update=error_state
        )

    match user_response.type:
        case "submit_response":
            try:
                user_response = SubmitResponsePayload.model_validate(
                    user_response.model_dump())
            except Exception as e:
                print(f"Error validating submit response payload: {e}")
                error_state = state.model_copy(deep=True, update={
                    "metadata": {
                        "error": "Invalid submit response payload format."
                    }
                })
                return Command(
                    goto="interrupt_node",
                    update=error_state
                )

            question_id = user_response.payload.question_id
            question = state.generated_questions.get(question_id)
            if not question:
                error_state = state.model_copy(deep=True, update={
                    "metadata": {
                        "error": f"Question {question_id} not found in generated questions."
                    }
                })
                return Command(
                    goto="interrupt_node",
                    update=error_state.model_dump()
                )

            # Create the response object
            response = Response(
                question_id=question_id,
                selected_option=user_response.payload.selected_option,
                is_correct=question.correct_option == user_response.payload.selected_option
            )

            # Update candidate_graph with new response
            updated_candidate_graph = []
            for node_state in state.candidate_graph:
                if question_id in node_state.asked_questions:
                    # Add response to this node's responses
                    updated_node = GraphNodeState(
                        node_id=node_state.node_id,
                        priority=node_state.priority,
                        score=node_state.score,
                        status=node_state.status,
                        asked_questions=node_state.asked_questions.copy(),
                        responses=node_state.responses + [question_id]
                    )
                    updated_candidate_graph.append(updated_node)
                else:
                    updated_candidate_graph.append(node_state)

            # Remove question from queue
            new_question_queue = [
                q for q in state.question_queue if q != question_id]

            # Update state
            updated_state = state.model_copy(deep=True, update={
                "candidate_response": {**state.candidate_response, question_id: response},
                "candidate_graph": updated_candidate_graph,
                "question_queue": new_question_queue,
                "metadata": {
                    "message": f"Response recorded for question {question_id}."
                }
            })
            return Command(
                goto="interrupt_node",
                update=updated_state.model_dump()
            )
        case "generate_question":
            print("Generating next question...")
            updated_state = state.model_copy(deep=True, update={
                "metadata": {
                    "message": "Generating next question..."
                }
            })
            return Command(
                goto="generate_question",
                update=updated_state.model_dump()
            )
        case "exit":
            updated_state = state.model_copy(deep=True, update={
                "metadata": {
                    "message": "Exiting assessment."
                }
            })
            return Command(
                goto="finalize_assessment",
                update=updated_state.model_dump()
            )


def finalize_assessment(state: AgentState):
    """
    Finalize the assessment by cleaning up state and returning results.
    This is called when the assessment is complete or the user exits.
    """
    state.finalized = True
    return Command(goto=END, update=state.model_dump())


raw_graph = StateGraph(AgentState)

# Add nodes to the graph
raw_graph.add_node("initialize", initialize)
raw_graph.add_node("generate_question", generate_question)

raw_graph.add_node("interrupt_node", interrupt_node)
raw_graph.add_node("finalize_assessment", finalize_assessment)
# Define the flow
raw_graph.add_edge(START, "initialize")
raw_graph.add_edge("initialize", "interrupt_node")
raw_graph.add_edge("finalize_assessment", END)
# Global connection pool for PostgreSQL
_connection_pool = None


async def get_connection_pool():
    """Get or create a global connection pool"""
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = AsyncConnectionPool(
            conninfo=f"postgresql://{os.getenv('PSQL_USERNAME')}:{os.getenv('PSQL_PASSWORD')}@{os.getenv('PSQL_HOST')}:{os.getenv('PSQL_PORT')}/{os.getenv('PSQL_DATABASE_LANGGRAPH')}",
            max_size=20,
            kwargs={
                "autocommit": True,
                "prepare_threshold": 0,
                "row_factory": dict_row,
            }
        )
        # Open the pool
        await _connection_pool.open()
    return _connection_pool


async def close_connection_pool():
    """Close the global connection pool"""
    global _connection_pool
    if _connection_pool is not None:
        await _connection_pool.close()
        _connection_pool = None


async def setup_database_tables():
    """Setup required database tables for LangGraph checkpointing"""
    pool = await get_connection_pool()
    async with pool.connection() as conn:
        checkpointer = AsyncPostgresSaver(conn)
        # This will create the necessary tables if they don't exist
        await checkpointer.setup()


async def get_question_generation_graph():
    """Get the compiled graph with PostgreSQL checkpointer"""
    # Setup database tables first
    await setup_database_tables()

    pool = await get_connection_pool()

    # Get a connection from the pool for the checkpointer
    # Note: We're not using async with here because we want the connection to persist
    conn = await pool.getconn()

    # Create the checkpointer with the persistent connection
    checkpointer = AsyncPostgresSaver(
        conn, serde=JsonPlusSerializer(pickle_fallback=True))

    return raw_graph.compile(
        checkpointer=checkpointer,
        # Updated to match new node structure
        # interrupt_after=["interrupt_node"]
    )
