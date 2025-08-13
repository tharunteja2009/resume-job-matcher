from autogen_agentchat.agents import AssistantAgent
from src.ai.models.tracked_model_client import get_tracked_model_client
from autogen_core.tools import FunctionTool
from src.database.vector.chromadb_resume_util import store_candidate_in_chromadb

chromadb_tool = FunctionTool(
    store_candidate_in_chromadb,
    description="tool to insert candidate summary in chunks to ChromaDB vector database",
)


def build_rag_using_resume_context():
    agent = AssistantAgent(
        name="resume_rag_builder_agent",
        description="an agent that builds a RAG (Retrieval-Augmented Generation) system using the context extracted from resumes. Use ChromaDB to store the context and use it to answer questions about the resumes.",
        model_client=get_tracked_model_client("resume_rag_building", "default"),
        system_message="""
        You are an intelligent assistant tasked with generating concise, high-quality, and human-readable summaries of candidate profiles.
        The resume has already been parsed by a previous agent. You will receive the parsed data in the message content. Your goal is to store this information in a structured format for use in a Retrieval-Augmented Generation (RAG) system.
        Use the tool `store_candidate_in_chromadb` to store candidate context in ChromaDB vector database. Store the context as semantically meaningful chunks to support future question answering and job matching use cases.

        **Instructions:**
        1. Extract the candidate's full name, phone number, and email address. These three fields combined serve as a unique identifier for each candidate.
        2. Check if a candidate with the same identifier (name + phone + email) already exists in ChromaDB.
        - If a match exists, override the existing entry with the new summary.
        - If no match is found, do not update any unrelated existing content in memory.
        3. Structure the summary in natural language using paragraph format. Ensure that it includes:
        - Full name, total years of experience, primary skills
        - Work experiences (company, role, duration, responsibilities)
        - Notable projects (title, role, technologies)
        - Education and certifications
        4. Store the generated summary using the `store_candidate_in_chromadb` tool, chunked appropriately for semantic retrieval using ChromaDB.

        If you're unable to extract the required candidate information (name, phone, or email), return `None`.
        
        once successfully stored, return a "COMPLETE" message for termination condition .
        """,
        tools=[chromadb_tool],
    )
    return agent
