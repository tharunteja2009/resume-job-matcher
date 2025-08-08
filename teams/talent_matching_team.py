from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from agents.talent_matcher_agent import create_talent_matcher_agent
from teams.resume_processing_team import get_resume_processing_team
from teams.job_processing_team import get_job_processing_team


def get_comprehensive_matching_team():
    """
    Create a comprehensive team that combines resume processing, job processing, and talent matching.
    This team orchestrates the entire talent matching pipeline.
    """
    # Get individual processing teams
    resume_team = get_resume_processing_team()
    job_team = get_job_processing_team()

    # Get the talent matcher agent
    talent_matcher = create_talent_matcher_agent()

    # Create termination condition
    termination_condition = TextMentionTermination("MATCHING_COMPLETE")

    # Create the comprehensive team
    team = RoundRobinGroupChat(
        participants=[talent_matcher],  # Primary agent for matching analysis
        max_turns=3,  # Allow for detailed analysis
        termination_condition=termination_condition,
    )

    return team


def get_talent_matching_workflow():
    """
    Create a specialized workflow for talent matching operations.
    This focuses specifically on matching analysis using existing ChromaDB data.
    """
    talent_matcher = create_talent_matcher_agent()

    # Use a completion-based termination
    termination_condition = TextMentionTermination("ANALYSIS_COMPLETE")

    # Create focused matching team
    team = RoundRobinGroupChat(
        participants=[talent_matcher],
        max_turns=2,  # Focused on analysis only
        termination_condition=termination_condition,
    )

    return team
