"""
This graph is used to generate skill DAG (Directed Acyclic Graph) from job description
"""
from app.services.skill_graph_generation.state import State, SkillGraph, SkillNode, Configuration
from langgraph.graph import StateGraph, END, START
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import os
from dotenv import load_dotenv

# Use string annotations for forward references
# JobDescriptionFields will be passed as a dictionary to avoid import issues

load_dotenv()

# Define prompts directly to avoid import issues
DAG_SYSTEM_PROMPT = """You are a Skill Graph Architect working within an AI-powered technical assessment platform.

Your role is to generate and maintain structured Directed Acyclic Graphs (DAGs) that represent the hierarchical relationships between technical skills required for a given job role. These DAGs are used to drive adaptive assessment and personalized question generation.


DAG OBJECTIVE:

Each graph should represent:
- A set of 'core and supporting technical skills' relevant to a job.
- A recursive, tree-like structure of parent skills and their subskills.
- Accurate relationships between skills based on conceptual or practical dependencies.

The DAG must:
- Begin with top-level (root) skills derived from the job.
- Include recursive subskills under each parent skill node.
- Reflect skill dependencies clearly and consistently.


STRUCTURE & RULES:


1. Node Structure:
   Every skill node must follow this schema:
   {{
     "skill": "string",                 // The name of the skill or subskill
     "priority": "H" | "M" | "L",       // Priority level of the skill
     "subskills": [ ... same format ... ]  // Recursive list of child skills
   }}

2. Priority Definitions:
   - "H" (High): Core, essential skills central to the job.
   - "M" (Medium): Important supporting skills.
   - "L" (Low): Optional or nice-to-have skills — usually derived from resumes.

3. Subskill Logic:
   - Subskills must be conceptually or practically required to master their parent.
   - Subskills may themselves contain further subskills.
   - Avoid unnecessary depth — use recursion only where it adds meaningful structure.

4. Graph Constraints:
   - The graph must be *acyclic* — no circular dependencies.
   - Avoid duplicate nodes under multiple branches unless strongly justified.
   - Group related concepts under the most appropriate parent skill.

5. Consistency Requirements:
   - Always return fields in the same order: skill, priority, subskills.
   - Maintain consistent nesting behavior and naming conventions.
   - Repeated calls on the same input (or same graph extension) must produce *structurally similar outputs*.

6. Exclusions:
   - Do not include soft skills, behavioral traits, or general responsibilities.
   - Only include *concrete, technical, testable skills* (e.g., "Docker", "CI/CD", "Microservices").


OUTPUT FORMAT:

Always return a valid JSON object conforming to this schema:

{{
  "root_nodes": [
    {{
      "skill": "string",
      "priority": "H" | "M" | "L",
      "subskills": [
        {{
          "skill": "string",
          "priority": "H" | "M" | "L",
          "subskills": [ ... ]
        }}
      ]
    }},
    ...
  ]
}}

Do not include:
- Markdown
- Code blocks
- Comments
- Explanations or descriptions

Return only the structured JSON.
"""

SKILL_GRAPH_GENERATION_PROMPT = """
You are an intelligent assistant embedded in a skill-based candidate evaluation system. Your role is to convert a given Job Description (JD) into a hierarchical, structured skill graph used for adaptive assessment.


OBJECTIVE:

Read the JD below and extract *only technical skills*, organizing them into a recursive graph where:
- Each node has:
    - "skill": A specific, job-relevant technology, framework, concept, or tool.
    - "priority": One of:
        - "H" = High priority (core skill for the role)
        - "M" = Medium priority (important, but secondary)
    - "subskills": Prerequisites for the parent skill, structured the same way.

The output must represent a 'Directed Acyclic Graph (DAG)', structured as a recursive tree.


INSTRUCTIONS FOR EXTRACTION:


1. Root Node Selection:
   - Must be *explicitly or implicitly central* to the JD (e.g., DevOps, React, AWS, CI/CD, Python, Docker).
   - These are the top-level skills you will test the candidate on.

2. Subskill Extraction:
   - Identify *logical prerequisites* to master each parent skill (e.g., "CI/CD" → "Jenkins", "Pipeline Design").
   - Subskills must also be technical, practical, and independently valid.

3. Prioritization Rules:
   - Use "H" only for absolutely core skills for the role.
   - Use "M" for supporting or secondary skills.
   - *Do not use "L"* in this phase.

4. Recursion Depth:
   - Max recommended depth is 3 levels unless strongly justified.
   - Do not flatten everything; group concepts meaningfully.

5. Sorting Rules:
   - Root nodes must be sorted alphabetically.
   - Subskills must also be sorted alphabetically.
   - This ensures consistency across runs.

6. Consistency Guidelines:
   - Given the same or similar JD, your generated skill graph must remain largely consistent across runs.
   - Avoid random variance, excessive restructuring, or fluctuating depth.
   - Be deterministic in structure: always return the same format, field order, and prioritization logic.

7. Skills and subskills should not repeat across different branches in any situation.

EXCLUSIONS:

- Do not include soft skills (e.g., "communication", "leadership").
- Do not include generic job titles or duties (e.g., "collaborate with teams").
- Do not include abstract concepts unless they're testable (e.g., use “REST API” not “Web Development”).


OUTPUT FORMAT:

Return only a *valid JSON* object matching this exact schema:

{{
  "root_nodes": [
    {{
      "skill": "string",
      "priority": "H" | "M",
      "subskills": [
        {{
          "skill": "string",
          "priority": "H" | "M",
          "subskills": [ ... ]
        }}
      ]
    }},
    ...
  ]
}}

Ensure the response contains:
- No explanations
- No code formatting (like triple backticks)
- No markdown
- No surrounding text


JOB DESCRIPTION:

\"\"\"
{jd_text}
\"\"\"
"""


