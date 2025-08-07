import logging
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from agents.resume_parser_agent import parse_resume_agent
from agents.resume_rag_builder_agent import build_rag_using_resume_context
from agents.job_posting_parser_agent import parse_job_agent
from config.constants import MAX_TURNS as cons


def get_tech_recruiter_team():
    resume_agent = parse_resume_agent()
    rag_agent = build_rag_using_resume_context()
    job_parsing_agent = parse_job_agent()
    termination_condition = TextMentionTermination("STOP") | TextMentionTermination(
        "APPROVE"
    )
    team = RoundRobinGroupChat(
        participants=[resume_agent, rag_agent],
        max_turns=cons,
        termination_condition=termination_condition,
    )
    return team
