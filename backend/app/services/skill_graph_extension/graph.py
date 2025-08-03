"""
This graph is used to extend skill graphs with specific skills
"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END, START
from langchain_openai import ChatOpenAI
import json

# Import SkillNode and SkillGraph from skill_graph_generation
# We'll redefine them here to avoid import issues
from typing import Literal


def get_llm():
    """Get LLM instance lazily to avoid initialization issues during import."""
    return ChatOpenAI(
        model="gpt-4o",
        temperature=0.1,
    )


# Define priority type
Priority = Literal["H", "M", "L"]


class SkillNode(BaseModel):
    """Represents a skill node in the DAG with subskills and priority."""
    skill: str = Field(description="The name of the skill")
    priority: Priority = Field(
        description="Priority level: H (High), M (Medium), L (Low)")
    subskills: List["SkillNode"] = Field(
        default_factory=list, description="List of subskills")
    score: int = Field(default=0, description="Current score for this skill")
    total: int = Field(
        default=0, description="Total possible points for this skill")
    passed: bool = Field(
        default=False, description="Whether this skill assessment is passed")

    class Config:
        arbitrary_types_allowed = True


# Update forward references for recursive model
SkillNode.model_rebuild()


class SkillGraph(BaseModel):
    """Represents the complete skill graph with root nodes."""
    root_nodes: List[SkillNode] = Field(description="List of root skill nodes")


class ExtensionNode(BaseModel):
    """Represents a new L-priority node to be added to the skill graph."""
    skill: str = Field(description="The name of the new skill")
    priority: Literal["L"] = Field(
        description="Priority level (always L for extensions)")
    parent_skill: str = Field(
        description="The parent skill to attach this node to")
    subskills: List[str] = Field(default_factory=list,
                                 description="Always empty for new L-nodes")


class ExtensionResult(BaseModel):
    """Result containing new L-priority nodes to be added."""
    new_nodes: List[ExtensionNode] = Field(
        default_factory=list,
        description="List of new L-priority nodes to be added to the skill graph"
    )


# Skill graph extension prompt
SKILL_GRAPH_EXTENSION_SYSTEM_PROMPT = """

You are an intelligent assistant responsible for extending an existing skill graph (DAG) using information extracted from a candidate’s resume. This extended DAG will capture additional resume-specific skills as optional, low-priority nodes.

Your goal is to analyze the resume and identify concrete, technical skills that are relevant to the job role but are currently missing from the existing DAG (which was originally derived from the job description).

---
OBJECTIVE:
---

- Enrich the skill graph with new technical skills found in the candidate's resume.
- Only add skills that:
    - Are clearly technical
    - Have implementation value
    - Are not already present in the existing DAG
- Attach these new skills under the most appropriate parent node in the DAG.
- All new nodes must be labeled with priority "L" (Low) since they are optional, resume-specific additions.

---
EXTENSION RULES:
---

1. New Skill Identification:
   - Extract only high-confidence, high-level technical skills from the candidate’s resume.
   - Focus on skills that are missing entirely from the current DAG (do not duplicate any skill at any level).
   - Use the job description context to validate whether the skill is relevant or complementary.

2. Skill Categories to Include:
   You should only consider concrete, technical skills such as:
   - Programming languages (e.g., Python, Java, C++)
   - Frameworks (e.g., Django, React, FastAPI)
   - Libraries (e.g., NumPy, Pandas, TensorFlow)
   - Tools and platforms (e.g., Docker, Kubernetes, Git, AWS, Azure)
   - Databases (e.g., PostgreSQL, MongoDB, Redis)
   - Architectural concepts (e.g., REST APIs, Microservices, GraphQL)

3. What to Exclude:
   Strictly exclude the following:
   - Soft skills (e.g., communication, leadership)
   - Abstract or generic traits (e.g., problem-solving)
   - Non-technical domain knowledge (e.g., finance, healthcare without tech context)
   - Certifications or methodologies unless tied to a technical implementation (e.g., "AWS Certified" is not the same as "AWS EC2")

4. Parent Mapping Logic:
   - For each new skill, identify the most relevant existing node in the current graph and attach it as a subskill.
   - If no clear parent exists, select the closest conceptual anchor available.
   - The original graph structure must remain unchanged except for the addition of new L-priority subskills.

5. Node Priority:
   - All new nodes must have "priority": "L" (Low).
   - Do not alter or relabel any existing H or M nodes.

