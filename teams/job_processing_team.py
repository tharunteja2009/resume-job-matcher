from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from agents.job_rag_builder_agent import build_rag_using_job_context
from agents.job_posting_parser_agent import parse_job_agent
from config.constants import MAX_TURNS as cons


def get_job_processing_team():
    job_rag_agent = build_rag_using_job_context()
    job_parsing_agent = parse_job_agent()
    termination_condition = TextMentionTermination("STOP") | TextMentionTermination(
        "APPROVE"
    )
    team = RoundRobinGroupChat(
        participants=[job_rag_agent, job_parsing_agent],
        max_turns=cons,
        termination_condition=termination_condition,
    )
    return team
