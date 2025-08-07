from autogen_agentchat.agents import AssistantAgent
from model.model_client import get_model_client

from util.mongo_util import insert_candidate_to_mongo
from autogen_core.tools import FunctionTool

insert_candidate_to_mongo_tool = FunctionTool(
    insert_candidate_to_mongo,
    description="A tool to insert candidate data into MongoDB",
)


def parse_resume_agent():
    agent = AssistantAgent(
        name="parse_resume_agent",
        description="An agent that parses resumes and extracts relevant information such as experience, skills, and projects.",
        model_client=get_model_client(),
        system_message="""
        You are a resume parsing agent. Your task is to analyze resume content provided by the user and extract relevant information in the structured JSON format below.

        Example format:
        {
                    "candidate_name": "Tharun Peddi",
                    "candidate_email": "tharunteja2009@gmail.com",
                    "candidate_phone": "1234567890",
                    "candidate_skills": ["Python", "AI", "Machine Learning", "Data Analysis"],
                    "candidate_total_experience": "5 years",
                    "professional_experience": [
                        {
                        "company": "XYZ Corp",
                        "role": "AI Engineer",
                        "start_date": "2020-01-01",
                        "end_date": "2022-01-01",
                        "responsibilities": "Developed AI models for data analysis, collaborated with cross-functional teams to implement machine learning solutions.",
                        "duration_of_job": "2 years",
                        "projects": [
                            {
                            "project_name": "AI Model Development",
                            "description": "Developed a predictive model for customer behavior analysis.",
                            "technologies_used": ["Python", "TensorFlow", "Pandas"]
                            },
                            {
                            "project_name": "Data Analysis Automation",
                            "description": "Automated data analysis processes using Python scripts.",
                            "technologies_used": ["Python", "NumPy", "Pandas"]
                            }
                        ]
                        }
                    ],
                    "education": {
                        "degree": "Bachelor of Technology in Computer Science",
                        "institution": "ABC University",
                        "graduation_year": "2019",
                        "grade": "First Class",
                        "performance": "85%"
                    },
                    "certifications": [
                        {
                        "name": "Certified AI Engineer",
                        "issuing_organization": "AI Institute",
                        "issue_date": "2021-06-01"
                        }
                    ],
                    "languages": ["English", "Spanish"]
                    }

        Instructions:
                    1. If any field is missing in the resume, omit it from the JSON.
                    2. If you are unable to extract any useful information, return None.

        Once you have extracted the data:
                    1. **Call the tool `insert_candidate_to_mongo_tool`** with the following parameters:
                    - `data`: The extracted information in JSON format (as a string).
                    - `index`: true
                    - `unique`: true
                    - `upsert`: true

        Example function call
         insert_candidate_to_mongo_tool(data=<extracted_json>, index=true, unique=true, upsert=true)
                    
        2. **Send the extracted data to the next agent** called `resume_rag_builder_agent` for RAG creation.

        Be precise, structured, and call the tool correctly.
        """,
        tools=[insert_candidate_to_mongo_tool],
        reflect_on_tool_use=False,
    )
    return agent
