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

# Create or get the collection for job data
job_collection = db_client.get_or_create_collection(
    name="job_descriptions", metadata={"hnsw:space": "cosine"}
)


def create_searchable_text(job_data: Dict[str, Any]) -> str:
    """Create a natural language representation of job data for better semantic search."""
    sections = []

    # Basic Job Information
    sections.append(f"Job Title: {job_data.get('job_title', '')}")
    sections.append(f"Company: {job_data.get('company_name', '')}")
    sections.append(f"Location: {job_data.get('location', '')}")
    sections.append(f"Employment Type: {job_data.get('employment_type', '')}")

    # Required Experience and Skills
    sections.append(f"\nRequired Experience: {job_data.get('required_experience', '')}")
    sections.append(
        f"Required Skills: {', '.join(job_data.get('required_skills', []))}"
    )

    # Nice to Have Skills
    if job_data.get("preferred_skills"):
        sections.append(
            f"Preferred Skills: {', '.join(job_data.get('preferred_skills', []))}"
        )

    # Job Description and Responsibilities
    if job_data.get("responsibilities"):
        sections.append("\nKey Responsibilities:")
        for resp in job_data.get("responsibilities", []):
            sections.append(f"- {resp}")

    # Requirements
    if job_data.get("requirements"):
        sections.append("\nRequirements:")
        for req in job_data.get("requirements", []):
            sections.append(f"- {req}")

    # Qualifications
    if job_data.get("qualifications"):
        sections.append("\nQualifications:")
        for qual in job_data.get("qualifications", []):
            sections.append(f"- {qual}")

    # Additional Information
    if job_data.get("additional_info"):
        sections.append("\nAdditional Information:")
        sections.append(job_data.get("additional_info", ""))

    # Benefits
    if job_data.get("benefits"):
        sections.append("\nBenefits:")
        for benefit in job_data.get("benefits", []):
            sections.append(f"- {benefit}")

    return "\n".join(sections)


def store_job_in_chromadb(data: str) -> None:
    """
    Store job data in ChromaDB with RAG capabilities for future retrieval and querying.

    Args:
        data (str): Job description data in string format
    """
    try:
        # Parse the job data
        job_data = {}
        current_section = None
        current_list = []

        for line in data.strip().split("\n"):
            line = line.strip()
            if not line:
                continue

            # Handle main sections (usually in title case or uppercase)
            if line.isupper() or line.istitle() and not line.startswith("-"):
                if current_section and current_list:
                    job_data[current_section] = current_list
                    current_list = []
                current_section = line.lower().replace(" ", "_")
                continue

            # Handle list items and content
            if current_section:
                if line.startswith("-"):
                    current_list.append(line[1:].strip())
                else:
                    if not current_list:
                        job_data[current_section] = line
                    else:
                        current_list.append(line)

        # Add last section if exists
        if current_section and current_list:
            job_data[current_section] = current_list

        # Create searchable text for RAG
        searchable_text = create_searchable_text(job_data)

        # Prepare metadata
        # Convert lists to strings and ensure all metadata values are of accepted types
        skills = job_data.get("required_skills", [])
        if isinstance(skills, list):
            skills = ", ".join(skills)
        elif not isinstance(skills, str):
            skills = str(skills)

        metadata = {
            "type": "job_description",
            "job_title": str(job_data.get("job_title", "unknown")),
            "company": str(job_data.get("company_name", "unknown")),
            "timestamp": datetime.now().isoformat(),
            "required_skills": skills,
            "content_type": "both",
            "experience_level": str(
                job_data.get("required_experience", "not specified")
            ),
            "location": str(job_data.get("location", "not specified")),
        }  # Create three focused chunks for better matching
        skills_chunk = f"Position: {metadata['job_title']} | Skills Required: {metadata['required_skills']} | Experience: {metadata['experience_level']}"

        context_chunk = searchable_text  # Keep the full searchable text as context

        # Create a sanitized document ID (remove special characters and spaces)
        base_id = f"{metadata['job_title']}_{metadata['company']}".lower()
        base_id = "".join(c if c.isalnum() else "_" for c in base_id)
        timestamp = metadata["timestamp"].replace(":", "-")
        doc_id = f"{base_id}_{timestamp}"

        # Store data in a way that's compatible with ChromaDB
        document = {
            "skills_focus": skills_chunk,
            "full_context": context_chunk,
            "metadata": json.dumps(metadata),  # Store metadata as a JSON string
        }

        try:
            # Store in ChromaDB with proper error handling
            job_collection.upsert(
                documents=[json.dumps(document)],
                metadatas=[
                    {
                        "type": metadata["type"],
                        "job_title": metadata["job_title"],
                        "company": metadata["company"],
                        "timestamp": metadata["timestamp"],
                        "skills": metadata["required_skills"],
                        "experience": metadata["experience_level"],
                        "location": metadata["location"],
                    }
                ],
                ids=[doc_id],
            )
            logger.info(
                f"Successfully stored job data for {metadata['job_title']} at {metadata['company']}"
            )

        except Exception as e:
            logger.error(f"Error storing job data in ChromaDB: {str(e)}")
            raise

        logger.info(
            f"Successfully stored job data in ChromaDB for {job_data.get('job_title', 'unknown')} at {job_data.get('company_name', 'unknown')}"
        )

    except Exception as e:
        logger.error(f"Error storing job data in ChromaDB: {e}")
        raise


def search_jobs(query: str, limit: int = 5) -> List[Dict]:
    """
    Search for jobs based on a query string.
    Args:
        query (str): The search query
        limit (int): Maximum number of results to return
    Returns:
        List[Dict]: List of matching job descriptions
    """
    # Search using ChromaDB's similarity search
    results = job_collection.query(query_texts=[query], n_results=limit)

    # Extract and parse the job data
    jobs = []
    if results and results["documents"]:
        for doc in results["documents"][0]:  # ChromaDB returns a nested list
            try:
                document = json.loads(doc)
                job_data = json.loads(document["structured_data"])
                jobs.append(job_data)
            except json.JSONDecodeError:
                continue

    return jobs


def match_jobs_to_candidate(
    candidate_skills: List[str], experience_years: str, limit: int = 5
) -> List[Dict]:
    """
    Find matching jobs for a candidate based on their skills and experience.
    Args:
        candidate_skills: List of candidate's skills
        experience_years: Candidate's years of experience (e.g., "5 years")
        limit: Maximum number of jobs to return
    Returns:
        List[Dict]: List of matching jobs with similarity scores
    """
    # Create a query combining skills and experience
    skills_query = ", ".join(candidate_skills)
    query = f"Required skills include {skills_query} with approximately {experience_years} of experience"

    # Get matching jobs
    results = job_collection.query(
        query_texts=[query],
        n_results=limit,
        include=["metadatas", "documents", "distances"],
    )

    # Process and score matches
    matches = []
    if results and results["documents"]:
        for doc, metadata, distance in zip(
            results["documents"][0], results["metadatas"][0], results["distances"][0]
        ):
            try:
                document = json.loads(doc)
                job_data = json.loads(document["structured_data"])

                # Calculate match score (convert distance to similarity score)
                similarity_score = 1 - distance

                # Add score to job data
                job_data["match_score"] = round(similarity_score * 100, 2)
                matches.append(job_data)

            except json.JSONDecodeError:
                continue

    # Sort by match score
    matches.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    return matches
