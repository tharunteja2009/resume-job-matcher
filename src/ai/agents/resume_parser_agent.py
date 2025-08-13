from autogen_agentchat.agents import AssistantAgent
from src.ai.models.tracked_model_client import get_tracked_model_client
from src.database.mongo.mongo_util import insert_candidate_to_mongo
from autogen_core.tools import FunctionTool
import json


def sanitize_for_mongo(data_dict):
    """Sanitize data dictionary for MongoDB storage."""
    if isinstance(data_dict, dict):
        return {k: sanitize_for_mongo(v) for k, v in data_dict.items()}
    elif isinstance(data_dict, list):
        return [sanitize_for_mongo(item) for item in data_dict]
    elif isinstance(data_dict, (str, int, float, bool)):
        return data_dict
    elif data_dict is None:
        return None
    else:
        return str(data_dict)


def prepare_candidate_data(data):
    """Prepare candidate data for storage."""
    try:
        if isinstance(data, str):
            # Clean the data string before parsing
            data = data.strip()
            if not data:
                raise ValueError("Empty data string provided")

            # Parse JSON with better error handling
            try:
                data_dict = json.loads(data)
            except json.JSONDecodeError as e:
                print(f"JSON Parse Error: {e}")
                print(f"Data length: {len(data)} characters")
                print(f"Data preview: {data[:200]}...")
                if len(data) > 200:
                    print(f"Data ending: ...{data[-100:]}")
                raise ValueError(f"Invalid JSON format: {e}")
        else:
            data_dict = data

        # Sanitize the data
        sanitized_data = sanitize_for_mongo(data_dict)

        # Convert lists to strings for specific fields
        if "candidate_skills" in sanitized_data and isinstance(
            sanitized_data["candidate_skills"], list
        ):
            sanitized_data["candidate_skills"] = ", ".join(
                sanitized_data["candidate_skills"]
            )

        if "languages" in sanitized_data and isinstance(
            sanitized_data["languages"], list
        ):
            sanitized_data["languages"] = ", ".join(sanitized_data["languages"])

        # Ensure professional_experience is properly formatted
        if "professional_experience" in sanitized_data and isinstance(
            sanitized_data["professional_experience"], list
        ):
            for exp in sanitized_data["professional_experience"]:
                if "projects" in exp and isinstance(exp["projects"], list):
                    exp["projects"] = json.dumps(exp["projects"])

        return json.dumps(sanitized_data, ensure_ascii=False)
    except Exception as e:
        error_msg = f"Error preparing candidate data: {str(e)}"
        print(error_msg)
        return None


def safe_insert_candidate(data: str) -> str:
    """Safely insert candidate data into MongoDB with enhanced error handling.

    Args:
        data: JSON string containing candidate data

    Returns:
        Success message or detailed error message
    """
    try:
        # Validate input
        if not data or not isinstance(data, str):
            return "Error: No data provided or invalid data type"

        # Check data length first
        if len(data) > 2000:
            return f"Error: Data too large ({len(data)} chars). Please reduce to under 2000 characters."

        # Clean the data string
        data = data.strip()
        if not data:
            return "Error: Empty data string after cleaning"

        # Try to parse the JSON with detailed error reporting
        try:
            parsed_data = json.loads(data)
        except json.JSONDecodeError as parse_error:
            error_msg = str(parse_error)

            # Provide specific error details for debugging
            if "Unterminated string" in error_msg:
                # Find where the string was cut off
                lines = data.split("\n")
                total_lines = len(lines)

                return (
                    f"Error: JSON truncated (detected unterminated string). "
                    f"Data has {len(data)} characters across {total_lines} lines. "
                    f"Last 100 chars: ...{data[-100:]}. "
                    f"Please ensure complete JSON structure."
                )

            elif "Expecting" in error_msg:
                return (
                    f"Error: JSON syntax error - {error_msg}. "
                    f"Check JSON structure around character position mentioned in error."
                )

            else:
                return (
                    f"Error: JSON parsing failed - {error_msg}. "
                    f"Data length: {len(data)} chars. "
                    f"Preview: {data[:100]}{'...' if len(data) > 100 else ''}"
                )

        # Validate required fields in parsed data
        required_fields = ["candidate_name", "candidate_email", "candidate_phone"]
        missing_fields = [
            field for field in required_fields if field not in parsed_data
        ]

        if missing_fields:
            return f"Error: Missing required fields: {', '.join(missing_fields)}. Please ensure the JSON includes name, email, and phone number."

        # If parsing succeeds, proceed with preparation and insertion
        prepared_data = prepare_candidate_data(parsed_data)
        if prepared_data:
            insert_candidate_to_mongo(prepared_data)
            return f"✅ Successfully inserted candidate data for {parsed_data.get('candidate_name', 'Unknown')}"
        else:
            return "Error: Failed to prepare candidate data for insertion"

    except Exception as e:
        error_msg = f"Unexpected error inserting candidate data: {str(e)}"
        print(f"DETAILED ERROR: {error_msg}")
        return error_msg


