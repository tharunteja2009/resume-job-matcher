from autogen_agentchat.agents import AssistantAgent
from src.ai.models.tracked_model_client import get_tracked_model_client
from src.database.mongo.mongo_util import insert_job_to_mongo_dict
from autogen_core.tools import FunctionTool
import json


def safe_insert_job(data: str) -> str:
    """Safely insert job data into MongoDB.

    Args:
        data: JSON string containing job data

    Returns:
        Success message or error message
    """
    try:
        # Handle the case where data might be already parsed or truncated
        if not data or not isinstance(data, str):
            return "Error: No data provided or invalid data type"

        # Try to parse the JSON - if it fails, it might be truncated
        try:
            # Parse JSON once
            parsed_data = json.loads(data)
        except json.JSONDecodeError as parse_error:
            # If JSON is truncated, try to detect and fix common issues
            error_msg = str(parse_error)
            if "Unterminated string" in error_msg or "unterminated string" in error_msg:
                return f"Error: JSON data appears to be truncated. Please ensure complete JSON is provided. Parse error: {error_msg}"
            else:
                return f"Error: Invalid JSON format: {error_msg}"

        # If parsing succeeds, proceed with insertion using parsed data
        insert_job_to_mongo_dict(parsed_data)
        return "Successfully inserted job data"

    except Exception as e:
        error_msg = f"Error inserting job data: {str(e)}"
        print(error_msg)
        return error_msg


insert_job_to_mongo_tool = FunctionTool(
    safe_insert_job,
    description="A tool to safely insert job data into MongoDB",
)


def parse_job_agent():
    agent = AssistantAgent(
        name="parse_job_agent",
        description="An agent that parses job descriptions and extracts structured information such as requirements, skills, and responsibilities.",
        model_client=get_tracked_model_client("job_parsing", "parsing"),
        system_message="""
        You are a job posting parsing agent. Your task is to analyze job posting content and extract relevant information in structured JSON format.

        IMPORTANT: Keep the JSON output CONCISE to avoid truncation issues.

        Important JSON Handling Rules:
        1. Use double quotes for all strings
        2. Properly escape special characters
        3. All values must be strings (convert lists to comma-separated strings)
        4. Keep descriptions concise to prevent JSON truncation

        Example format (KEEP CONCISE):
        {
            "job_title": "Software Engineer",
            "company_name": "Tech Solutions Inc.",
            "job_location": "Singapore",
            "required_skills": "Python, Java, REST APIs, SQL",
            "job_responsibilities": "Develop software applications, collaborate with teams, troubleshoot issues",
            "required_experience": "3+ years",
            "education_requirements": "Bachelor's in Computer Science",
            "job_type": "Full-time",
            "salary_range": "$80,000 - $120,000"
        }

        Instructions:
        1. Extract information and format as concise JSON
        2. Convert all lists into comma-separated strings
        3. If any field is missing, omit it from the JSON
        4. Keep descriptions brief to avoid truncation
        5. KEEP OUTPUT CONCISE - avoid long text that may cause JSON truncation

        Once you have extracted the data:
        1. **Call the tool `insert_job_to_mongo_tool`** with the extracted JSON as a string parameter.

        Example function call:
        insert_job_to_mongo_tool(data="<your_concise_json_here>")
                    
        2. **Send the extracted data to the next agent** called `job_rag_builder_agent` for RAG creation.

        Be precise, structured, and call the tool correctly with CONCISE data.
        """,
        tools=[insert_job_to_mongo_tool],
        reflect_on_tool_use=False,
    )
    return agent
