from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from agents.resume_parser_agent import parse_resume_agent
from agents.resume_rag_builder_agent import build_rag_using_resume_context


def get_resume_processing_team():
    resume_agent = parse_resume_agent()
    rag_agent = build_rag_using_resume_context()
    # Use a stricter termination condition to reduce back-and-forth
    termination_condition = TextMentionTermination("COMPLETE")
    team = RoundRobinGroupChat(
        participants=[resume_agent, rag_agent],
        max_turns=5,  # Allow proper agent interaction
        termination_condition=termination_condition,
    )
    return team
