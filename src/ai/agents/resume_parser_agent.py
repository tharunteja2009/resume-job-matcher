from autogen_agentchat.agents import AssistantAgent
from src.ai.models.tracked_model_client import get_tracked_model_client
from src.database.mongo.mongo_util import insert_candidate_to_mongo_dict
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


def prepare_candidate_data_dict(data):
    """Prepare candidate data dict for storage."""
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

        return sanitized_data  # Return dict instead of JSON string
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
    print(f"🔧 MongoDB Tool Called - Data length: {len(data) if data else 0} chars")

    try:
        # Validate input
        if not data or not isinstance(data, str):
            error_msg = "Error: No data provided or invalid data type"
            print(f"❌ {error_msg}")
            return error_msg

        # Check data length first
        if len(data) > 2000:
            error_msg = f"Error: Data too large ({len(data)} chars). Please reduce to under 2000 characters."
            print(f"❌ {error_msg}")
            return error_msg

        # Clean the data string
        data = data.strip()
        if not data:
            error_msg = "Error: Empty data string after cleaning"
            print(f"❌ {error_msg}")
            return error_msg

        print(
            f"📝 Attempting to parse JSON data: {data[:200]}{'...' if len(data) > 200 else ''}"
        )

        # Try to parse the JSON with detailed error reporting
        try:
            parsed_data = json.loads(data)
            print(f"✅ JSON parsed successfully. Keys: {list(parsed_data.keys())}")
        except json.JSONDecodeError as parse_error:
            error_msg = str(parse_error)
            print(f"❌ JSON Parse Error: {error_msg}")

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
        required_fields = ["candidate_name"]  # Reduced to just name for better success
        missing_fields = [
            field for field in required_fields if field not in parsed_data
        ]

        if missing_fields:
            error_msg = f"Error: Missing required fields: {', '.join(missing_fields)}. Please ensure the JSON includes name."
            print(f"❌ {error_msg}")
            return error_msg

        print(f"🔄 Preparing candidate data for MongoDB insertion...")

        # If parsing succeeds, proceed with preparation and insertion
        prepared_data_dict = prepare_candidate_data_dict(parsed_data)
        if prepared_data_dict:
            print(f"📤 Calling MongoDB insertion function...")
            result = insert_candidate_to_mongo_dict(prepared_data_dict)
            print(f"📋 MongoDB Result: {result}")
            return result
        else:
            error_msg = "Error: Failed to prepare candidate data for insertion"
            print(f"❌ {error_msg}")
            return error_msg

    except Exception as e:
        error_msg = f"Unexpected error inserting candidate data: {str(e)}"
        print(f"❌ DETAILED ERROR: {error_msg}")
        import traceback

        traceback.print_exc()
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

        CRITICAL: You MUST call the insert_candidate_to_mongo_tool for EVERY resume processed.

        IMPORTANT: When processing "part X of Y" where Y > 1, this means you're seeing different sections of the SAME resume:
        - ALWAYS use the same candidate_name across all parts of the same resume
        - If you see a part that doesn't clearly show the full name, use context clues or generic descriptors
        - DO NOT create separate candidate entries for different parts of the same resume
        - Focus on extracting the primary candidate's information consistently

        REQUIRED MINIMAL FORMAT (MUST be under 500 characters total):
        {
            "candidate_name": "Full Name",
            "candidate_email": "email@example.com", 
            "candidate_phone": "+country-number",
            "candidate_skills": ["Skill1", "Skill2"],
            "candidate_total_experience": "X years"
        }

        MANDATORY PROCESS:
        1. Extract basic information (name is minimum requirement)
        2. For multi-part resumes: maintain consistent candidate_name across all parts
        3. Create simple JSON with available fields only
        4. ALWAYS call insert_candidate_to_mongo_tool with the JSON
        5. If tool call fails, create even simpler JSON with just name and try again
        6. Pass data to next agent after successful MongoDB insertion
        7. End with "COMPLETE"

        CRITICAL RULES:
        - You MUST call the MongoDB tool for every resume part (duplicate prevention is handled by the database)
        - Keep JSON under 500 characters to prevent truncation
        - If any field is missing, skip it (name is the only required field)
        - For multi-part processing: Use the SAME candidate name for all parts of one resume
        - If you can't determine the name from a part, use a consistent identifier based on the content
        - Always verify tool call succeeds before proceeding

        Example successful workflow:
        1. Extract: name="John Doe", email="john@email.com", phone="+1234567890"
        2. Create JSON: {"candidate_name":"John Doe","candidate_email":"john@email.com","candidate_phone":"+1234567890","candidate_skills":["Python"],"candidate_total_experience":"3 years"}
        3. Call: insert_candidate_to_mongo_tool(data='{"candidate_name":"John Doe","candidate_email":"john@email.com","candidate_phone":"+1234567890","candidate_skills":["Python"],"candidate_total_experience":"3 years"}')
        4. Verify success message received
        5. Pass to next agent: "Data stored in MongoDB successfully. Candidate: John Doe"
        6. Say "COMPLETE"

        If tool call fails with truncation error:
        1. Identify the issue (usually too much data)
        2. Remove all optional fields
        3. Truncate any long text fields to 30 characters max
        4. Retry the tool call with the minimal JSON

        Remember: It's better to have minimal complete data than truncated unusable data.
        """,
        tools=[insert_candidate_to_mongo_tool],
        reflect_on_tool_use=False,
    )
    return agent