insert_candidate_to_mongo_tool = FunctionTool(
    safe_insert_candidate,
    description="A tool to safely insert candidate data into MongoDB",
)


def parse_resume_agent():
    agent = AssistantAgent(
        name="parse_resume_agent",
        description="An agent that parses resumes and extracts relevant information such as experience, skills, and projects.",
        model_client=get_tracked_model_client("resume_parsing", "parsing"),
        system_message="""
        You are a resume parsing agent. Your task is to analyze resume content and create a clean, properly formatted JSON structure.

        CRITICAL: Due to system limitations, you MUST keep the JSON extremely concise to prevent truncation errors.

        Strict Formatting Rules:
        1. Use double quotes for all strings
        2. Properly escape special characters  
        3. MAXIMUM 2 jobs in professional_experience array
        4. Maximum 50 words per responsibility field
        5. Skills array maximum 10 items
        6. No nested objects deeper than 2 levels
        7. Omit optional fields if empty

        REQUIRED MINIMAL FORMAT:
        {
            "candidate_name": "Full Name",
            "candidate_email": "email@example.com", 
            "candidate_phone": "+country-number",
            "candidate_skills": ["Skill1", "Skill2", "Skill3"],
            "candidate_total_experience": "X years",
            "professional_experience": [
                {
                    "company": "Company Name",
                    "role": "Job Title", 
                    "start_date": "YYYY-MM-DD",
                    "end_date": "YYYY-MM-DD",
                    "responsibilities": "Brief 1-2 sentence summary only.",
                    "duration_of_job": "X years Y months"
                }
            ],
            "education": {
                "degree": "Degree Name",
                "institution": "University Name", 
                "graduation_year": "YYYY"
            }
        }

        CRITICAL CONSTRAINTS:
        - Total JSON must be under 1000 characters to prevent truncation
        - If resume has >2 jobs, only include the 2 most recent
        - Responsibilities: maximum 1 sentence, no more than 50 words
        - Remove all unnecessary fields and data
        - Test JSON validity before calling the tool

        Process:
        1. Extract ONLY essential information
        2. Create minimal JSON following the exact format above
        3. BEFORE calling the tool: Verify JSON is valid by attempting to parse it
        4. Check that JSON string length is reasonable (under 1500 chars)
        5. If JSON passes validation, call insert_candidate_to_mongo_tool
        6. Pass the same validated JSON to the next agent for RAG storage
        7. Always end with "COMPLETE" to terminate the conversation

        ERROR RECOVERY:
        If JSON validation fails or is too large:
        1. Create an even more minimal version with just name, email, skills (max 5), and 1 job
        2. Remove all optional fields
        3. Truncate any long text fields to 30 characters max
        4. Retry the tool call with the minimal JSON

        Remember: It's better to have minimal complete data than truncated unusable data.
        """,
        tools=[insert_candidate_to_mongo_tool],
        reflect_on_tool_use=False,
    )
    return agent
