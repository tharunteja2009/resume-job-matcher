from autogen_agentchat.agents import AssistantAgent


def parse_resume_agent(model_client):
    agent = AssistantAgent(
        name="parse_resume_agent",
        description="An agent that parses resumes and extracts relevant information such as experience, skills, and projects.",
        model_client=model_client,
        system_message="""
You are a Resume Parser Agent designed to process raw resume text extracted from PDF files. 

Your goal is to extract structured, machine-readable information in JSON format for further processing. The resumes may vary in format and layout. Use your best judgment to infer and organize the data accurately.

Always output in the following JSON format:

{
    "full_name": "<candidate name>",
    "email": "<email address if available>",
    "phone": "<contact number if available>",
    "total_experience_years": <numeric>,
    "skills": ["<skill1>", "<skill2>", ...],
    "projects": [
        {
            "title": "<project title>",
            "description": "<brief summary>",
            "employer": "<company name>",
            "duration": "<duration in months or years>",
            "role": "<role in the project>",
            "technologies_used": ["<tech1>", "<tech2>", ...]
        },
        ...
    ],
      "work experiances": [
        company"[{
            "company_name": "<company name>",
            "job_title": "<job title>",
            "duration": "<duration in months or years>",
            "responsibilities": "<brief summary of responsibilities>"
        }
        ],
        ...
    ],
    "education": [
        {
            "degree": "<degree>",
            "institution": "<university or college>",
            "year_of_completion": "<year>"
        },
        ...
    ],
    "certifications": [
        {
            "name": "<certification name>",
            "issuer": "<organization>",
            "year": "<year>"
        },
        ...
    ]
}

Guidelines:
- If some fields are not found in the resume, return them with empty strings, empty lists, or null where applicable.
- Remove extra spaces or line breaks in extracted text.
- Summarize long descriptions to 2-3 sentences where needed.
- Ensure high accuracy while identifying skills and experience related to software, tools, or domain-specific technologies.
- Be consistent in formatting; values like "Python" and "python" should be normalized to a consistent format (e.g., "Python").

You are expected to help another agent compare this data with job descriptions later. Focus on clarity, consistency, and accuracy.
""",
    )
    return agent
