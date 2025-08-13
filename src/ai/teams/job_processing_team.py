from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from src.ai.agents.job_rag_builder_agent import build_rag_using_job_context
from src.ai.agents.job_posting_parser_agent import parse_job_agent


def get_job_processing_team(num_jobs: int = 1):
    """
    Create a job processing team with dynamic max_turns based on workload.

    Args:
        num_jobs: Number of job postings to process (affects max_turns)

    Returns:
        RoundRobinGroupChat team configured for optimal processing
    """
    job_parsing_agent = parse_job_agent()
    job_rag_agent = build_rag_using_job_context()

    # Calculate optimal max_turns: 2 turns per job (parse → rag → complete)
    max_turns = 2 * num_jobs

    # Use a stricter termination condition to reduce back-and-forth
    termination_condition = TextMentionTermination("COMPLETE")

    team = RoundRobinGroupChat(
        participants=[job_parsing_agent, job_rag_agent],  # Parser first, then RAG
        max_turns=max_turns,
        termination_condition=termination_condition,
    )
    return team


def get_job_processing_team_legacy():
    """Legacy function for backward compatibility - uses default settings."""
    return get_job_processing_team(num_jobs=1)
