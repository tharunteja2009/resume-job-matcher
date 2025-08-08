from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from agents.job_rag_builder_agent import build_rag_using_job_context
from agents.job_posting_parser_agent import parse_job_agent


def get_job_processing_team():
    job_parsing_agent = parse_job_agent()
    job_rag_agent = build_rag_using_job_context()
    # Use a stricter termination condition to reduce back-and-forth
    termination_condition = TextMentionTermination("COMPLETE")
    team = RoundRobinGroupChat(
        participants=[job_parsing_agent, job_rag_agent],  # Parser first, then RAG
        max_turns=5,  # Allow proper agent interaction
        termination_condition=termination_condition,
    )
    return team
