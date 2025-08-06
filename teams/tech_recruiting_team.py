from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from agents.resume_parser_agent import parse_resume_agent
from config.constants import MAX_TURNS as cons


def get_tech_recruiter_team(model_client):
    resume_agent = parse_resume_agent(model_client)
    termination_condition = TextMentionTermination("STOP") | TextMentionTermination(
        "APPROVE"
    )
    team = RoundRobinGroupChat(
        participants=[resume_agent],
        max_turns=cons,
        termination_condition=termination_condition,
    )
    return team
