from autogen_agentchat.agents import AssistantAgent
from model.model_client import get_model_client
from util.mongo_util import insert_candidate_to_mongo
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
    """Safely insert candidate data into MongoDB.

    Args:
        data: JSON string containing candidate data

    Returns:
        Success message or error message
    """
    try:
        # Handle the case where data might be already parsed or truncated
        if not data or not isinstance(data, str):
            return "Error: No data provided or invalid data type"

        # Try to parse the JSON - if it fails, it might be truncated
        try:
            # First attempt at parsing
            test_parse = json.loads(data)
        except json.JSONDecodeError as parse_error:
            # If JSON is truncated, try to detect and fix common issues
            error_msg = str(parse_error)
            if "Unterminated string" in error_msg or "unterminated string" in error_msg:
                return f"Error: JSON data appears to be truncated. Please ensure complete JSON is provided. Parse error: {error_msg}"
            else:
                return f"Error: Invalid JSON format: {error_msg}"

        # If parsing succeeds, proceed with preparation and insertion
        prepared_data = prepare_candidate_data(data)
        if prepared_data:
            insert_candidate_to_mongo(prepared_data)
            return "Successfully inserted candidate data"
        else:
            return "Error: Failed to prepare candidate data for insertion"

    except Exception as e:
        error_msg = f"Error inserting candidate data: {str(e)}"
        print(error_msg)
        return error_msg


insert_candidate_to_mongo_tool = FunctionTool(
    safe_insert_candidate,
    description="A tool to safely insert candidate data into MongoDB",
)


def parse_resume_agent():
    agent = AssistantAgent(
        name="parse_resume_agent",
        description="An agent that parses resumes and extracts relevant information such as experience, skills, and projects.",
        model_client=get_model_client("parsing"),
        system_message="""
        You are a resume parsing agent. Your task is to analyze resume content and create a clean, properly formatted JSON structure.

        IMPORTANT: Keep the JSON output CONCISE to avoid truncation issues. Focus on essential information only.

        Important JSON Handling Rules:
        1. Use double quotes for all strings
        2. Properly escape special characters  
        3. Format lists consistently
        4. Keep strings for phone numbers and emails intact
        5. Handle dates in ISO format (YYYY-MM-DD)
        6. Format all skills as an array of strings
        7. LIMIT professional_experience to maximum 3 most recent/relevant jobs
        8. For responsibilities, use 1-2 sentences maximum per job
        9. Avoid very long descriptions to prevent JSON truncation

        Example format (KEEP CONCISE):
        {
            "candidate_name": "Tharun Peddi",
            "candidate_email": "example@email.com", 
            "candidate_phone": "+65-12345678",
            "candidate_skills": ["Python", "AI", "Machine Learning"],
            "candidate_total_experience": "5 years",
            "professional_experience": [
                {
                "company": "XYZ Corp",
                "role": "AI Engineer", 
                "start_date": "2020-01-01",
                "end_date": "2022-01-01",
                "responsibilities": "Developed AI models and collaborated with teams.",
                "duration_of_job": "2 years"
                }
            ],
            "education": {
                "degree": "Bachelor of Technology in Computer Science",
                "institution": "ABC University", 
                "graduation_year": "2019"
            },
            "languages": ["English", "Spanish"]
        }

        Instructions:
        1. If any field is missing in the resume, omit it from the JSON.
        2. If you are unable to extract any useful information, return None.
        3. KEEP OUTPUT CONCISE - avoid long text that may cause JSON truncation

        Once you have extracted the data:
        1. **Call the tool `insert_candidate_to_mongo_tool`** with the extracted JSON as a string parameter.

        Example function call:
        insert_candidate_to_mongo_tool(data="<your_concise_json_here>")
                    
        2. **Send the extracted data to the next agent** called `resume_rag_builder_agent` for RAG creation.

        Be precise, structured, and call the tool correctly with CONCISE data.
        """,
        tools=[insert_candidate_to_mongo_tool],
        reflect_on_tool_use=False,
    )
    return agent
