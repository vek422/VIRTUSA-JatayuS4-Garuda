"""
This graph is used to parse resume into structured output
"""
from langgraph.graph import StateGraph, END, START
from langchain_openai import ChatOpenAI
from app.services.resume_parsing.state import State, ResumeFields, RESUME_PARSING_SYSTEM_PROMPT


def get_llm():
    """Get LLM instance lazily to avoid initialization issues during import."""
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.1,
    )

# Define BaseModel for Resume Structure


def extract_resume_fields(state: State) -> State:
    """Extract structured fields from resume."""
    try:
        resume_text = state.raw_resume
        llm = get_llm()
        extractor_llm = llm.with_structured_output(ResumeFields)

        messages = [
            {"role": "system", "content": RESUME_PARSING_SYSTEM_PROMPT},
            {"role": "user", "content": resume_text}
        ]
        result = extractor_llm.invoke(messages)

        # Ensure we get a ResumeFields instance
        if isinstance(result, dict):
            result = ResumeFields(**result)

        return State(
            raw_resume=state.raw_resume,
            parsed_resume=result,
            error=None
        )

    except Exception as e:
        return State(
            raw_resume=state.raw_resume,
            parsed_resume=None,
            error=str(e)
        )


def create_resume_parsing_graph():
    """Create the resume parsing graph."""
    workflow = StateGraph(State)

    # Add nodes
    workflow.add_node("extract_resume", extract_resume_fields)

    # Add edges
    workflow.add_edge(START, "extract_resume")
    workflow.add_edge("extract_resume", END)

    return workflow.compile()


# Export the graph
graph = create_resume_parsing_graph()
