from autogen_agentchat.agents import AssistantAgent
from model.model_client import get_model_client
from autogen_core.tools import FunctionTool
from util.mem0_rag_util import rag_job_posting_with_mem0

mem0_tool = FunctionTool(
    rag_job_posting_with_mem0,
    description="tool to insert job summary in chunks to mem0",
)


def build_rag_using_job_context():
    agent = AssistantAgent(
        name="job_rag_builder_agent",
        description="an agent that builds a RAG (Retrieval-Augmented Generation) system using the context extracted from job posting. use mem0 to store the context and use it to answer questions about the job posting document.",
        model_client=get_model_client(),
        system_message="""
            You are a smart and reliable assistant responsible for processing job postings extracted from various sources. Your task is to validate, clean, and summarize the structured JSON data before storing it in a MongoDB database.
            You will receive a job posting in JSON format. Follow the instructions carefully before calling the tool `rag_job_posting_with_mem0`.

            ---

            **Instructions:**

            1. **Validate and Clean the JSON:**
            - Remove any fields that are:
                - Empty (e.g., `""`, `null`, or missing).
                - Clearly invalid or malformed (e.g., misspelled keys or stray characters).

            2. **Generate a Structured Summary:**
            - Create a **natural language paragraph** summarizing the job posting using the cleaned data.
            - The summary should be human-readable and include:
                - Job title, company name, and job mode (if available)
                - High-level job responsibilities and requirements
                - Job type and salary (if available)
                - Posting and closing dates (if present)
                - Company information (if available)
                - Hr contact information (if available)
                - office location (if available)
            - Example format:
                ```
                The job title is Software Engineer at Tech Solutions Inc. The role involves developing and maintaining software applications, requiring a Bachelor's degree in Computer Science or related field and 3+ years of experience in software development. The job is full-time with a salary range of 80,000 - 120,000 USD per year. The office is located in San Francisco, CA.
                ```

            3. **Store the Data in MongoDB:**
            - After generating the summary, append it to the cleaned JSON as a new field: `"job_summary"`.
            - Convert the entire JSON (including the summary) to a string.
            - Call the tool `insert_job_to_mongo_tool` with the following parameters:
                ```
                insert_job_to_mongo_tool(data=<cleaned_json_with_summary_as_string>, index=true, unique=true, upsert=true)
                ```

            4. **If no valid information is extractable:**
            - Return `None`.

            ---

            Your final output must be **either**:
            - A valid tool call containing the cleaned job JSON with the `job_summary` field,  
            **or**
            - `None` if the input is too malformed or missing to extract meaningful content.
        """,
        tools=[mem0_tool],
    )
    return agent