6. Selectivity and Volume:
   - Be highly selective. Prioritize only the most meaningful technical additions.
   - Return a maximum of 5 to 8 well-mapped new skills to maintain graph clarity.

---
OUTPUT FORMAT:
---
Return only a list of extension nodes in the following format:

[
  {{
    "skill": "string",             // Name of the new skill
    "priority": "L",
    "parent_skill": "string"       // Exact name of the existing parent skill in the DAG
  }},
  ...
]

---
IMPORTANT:
--- 
- Do not return the entire updated graph — only the list of new L-priority nodes and their parent mappings.
- Do not include any explanation, commentary, or markdown formatting.
- Avoid randomness. Results should remain consistent across similar resume inputs.

You will be provided with:
- The original skill graph (with H and M nodes)
- The candidate’s parsed resume
- The job description text for context
"""


@dataclass
class Configuration:
    """Configuration for the skill graph extension."""
    model: str = "gpt-4o-mini"
    temperature: float = 0.1


@dataclass
class State:
    """State for the skill graph extension."""
    jd_text: str = ""
    resume_text: str = ""
    original_skill_graph: Optional[SkillGraph] = None
    extended_skill_graph: Optional[SkillGraph] = None
    extension_nodes: Optional[ExtensionResult] = None
    error: Optional[str] = None


def identify_extension_nodes(state: State) -> State:
    """Identify new L-priority nodes to add to the skill graph."""
    try:
        jd_text = state.jd_text
        resume_text = state.resume_text
        skill_graph = state.original_skill_graph

        if not jd_text or not resume_text or not skill_graph:
            return State(
                jd_text=state.jd_text,
                resume_text=state.resume_text,
                original_skill_graph=state.original_skill_graph,
                extended_skill_graph=None,
                extension_nodes=None,
                error="Missing required input data (JD, resume, or skill graph)"
            )

        # Create the extension prompt
        extension_prompt = f"""

You are assisting in the extension of a skill graph (DAG) used for AI-powered technical assessments.

You have been provided with the following:
1. A Job Description (JD) that outlines the required technical competencies.
2. A candidate’s parsed resume containing their self-declared technical experience.
3. An existing skill graph containing only High (H) and Medium (M) priority nodes.

Your objective is to:
- Analyze the resume and extract *high-level technical skills* that are *not already present* anywhere in the current skill graph.
- Validate the relevance of these skills using the context of the job description.
- Map each new skill to the *most appropriate parent node* in the existing skill graph.
- Return only the *new L-priority nodes* (Low priority), which represent resume-specific but job-relevant technical skills.

---
INSTRUCTIONS:
---
- Only include *concrete technical skills* that fall into the following categories:
    - Programming Languages (e.g., Python, Java, Go)
    - Frameworks (e.g., React, Django, FastAPI)
    - Libraries (e.g., NumPy, Pandas, TensorFlow)
    - Tools & Platforms (e.g., Git, Docker, Kubernetes, AWS)
    - Databases (e.g., PostgreSQL, MongoDB, Redis)
    - Technologies (e.g., REST APIs, GraphQL, Microservices)

- Do NOT include:
    - Soft skills (e.g., communication, leadership)
    - Abstract or behavioral traits (e.g., problem-solving)
    - General domain knowledge without technical specificity
    - Certifications or methodologies unless they imply specific technical tools

- Each new node must:
    - Be labeled with priority "L"
    - Be attached under the most logically relevant *existing H or M node*
    - Not already exist anywhere in the current graph (root or subskills)

- Be selective and return *no more than 5–8* highly relevant technical additions.

---
CONTEXT:
---

Job Description:
\"\"\"
{jd_text}
\"\"\"

Candidate Resume:
\"\"\"
{resume_text}
\"\"\"

Existing Skill Graph (H and M only):
\"\"\"
{json.dumps(skill_graph.model_dump() if hasattr(skill_graph, 'model_dump') else skill_graph, indent=2)}
\"\"\"

---
REQUIRED OUTPUT:
---
Return only a list of new nodes in the following format:

[
  {{
    "skill": "string",
    "priority": "L",
    "parent_skill": "string"
  }},
  ...
]

