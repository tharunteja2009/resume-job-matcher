import os
import json
import logging
from typing import Dict, Any, List
from datetime import datetime
from chromadb import PersistentClient
import chromadb

# Configure logging
logger = logging.getLogger(__name__)

# Initialize ChromaDB client for vector storage
PERSIST_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "../..", "chromadb"
)
db_client = PersistentClient(path=PERSIST_DIR)

# Create or get the collection for candidate data
candidate_collection = db_client.get_or_create_collection(
    name="candidate_profiles", metadata={"hnsw:space": "cosine"}
)


def create_searchable_text(candidate_data: Dict[str, Any]) -> str:
    """Create a natural language representation of candidate data for better semantic search."""
    sections = []

    # Basic Information
    sections.append(f"Candidate Profile: {candidate_data.get('candidate_name', '')}")
    sections.append(
        f"Contact: Email - {candidate_data.get('candidate_email', '')}, Phone - {candidate_data.get('candidate_phone', '')}"
    )
    sections.append(
        f"Total Experience: {candidate_data.get('candidate__total_experience', '')}"
    )

    # Skills
    sections.append(f"Skills: {candidate_data.get('candidate_skills', '')}")

    # Professional Experience
    exp = candidate_data.get("professional_experience", {})
    if exp:
        sections.append("\nProfessional Experience:")
        sections.append(f"Company: {exp.get('company', '')}")
        sections.append(f"Role: {exp.get('role', '')}")
        sections.append(
            f"Duration: {exp.get('duration_of_job', '')} ({exp.get('start date', '')} to {exp.get('end date', '')})"
        )
        sections.append(f"Responsibilities: {exp.get('resposibilities', '')}")

        # Projects
        if "projects" in exp:
            sections.append("\nProjects:")
            for project in exp["projects"]:
                sections.append(f"- {project.get('project_name', '')}")
                sections.append(f"  Description: {project.get('description', '')}")
                sections.append(
                    f"  Technologies: {project.get('technologies_used', '')}"
                )

    # Education
    edu = candidate_data.get("education", {})
    if edu:
        sections.append("\nEducation:")
        sections.append(f"{edu.get('degree', '')} from {edu.get('institution', '')}")
        sections.append(f"Graduated: {edu.get('graduation_year', '')}")
        sections.append(
            f"Performance: {edu.get('grade', '')} ({edu.get('performance', '')})"
        )

    # Certifications
    certs = candidate_data.get("certifications", [])
    if certs:
        sections.append("\nCertifications:")
        for cert in certs:
            sections.append(
                f"- {cert.get('name', '')} from {cert.get('issuing_organization', '')} ({cert.get('issue_date', '')})"
            )

    # Languages
    if "languages" in candidate_data:
        sections.append(f"\nLanguages: {candidate_data.get('languages', '')}")

    return "\n".join(sections)


def rag_candidate_with_mem0(data: str) -> None:
    """
    Store candidate data in mem0 with RAG capabilities for future retrieval and querying.

    Args:
        data (str): Candidate data in string format
    """
    try:
        # Parse the candidate data
        candidate_data = {}
        current_section = None
        current_dict = {}

        for line in data.strip().split("\n"):
            line = line.strip()
            if not line:
                continue

            # Handle main sections
            if ":" in line and not line.startswith(" "):
                if current_section and current_dict:
                    candidate_data[current_section] = current_dict
                    current_dict = {}
                key, value = line.split(":", 1)
                if value.strip():
                    candidate_data[key.strip()] = value.strip()
                else:
                    current_section = key.strip()
                    current_dict = {}
            # Handle subsections
            elif ":" in line and line.startswith(" "):
                key, value = line.split(":", 1)
                current_dict[key.strip()] = value.strip()

        # Add last section if exists
        if current_section and current_dict:
            candidate_data[current_section] = current_dict

        # Create searchable text for RAG
        searchable_text = create_searchable_text(candidate_data)

        # Prepare metadata
        metadata = {
            "type": "candidate_profile",
            "candidate_name": candidate_data.get("candidate_name", "unknown"),
            "timestamp": datetime.now().isoformat(),
            "total_experience": candidate_data.get("candidate__total_experience", ""),
            "skills": candidate_data.get("candidate_skills", ""),
            "content_type": "both",  # Indicates this document contains both structured and searchable data
        }

        # Create a combined document that includes both structured and searchable data
        document = {
            "structured_data": json.dumps(candidate_data),
            "searchable_text": searchable_text,
        }

        # Generate a unique ID for the document
        doc_id = f"{metadata['candidate_name']}_{metadata['timestamp']}"

        # Store in ChromaDB
        candidate_collection.upsert(
            documents=[json.dumps(document)], metadatas=[metadata], ids=[doc_id]
        )

        logger.info(
            f"Successfully stored candidate data in mem0 for {candidate_data.get('candidate_name', 'unknown')}"
        )

    except Exception as e:
        logger.error(f"Error storing candidate data in mem0: {e}")
        raise


def search_candidates(query: str, limit: int = 5) -> List[Dict]:
    """
    Search for candidates based on a query string.
    Args:
        query (str): The search query
        limit (int): Maximum number of results to return
    Returns:
        List[Dict]: List of matching candidate profiles
    """
    # Search using ChromaDB's similarity search
    results = candidate_collection.query(query_texts=[query], n_results=limit)

    # Extract and parse the candidate data
    candidates = []
    if results and results["documents"]:
        for doc in results["documents"][0]:  # ChromaDB returns a nested list
            try:
                document = json.loads(doc)
                candidate_data = json.loads(document["structured_data"])
                candidates.append(candidate_data)
            except json.JSONDecodeError:
                continue

    return candidates
