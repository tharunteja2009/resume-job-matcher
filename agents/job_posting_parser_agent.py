from autogen_agentchat.agents import AssistantAgent
from model.model_client import get_model_client

from util.mongo_util import insert_job_to_mongo
from autogen_core.tools import FunctionTool

insert_job_to_mongo_tool = FunctionTool(
    insert_job_to_mongo,
    description="A tool to insert job data into MongoDB",
)


def parse_job_agent():
    agent = AssistantAgent(
        name="parse_job_agent",
        description="",
        model_client=get_model_client(),
        system_message="""
        You are a job posting parsing agent. Your task is to analyze job posting content provided by the user and extract relevant information in the structured JSON format below. 
        Example format:
        {
            "job_title": "Software Engineer",
            "job_description": "Develop and maintain software applications.",
            "required_skills": "Python, Java, C++",
            "preferred_skills": "Docker, Kubernetes",
            "required_experience": "3+ years",
            "job_responsibilities": "Design, develop, and test software applications. Collaborate with cross-functional teams to define, design, and ship new features. Troubleshoot and debug applications",
            "job_mode": "Remote",
            "office_location": "San Francisco, CA",
            "job_type": "Full-time",
            "salary_range": "80,000 - 120,000 USD per year",
            "company_name": "Tech Solutions Inc.",
            "company_website": "https://www.techsolutions.com",
            "application_email": "careers@techsolutions.com",
            "hr_contact": "hr@techsolutions.com",
            "posting_date": "2023-10-01",
            "closing_date": "2023-11-01",
            "qualifications": "Bachelor's degree in Computer Science or related field",
            "additional_info": "Strong problem-solving skills and ability to work in a team environment"
        }
            
        Instructions:
                    1. Extract all fields as STRING values, not lists or complex objects
                    2. For multiple items (like skills or responsibilities), combine them into a single string with appropriate separators
                    3. If any field is missing in the job, omit it from the JSON
                    4. If you are unable to extract any useful information, return None
                    5. Ensure all values are properly escaped strings

        Important:
                    - Convert all lists into comma-separated strings
                    - Do not use arrays or nested objects
                    - All values must be strings, not lists or objects
                    - Use proper JSON string escaping

        Once you have extracted the data:
                    1. **Call the tool `insert_job_to_mongo_tool`** with the following parameters:
                    - `data`: The extracted information in JSON format (as a string)
                    - `index`: true
                    - `unique`: true
                    - `upsert`: true

        Example function call:
        ```
        insert_job_to_mongo_tool(
            data=json.dumps({
                "job_title": "Software Engineer",
                "required_skills": "Python, Java, C++",
                "job_responsibilities": "Design and develop software. Test and deploy applications.",
                ...
            }),
            index=true,
            unique=true,
            upsert=true
        )
        ```
                    
        2. After successful MongoDB insertion, forward the same structured data to the `job_rag_builder_agent` for RAG creation.

        Be precise, structured, and call the tool correctly.
        """,
        tools=[insert_job_to_mongo_tool],
        reflect_on_tool_use=False,
    )
    return agent
