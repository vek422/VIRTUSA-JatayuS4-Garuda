"""
This graph is used to parse job description into structured output
"""
from app.services.jd_parsing.state import State, JobDescriptionFields, JOB_DESCRIPTION_SYSTEM_PROMPT, Configuration
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI


def get_llm():
    """Get LLM instance lazily to avoid initialization issues during import."""
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.1,
    )


def extract_jd_fields(state: State) -> State:
    """Extract structured fields from job description."""
    try:
        jd_text = state.raw_job_description
        llm = get_llm()
        extractor_llm = llm.with_structured_output(JobDescriptionFields)

        messages = [
            {"role": "system", "content": JOB_DESCRIPTION_SYSTEM_PROMPT},
            {"role": "user", "content": jd_text}
        ]
        result = extractor_llm.invoke(messages)

        # Ensure we get a JobDescriptionFields instance
        if isinstance(result, dict):
            result = JobDescriptionFields(**result)

        # Return properly typed State
        return State(
            raw_job_description=state.raw_job_description,
            parsed_job_description=result,
            error=None
        )

    except Exception as e:
        return State(
            raw_job_description=state.raw_job_description,
            parsed_job_description=None,
            error=str(e)
        )


def create_graph():
    """Create and return the job description parsing graph."""
    workflow = StateGraph(State, config_schema=Configuration)

    # Add nodes
    workflow.add_node("extract_jd_fields", extract_jd_fields)

    # Set entry point
    workflow.set_entry_point("extract_jd_fields")

    # Add edges
    workflow.add_edge("extract_jd_fields", END)

    return workflow.compile()


# Create the graph instance
graph = create_graph()
