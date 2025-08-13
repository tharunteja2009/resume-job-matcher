from autogen_agentchat.agents import AssistantAgent
from src.ai.models.tracked_model_client import get_tracked_model_client
from autogen_core.tools import FunctionTool
from src.database.vector.chromadb_job_util import store_job_in_chromadb
import json


def sanitize_json_string(json_str):
    """Ensure the JSON string is properly formatted and escaped."""
    try:
        # First parse to validate
        data = json.loads(json_str)
        # Then properly format it
        return json.dumps(data, ensure_ascii=False)
    except json.JSONDecodeError:
        return None


chromadb_tool = FunctionTool(
    store_job_in_chromadb,
    description="tool to insert job summary in chunks to ChromaDB vector database",
)


def build_rag_using_job_context():
    agent = AssistantAgent(
        name="job_rag_builder_agent",
        description="an agent that builds a RAG (Retrieval-Augmented Generation) system using the context extracted from job posting. Use ChromaDB to store the context and use it to answer questions about the job posting document.",
        model_client=get_tracked_model_client("job_rag_building", "default"),
        system_message="""
        You are an intelligent assistant specialized in processing job descriptions for optimal candidate matching. Your primary goal is to structure and store job information in a way that maximizes matching accuracy with candidate profiles.

        Key Responsibilities:
        1. Process parsed job data and prepare it for vector storage in ChromaDB
        2. Structure information to optimize for semantic similarity matching with candidate profiles
        3. Ensure consistent formatting of technical terms and skills for better matching

        **Processing Instructions:**

        1. ESSENTIAL IDENTIFIERS (for unique job identification):
        - Job title (normalize common variations, e.g., "Sr. Software Engineer" = "Senior Software Engineer")
        - Company name
        - Location (standardize format: City, State/Country)
        - Job ID or Reference (if available)
        - Employment type (standardize: Full-time, Part-time, Contract, etc.)

        2. MATCHING CRITERIA (prioritize these for vector storage):
        Primary Criteria (highest weight):
        - Required technical skills (use standardized terms, e.g., "JavaScript" not "JS")
        - Years of experience (format as "X+ years in [technology/field]")
        - Core responsibilities (focus on technical aspects)
        
        Secondary Criteria:
        - Preferred skills (separate from required)
        - Industry experience
        - Education requirements
        - Certifications
        
        Additional Context:
        - Team size/structure
        - Project types
        - Technology stack
        - Development methodologies

        3. STORAGE FORMATTING:
        Create three types of chunks for effective matching:
        a) Skills-focused chunk:
           "Position: [title] | Required: [key technical skills] | Experience: [years] | Stack: [technologies]"
        
        b) Experience-focused chunk:
           "Role: [title] | Level: [seniority] | Primary: [main responsibilities] | Domain: [industry/domain]"
        
        c) Context chunk:
           "Environment: [team details] | Projects: [types] | Methodology: [approach] | Growth: [opportunities]"

        4. OPTIMIZATION RULES:
        - Use standardized skill names (maintain consistency with resume parsing)
        - Include skill variations (e.g., "AWS" with "Amazon Web Services")
        - Quantify requirements where possible (years, team size, etc.)
        - Structure technical requirements hierarchically (must-have vs. nice-to-have)

        5. STORAGE PROCESS:
        Use the `store_job_in_chromadb` tool to store the processed data:
        - Store each chunk type separately for targeted matching
        - Include cross-references between related chunks
        - Ensure all technical terms are standardized
        - Maintain context between chunks for coherent retrieval

        6. ERROR HANDLING:
        - If missing critical fields (title, company, key skills), return None
        - For partial data, store with confidence scores
        - Log any standardization issues

        After successful storage, return "COMPLETE" for termination.

        Remember: The quality of candidate matching depends on how well you structure and store this data. Focus on technical accuracy and standardization of terms.
        """,
        tools=[chromadb_tool],
    )
    return agent