def get_llm():
    """Get LLM instance lazily to avoid initialization issues during import."""
    return ChatOpenAI(
        model="gpt-4o",
    )


def generate_skill_graph_from_raw_jd(state: State) -> State:
    """Generate skill graph from raw job description text."""
    try:
        llm = get_llm()
        if not state.raw_job_description:
            raise ValueError("No raw job description provided")

        # Use structured output with the SkillGraph model
        # structured_llm = llm.with_structured_output(SkillGraph)

        # Format the prompt with job description text
        formatted_prompt = SKILL_GRAPH_GENERATION_PROMPT.format(
            jd_text=state.raw_job_description
        )

        messages = [
            SystemMessage(content=DAG_SYSTEM_PROMPT),
            HumanMessage(content=formatted_prompt)
        ]

        # Get structured output
        result = llm.invoke(messages)
        raw_json = result.content[0] if isinstance(
            result.content, list) else result.content
        if isinstance(raw_json, dict):
            raw_json = str(raw_json)

        if raw_json.startswith("```json"):
            raw_json = raw_json.removeprefix(
                "```json").removesuffix("```").strip()
        elif raw_json.startswith("```"):
            raw_json = raw_json.removeprefix("```").removesuffix("```").strip()

        parsed_json = json.loads(raw_json)
        print("[DEBUG] Parsed JSON from LLM:", json.dumps(parsed_json, indent=2))  # Debug print
        # Ensure we get a SkillGraph instance

        result = SkillGraph(**parsed_json)
        return State(
            raw_job_description=state.raw_job_description,
            skill_graph=result,
            error=None
        )

    except Exception as e:
        return State(
            raw_job_description=state.raw_job_description,
            skill_graph=None,
            error=str(e)
        )


def handle_error(state: State) -> State:
    """Handle cases where no valid input is provided."""
    return State(
        raw_job_description=state.raw_job_description,
        skill_graph=None,
        error="No valid job description input provided (neither raw nor parsed)"
    )


def create_skill_graph_generation_graph():
    """Create and return the skill graph generation graph."""
    workflow = StateGraph(State, config_schema=Configuration)

    workflow.add_node("generate_from_raw", generate_skill_graph_from_raw_jd)

    workflow.add_edge(START, "generate_from_raw")
    workflow.add_edge("generate_from_raw", END)

    return workflow.compile()


# Create the graph instance
# skill_graph_generation_graph = create_skill_graph_generation_graph()
graph = create_skill_graph_generation_graph()

# Helper function to print skill graph in a readable format


def print_skill_graph(skill_graph: SkillGraph, indent: int = 0) -> None:
    """Print the skill graph in a readable tree format."""
    for node in skill_graph.root_nodes:
        print_skill_node(node, indent)


# Utility: Count nodes by priority and total
def count_nodes_by_priority(skill_graph: SkillGraph):
    """
    Returns a dict with counts for each priority (H, M, L) and total nodes.
    Example output: {"H": 3, "M": 5, "L": 2, "total": 10}
    """
    counts = {"H": 0, "M": 0, "L": 0, "total": 0}

    def traverse(nodes):
        for node in nodes:
            prio = node.priority
            if prio in counts:
                counts[prio] += 1
            counts["total"] += 1
            if node.subskills:
                traverse(node.subskills)

    traverse(skill_graph.root_nodes)
    return counts


def print_skill_node(node: SkillNode, indent: int = 0) -> None:
    """Print a skill node and its subskills recursively."""
    prefix = "  " * indent
    priority_emoji = {"H": "🔴", "M": "🟡", "L": "🟢"}
    emoji = priority_emoji.get(node.priority, "⚪")

    print(f"{prefix}{emoji} {node.skill} (Priority: {node.priority})")

    for subskill in node.subskills:
        print_skill_node(subskill, indent + 1)
