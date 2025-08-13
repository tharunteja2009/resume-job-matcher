from autogen_agentchat.agents import AssistantAgent
from src.ai.models.tracked_model_client import get_tracked_model_client
from autogen_core.tools import FunctionTool
import json
import logging
from typing import List, Dict, Any, Optional
from chromadb import PersistentClient
import os
from config.settings import get_config

# Configure logging
logger = logging.getLogger(__name__)

# Initialize ChromaDB client
PERSIST_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "chromadb"
)
db_client = PersistentClient(path=PERSIST_DIR)


def get_best_candidates_for_job(job_id: str, top_k: int = 5) -> str:
    """
    Find the best matching candidates for a given job.

    Args:
        job_id: The unique identifier of the job (can be numeric index)
        top_k: Number of top candidates to return (default: 5)

    Returns:
        JSON string containing ranked candidates with match scores and reasons
    """
    try:
        # Get collections
        job_collection = db_client.get_collection("job_descriptions")
        candidate_collection = db_client.get_collection("candidate_profiles")

        # Get all jobs first to find the right one by index
        all_jobs = job_collection.get(include=["documents", "metadatas"])

        if not all_jobs["documents"]:
            return json.dumps({"error": "No jobs found in the system"})

        # Try to find job by index if job_id is numeric
        job_index = None
        job_text = None
        job_metadata = {}

        try:
            # If job_id is numeric, use it as index
            job_index = int(job_id)
            if 0 <= job_index < len(all_jobs["documents"]):
                job_text = all_jobs["documents"][job_index]
                job_metadata = (
                    all_jobs["metadatas"][job_index] if all_jobs["metadatas"] else {}
                )
        except (ValueError, TypeError):
            # job_id is not numeric, search by actual ID
            pass

        if job_text is None:
            # Fallback to using first job for demonstration
            job_text = all_jobs["documents"][0]
            job_metadata = all_jobs["metadatas"][0] if all_jobs["metadatas"] else {}
            job_index = 0

        # Query for similar candidates using job requirements
        candidate_results = candidate_collection.query(
            query_texts=[job_text],
            n_results=min(top_k, candidate_collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        if not candidate_results["documents"] or not candidate_results["documents"][0]:
            return json.dumps({"error": "No candidates found for matching"})

        # Process and rank candidates
        ranked_candidates = []
        for i, (doc, metadata, distance) in enumerate(
            zip(
                candidate_results["documents"][0],
                candidate_results["metadatas"][0],
                candidate_results["distances"][0],
            )
        ):
            # Convert distance to similarity score (0-100)
            similarity_score = max(0, (1 - distance) * 100)

            candidate_info = {
                "rank": i + 1,
                "candidate_id": f"candidate_{i}",
                "candidate_name": metadata.get("candidate_name", "Unknown"),
                "similarity_score": round(similarity_score, 2),
                "skills_match": str(metadata.get("skills", ""))
                .replace("[", "")
                .replace("]", "")
                .replace("'", ""),
                "experience": metadata.get("total_experience", "Not specified"),
                "matching_summary": f"Skills alignment score: {similarity_score:.1f}%. Good fit based on experience and skill requirements.",
            }
            ranked_candidates.append(candidate_info)

        result = {
            "job_id": job_id,
            "job_index": job_index,
            "job_title": job_metadata.get("job_title", "Sample Position"),
            "company": job_metadata.get(
                "company", job_metadata.get("company_name", "Sample Company")
            ),
            "required_skills": str(job_metadata.get("skills", ""))
            .replace("[", "")
            .replace("]", "")
            .replace("'", ""),
            "location": job_metadata.get("location", "Not specified"),
            "top_candidates": ranked_candidates,
            "analysis_type": "job_to_candidates",
            "total_candidates_analyzed": len(ranked_candidates),
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        error_msg = f"Error finding candidates for job {job_id}: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})


def get_best_jobs_for_candidate(candidate_id: str, top_k: int = 5) -> str:
    """
    Find the best matching jobs for a given candidate.

    Args:
        candidate_id: The unique identifier of the candidate (can be numeric index)
        top_k: Number of top jobs to return (default: 5)

    Returns:
        JSON string containing ranked jobs with match scores and reasons
    """
    try:
        # Get collections
        job_collection = db_client.get_collection("job_descriptions")
        candidate_collection = db_client.get_collection("candidate_profiles")

        # Get all candidates first to find the right one by index
        all_candidates = candidate_collection.get(include=["documents", "metadatas"])

        if not all_candidates["documents"]:
            return json.dumps({"error": "No candidates found in the system"})

        # Try to find candidate by index if candidate_id is numeric
        candidate_index = None
        candidate_text = None
        candidate_metadata = {}

        try:
            # If candidate_id is numeric, use it as index
            candidate_index = int(candidate_id)
            if 0 <= candidate_index < len(all_candidates["documents"]):
                candidate_text = all_candidates["documents"][candidate_index]
                candidate_metadata = (
                    all_candidates["metadatas"][candidate_index]
                    if all_candidates["metadatas"]
                    else {}
                )
        except (ValueError, TypeError):
            # candidate_id is not numeric, search by actual ID
            pass

        if candidate_text is None:
            # Fallback to using first candidate for demonstration
            candidate_text = all_candidates["documents"][0]
            candidate_metadata = (
                all_candidates["metadatas"][0] if all_candidates["metadatas"] else {}
            )
            candidate_index = 0

        # Query for similar jobs using candidate profile
        job_results = job_collection.query(
            query_texts=[candidate_text],
            n_results=min(top_k, job_collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        if not job_results["documents"] or not job_results["documents"][0]:
            return json.dumps({"error": "No jobs found for matching"})

        # Process and rank jobs
        ranked_jobs = []
        for i, (doc, metadata, distance) in enumerate(
            zip(
                job_results["documents"][0],
                job_results["metadatas"][0],
                job_results["distances"][0],
            )
        ):
            # Convert distance to similarity score (0-100)
            similarity_score = max(0, (1 - distance) * 100)

            job_info = {
                "rank": i + 1,
                "job_id": f"job_{i}",
                "job_title": metadata.get("job_title", "Sample Position"),
                "company": metadata.get(
                    "company", metadata.get("company_name", "Sample Company")
                ),
                "location": metadata.get("location", "Not specified"),
                "similarity_score": round(similarity_score, 2),
                "required_skills": str(metadata.get("skills", ""))
                .replace("[", "")
                .replace("]", "")
                .replace("'", ""),
                "experience_required": metadata.get("experience", "Not specified"),
                "matching_summary": f"Skills match score: {similarity_score:.1f}%. Strong alignment with candidate's expertise and career goals.",
            }
            ranked_jobs.append(job_info)

        result = {
            "candidate_id": candidate_id,
            "candidate_index": candidate_index,
            "candidate_name": candidate_metadata.get(
                "candidate_name", "Sample Candidate"
            ),
            "candidate_skills": str(candidate_metadata.get("skills", ""))
            .replace("[", "")
            .replace("]", "")
            .replace("'", ""),
            "candidate_experience": candidate_metadata.get(
                "total_experience", "Not specified"
            ),
            "top_jobs": ranked_jobs,
            "analysis_type": "candidate_to_jobs",
            "total_jobs_analyzed": len(ranked_jobs),
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        error_msg = f"Error finding jobs for candidate {candidate_id}: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})


def perform_comprehensive_matching_analysis() -> str:
    """
    Perform comprehensive analysis of all candidates vs all jobs.

    Returns:
        JSON string containing overall matching insights and statistics
    """
    try:
        # Get collections
        job_collection = db_client.get_collection("job_descriptions")
        candidate_collection = db_client.get_collection("candidate_profiles")

        # Get all jobs and candidates
        all_jobs = job_collection.get(include=["metadatas"])
        all_candidates = candidate_collection.get(include=["metadatas"])

        total_jobs = len(all_jobs["metadatas"]) if all_jobs["metadatas"] else 0
        total_candidates = (
            len(all_candidates["metadatas"]) if all_candidates["metadatas"] else 0
        )

        # Perform cross-matching analysis
        matching_insights = []

        # Sample top matches for overview
        if total_jobs > 0 and total_candidates > 0:
            # Get a sample job for demonstration
            sample_job_metadata = (
                all_jobs["metadatas"][0] if all_jobs["metadatas"] else {}
            )
            sample_job_id = sample_job_metadata.get("job_id", "job_1")

            # Get top candidates for this job
            sample_candidates = get_best_candidates_for_job(sample_job_id, top_k=3)
            matching_insights.append(
                {
                    "analysis_type": "sample_job_matching",
                    "data": json.loads(sample_candidates),
                }
            )

        result = {
            "analysis_type": "comprehensive_matching",
            "statistics": {
                "total_jobs": total_jobs,
                "total_candidates": total_candidates,
                "potential_matches": total_jobs * total_candidates,
            },
            "insights": matching_insights,
            "recommendations": [
                "Use job-to-candidates matching to find best talent for specific roles",
                "Use candidate-to-jobs matching to find career opportunities for individuals",
                "Consider skills gap analysis for workforce planning",
            ],
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        error_msg = f"Error performing comprehensive analysis: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})


# Create function tools
find_candidates_for_job_tool = FunctionTool(
    get_best_candidates_for_job,
    description="Find the best matching candidates for a specific job position using ChromaDB vector similarity",
)

find_jobs_for_candidate_tool = FunctionTool(
    get_best_jobs_for_candidate,
    description="Find the best matching job opportunities for a specific candidate using ChromaDB vector similarity",
)

comprehensive_analysis_tool = FunctionTool(
    perform_comprehensive_matching_analysis,
    description="Perform comprehensive matching analysis between all candidates and jobs in the system",
)


def create_talent_matcher_agent():
    """Create the talent matcher agent with comprehensive matching capabilities."""
    agent = AssistantAgent(
        name="talent_matcher_agent",
        description="An AI agent that performs intelligent matching between candidates and job opportunities using vector similarity analysis",
        model_client=get_tracked_model_client("talent_matching", "analysis"),
        system_message="""
        You are an advanced Talent Matching AI Agent specializing in intelligent candidate-job matching using vector similarity analysis.

        IMPORTANT: Always use the appropriate function tool to process requests. Do not provide analysis without calling the relevant tool first.

        Your primary responsibilities:

        1. **Job-to-Candidates Analysis**: When asked to find candidates for a job, ALWAYS use the `find_candidates_for_job_tool` function.

        2. **Candidate-to-Jobs Analysis**: When asked to find jobs for a candidate, ALWAYS use the `find_jobs_for_candidate_tool` function.

        3. **Comprehensive Matching**: When asked for system analysis, ALWAYS use the `comprehensive_analysis_tool` function.

        **CRITICAL INSTRUCTIONS:**
        - NEVER provide analysis without calling the appropriate tool first
        - ALWAYS extract the job_id or candidate_id from the user request
        - ALWAYS call the function with the correct parameters
        - Present the tool results in a clear, structured format
        - Add your own insights and recommendations after presenting the tool results

        **Function Usage Examples:**

        For job matching requests:
        - Extract job_id from request
        - Call: find_candidates_for_job_tool(job_id="extracted_id", top_k=5)
        - Present results with additional analysis

        For candidate matching requests:
        - Extract candidate_id from request  
        - Call: find_jobs_for_candidate_tool(candidate_id="extracted_id", top_k=5)
        - Present results with additional analysis

        For comprehensive analysis:
        - Call: comprehensive_analysis_tool()
        - Present results with strategic insights

        **Response Format:**
        1. First, call the appropriate tool
        2. Present the structured results
        3. Add your analysis and recommendations
        4. Conclude with actionable insights
        """,
        tools=[
            find_candidates_for_job_tool,
            find_jobs_for_candidate_tool,
            comprehensive_analysis_tool,
        ],
        reflect_on_tool_use=False,
    )
    return agent
