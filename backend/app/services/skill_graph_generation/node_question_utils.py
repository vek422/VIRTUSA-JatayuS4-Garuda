from app.services.skill_graph_generation.state import SkillGraph

def get_question_distribution(skill_graph: SkillGraph, questions_per_node: int = 5):
    """
    Returns (total_questions, question_distribution_dict) for a given skill graph.
    question_distribution_dict: {"high": H*5, "medium": M*5, "low": L*5}
    """
    from .graph import count_nodes_by_priority
    counts = count_nodes_by_priority(skill_graph)
    distribution = {
        "high": counts["H"] * questions_per_node,
        "medium": counts["M"] * questions_per_node,
        "low": counts["L"] * questions_per_node
    }
    total = sum(distribution.values())
    return total, distribution
