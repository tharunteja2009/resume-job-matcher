from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from src.ai.agents.resume_parser_agent import parse_resume_agent
from src.ai.agents.resume_rag_builder_agent import build_rag_using_resume_context


def get_resume_processing_team(num_resumes=1):
    """
    Create and return a resume processing team with optimized max_turns.

    Args:
        num_resumes (int): Number of resumes to process (default: 1)

    Returns:
        RoundRobinGroupChat: Configured team for resume processing
    """
    resume_parsing_agent = parse_resume_agent()
    resume_rag_agent = build_rag_using_resume_context()

    # Calculate optimal max_turns: 2 turns per resume
    max_turns = 2 * num_resumes

    # Use a stricter termination condition to reduce back-and-forth
    termination_condition = TextMentionTermination("COMPLETE")

    team = RoundRobinGroupChat(
        participants=[resume_parsing_agent, resume_rag_agent],  # Parser first, then RAG
        max_turns=max_turns,
        termination_condition=termination_condition,
    )
    return team