Do not return the full graph. Do not include H or M nodes. Do not include any commentary or explanation. Only return a valid list of extension nodes.
"""

        llm = get_llm()
        extractor_llm = llm.with_structured_output(ExtensionResult)

        messages = [
            {"role": "system", "content": SKILL_GRAPH_EXTENSION_SYSTEM_PROMPT},
            {"role": "user", "content": extension_prompt}
        ]

        result = extractor_llm.invoke(messages)

        # Ensure we get an ExtensionResult instance
        if isinstance(result, dict):
            result = ExtensionResult(**result)

        return State(
            jd_text=state.jd_text,
            resume_text=state.resume_text,
            original_skill_graph=state.original_skill_graph,
            extended_skill_graph=None,
            extension_nodes=result,
            error=None
        )

    except Exception as e:
        return State(
            jd_text=state.jd_text,
            resume_text=state.resume_text,
            original_skill_graph=state.original_skill_graph,
            extended_skill_graph=None,
            extension_nodes=None,
            error=str(e)
        )


def extend_skill_graph(state: State) -> State:
    """Extend the skill graph with the identified L-priority nodes."""
    try:
        if state.error or not state.extension_nodes or not state.original_skill_graph:
            return State(
                jd_text=state.jd_text,
                resume_text=state.resume_text,
                original_skill_graph=state.original_skill_graph,
                # Return original if no extensions
                extended_skill_graph=state.original_skill_graph,
                extension_nodes=state.extension_nodes,
                error=state.error or "No extension nodes to process"
            )

        # Create a deep copy of the original skill graph
        extended_graph = SkillGraph.model_validate(
            state.original_skill_graph.model_dump() if hasattr(state.original_skill_graph, 'model_dump') else state.original_skill_graph)

        def attach_to_parent(graph_nodes: List[SkillNode], parent_name: str, new_node: SkillNode) -> bool:
            """Recursively find and attach new node to parent."""
            for node in graph_nodes:
                if node.skill.lower() == parent_name.lower():
                    node.subskills.append(new_node)
                    return True
                if attach_to_parent(node.subskills, parent_name, new_node):
                    return True
            return False

        def ensure_other_category(graph_nodes: List[SkillNode]) -> SkillNode:
            """Ensure there's an 'Other' category at the root level."""
            for node in graph_nodes:
                if node.skill.lower() == "other":
                    return node

            # Create new "Other" category
            other_node = SkillNode(
                skill="Other",
                priority="M",
                subskills=[],
                score=0,
                total=0,
                passed=False
            )
            graph_nodes.append(other_node)
            return other_node

        # Process each extension node
        attachment_failures = []
        for ext_node in state.extension_nodes.new_nodes:
            new_skill_node = SkillNode(
                skill=ext_node.skill,
                priority="L",
                subskills=[],
                score=0,
                total=0,
                passed=False
            )

            attached = attach_to_parent(
                extended_graph.root_nodes, ext_node.parent_skill, new_skill_node)

            if not attached:
                # If parent not found, attach to "Other" category
                other_node = ensure_other_category(extended_graph.root_nodes)
                other_node.subskills.append(new_skill_node)
                attachment_failures.append(
                    f"Parent '{ext_node.parent_skill}' not found for skill '{ext_node.skill}', attached to 'Other'")

        # Note any attachment failures but don't treat as complete error
        error_msg = None
        if attachment_failures:
            error_msg = f"Some attachments failed: {'; '.join(attachment_failures)}"

        return State(
            jd_text=state.jd_text,
            resume_text=state.resume_text,
            original_skill_graph=state.original_skill_graph,
            extended_skill_graph=extended_graph,
            extension_nodes=state.extension_nodes,
            error=error_msg
        )

    except Exception as e:
        return State(
            jd_text=state.jd_text,
            resume_text=state.resume_text,
            original_skill_graph=state.original_skill_graph,
            extended_skill_graph=None,
            extension_nodes=state.extension_nodes,
            error=str(e)
        )


def create_skill_graph_extension_graph():
    """Create the skill graph extension graph."""
    workflow = StateGraph(State)

    # Add nodes
    workflow.add_node("identify_extension_nodes", identify_extension_nodes)
    workflow.add_node("extend_skill_graph", extend_skill_graph)

    # Add edges
    workflow.add_edge(START, "identify_extension_nodes")
    workflow.add_edge("identify_extension_nodes", "extend_skill_graph")
    workflow.add_edge("extend_skill_graph", END)

    return workflow.compile()


# Export the graph
graph = create_skill_graph_extension_graph()
