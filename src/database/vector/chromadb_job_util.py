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

    # Extract job information with multiple fallback options
    job_title = (
        job_data.get("job_title")
        or job_data.get("Job Title")
        or job_data.get("title")
        or ""
    )

    company_name = (
        job_data.get("company_name")
        or job_data.get("Company")
        or job_data.get("company")
        or ""
    )

    location = job_data.get("location") or job_data.get("Location") or ""

    employment_type = (
        job_data.get("employment_type") or job_data.get("Employment Type") or ""
    )

    # Basic Job Information
    if job_title:
        sections.append(f"Job Title: {job_title}")
    if company_name:
        sections.append(f"Company: {company_name}")
    if location:
        sections.append(f"Location: {location}")
    if employment_type:
        sections.append(f"Employment Type: {employment_type}")

    # Required Experience and Skills
    required_experience = (
        job_data.get("required_experience")
        or job_data.get("Required Experience")
        or job_data.get("experience")
        or ""
    )
    if required_experience:
        sections.append(f"\nRequired Experience: {required_experience}")

    # Handle skills - can be list or string
    required_skills = job_data.get("required_skills") or job_data.get("skills", [])
    if isinstance(required_skills, list) and required_skills:
        sections.append(f"Required Skills: {', '.join(required_skills)}")
    elif isinstance(required_skills, str) and required_skills:
        sections.append(f"Required Skills: {required_skills}")

    # Nice to Have Skills
    preferred_skills = job_data.get("preferred_skills", [])
    if isinstance(preferred_skills, list) and preferred_skills:
        sections.append(f"Preferred Skills: {', '.join(preferred_skills)}")
    elif isinstance(preferred_skills, str) and preferred_skills:
        sections.append(f"Preferred Skills: {preferred_skills}")

    # Job Description and Responsibilities
    responsibilities = job_data.get("responsibilities", [])
    if responsibilities:
        sections.append("\nKey Responsibilities:")
        if isinstance(responsibilities, list):
            for resp in responsibilities[:3]:  # Limit to first 3
                sections.append(f"- {resp}")
        elif isinstance(responsibilities, str):
            sections.append(f"- {responsibilities}")

    # Requirements
    requirements = job_data.get("requirements", [])
    if requirements:
        sections.append("\nRequirements:")
        if isinstance(requirements, list):
            for req in requirements[:3]:  # Limit to first 3
                sections.append(f"- {req}")
        elif isinstance(requirements, str):
            sections.append(f"- {requirements}")

    # Additional Information
    additional_info = job_data.get("additional_info") or job_data.get("description")
    if additional_info and isinstance(additional_info, str):
        sections.append("\nAdditional Information:")
        sections.append(additional_info[:200])  # Limit length

    return "\n".join(filter(None, sections))  # Filter out empty sections


def extract_from_natural_language_job(text: str) -> Dict[str, Any]:
    """Extract structured job data from natural language summary text."""
    import re

    job_data = {}

    # Extract job title - look for "Position:" or similar
    title_match = re.search(r"Position:\s*([^|\n]+)", text, re.IGNORECASE)
    if not title_match:
        title_match = re.search(
            r"(?:Job\s+Title|Title|Role):\s*([^\n|]+)", text, re.IGNORECASE
        )
    if title_match:
        job_data["job_title"] = title_match.group(1).strip()

    # Extract company
    company_match = re.search(r"Company:\s*([^\n|]+)", text, re.IGNORECASE)
    if company_match:
        job_data["company"] = company_match.group(1).strip()

    # Extract location
    location_match = re.search(r"Location:\s*([^\n|]+)", text, re.IGNORECASE)
    if location_match:
        job_data["location"] = location_match.group(1).strip()

    # Extract required skills - look for various patterns
    skills_match = re.search(r"(?:Required|Skills?):\s*([^\n|]+)", text, re.IGNORECASE)
    if not skills_match:
        skills_match = re.search(r"Stack:\s*([^\n|]+)", text, re.IGNORECASE)
    if skills_match:
        skills_text = skills_match.group(1)
        # Split by comma and clean up
        skills = [skill.strip() for skill in skills_text.split(",")]
        job_data["required_skills"] = skills

    # Extract experience requirements
    exp_match = re.search(r"Experience:\s*([^\n|]+)", text, re.IGNORECASE)
    if not exp_match:
        exp_match = re.search(r"(\d+)\+?\s*(?:years?|yrs?)", text, re.IGNORECASE)
        if exp_match:
            job_data["required_experience"] = f"{exp_match.group(1)}+ years"
    else:
        job_data["required_experience"] = exp_match.group(1).strip()

    # Extract responsibilities
    resp_match = re.search(
        r"(?:Primary|Responsibilities?):\s*([^\n|]+)", text, re.IGNORECASE
    )
    if resp_match:
        job_data["responsibilities"] = [resp_match.group(1).strip()]

    return job_data


def store_job_in_chromadb(data: str) -> None:
    """
    Store job data in ChromaDB with RAG capabilities for future retrieval and querying.

    Args:
        data (str): Job description data in string format (can be JSON, structured text, or natural language summary)
    """
    try:
        # Try to parse as JSON first (from job parsing agent)
        job_data = {}
        try:
            # Attempt JSON parsing
            job_data = json.loads(data)
            logger.info(
                f"Successfully parsed JSON data for job: {job_data.get('job_title', 'unknown')}"
            )
        except json.JSONDecodeError:
            # Try to extract from natural language summary (from RAG builder agent)
            logger.info("JSON parsing failed, attempting natural language extraction")
            job_data = extract_from_natural_language_job(data)

            # If natural language extraction failed, fall back to manual parsing
            if not job_data.get("job_title"):
                logger.info(
                    "Natural language extraction failed, attempting manual parsing of structured text"
                )
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

        # Create searchable text for RAG (use original data if it's already natural language)
        if isinstance(job_data, dict) and job_data.get("job_title"):
            searchable_text = create_searchable_text(job_data)
        else:
            # If we couldn't extract structured data, use the original text as searchable
            searchable_text = data

        # Extract job information with multiple fallback options
        job_title = (
            job_data.get("job_title")
            or job_data.get("Job Title")
            or job_data.get("title")
            or "unknown"
        )

        company_name = (
            job_data.get("company_name")
            or job_data.get("Company")
            or job_data.get("company")
            or "unknown"
        )

        location = (
            job_data.get("location") or job_data.get("Location") or "not specified"
        )

        required_experience = (
            job_data.get("required_experience")
            or job_data.get("Required Experience")
            or job_data.get("experience")
            or "not specified"
        )

        # Handle skills - can be list or string
        skills = job_data.get("required_skills", [])
        if not skills:
            skills = job_data.get("skills", [])
        if isinstance(skills, list):
            skills_str = ", ".join(skills)
        else:
            skills_str = str(skills) if skills else ""

        # 🔍 Check for duplicates before insertion
        print(f"🔍 Checking for existing job: {job_title} at {company_name}")
        try:
            existing_jobs = job_collection.get(
                where={"$and": [{"job_title": job_title}, {"company": company_name}]},
                include=["metadatas"],
            )

            if existing_jobs["ids"] and len(existing_jobs["ids"]) > 0:
                print(
                    f"⚠️  Job '{job_title}' at '{company_name}' already exists in ChromaDB (ID: {existing_jobs['ids'][0]}) - Skipping insertion"
                )
                logger.info(f"Skipping duplicate job: {job_title} at {company_name}")
                return
        except Exception as e:
            print(f"⚠️  Error checking for duplicates: {e} - Proceeding with insertion")

        # Prepare metadata
        metadata = {
            "type": "job_description",
            "job_title": job_title,
            "company": company_name,
            "timestamp": datetime.now().isoformat(),
            "skills": skills_str,
            "experience": required_experience,
            "location": location,
        }

        # Create focused chunks for better matching
        skills_chunk = f"Position: {job_title} | Skills Required: {skills_str} | Experience: {required_experience}"
        context_chunk = searchable_text  # Keep the full searchable text as context

        # Create a sanitized document ID (remove special characters and spaces)
        base_id = f"{job_title}_{company_name}".lower()
        base_id = "".join(c if c.isalnum() else "_" for c in base_id)
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        doc_id = f"{base_id}_{timestamp_str}"

        # Store data in a way that's compatible with ChromaDB
        document = {
            "skills_focus": skills_chunk,
            "full_context": context_chunk,
            "structured_data": json.dumps(job_data),  # Store original data
            "original_data": data,  # Keep original for debugging
        }

        try:
            # Store in ChromaDB with proper error handling
            job_collection.upsert(
                documents=[json.dumps(document)],
                metadatas=[metadata],
                ids=[doc_id],
            )
            logger.info(
                f"Successfully stored job data for {job_title} at {company_name}"
            )

        except Exception as e:
            logger.error(f"Error storing job data in ChromaDB: {str(e)}")
            raise

    except Exception as e:
        logger.error(f"Error storing job data in ChromaDB: {e}")
        # Store as raw text if all else fails
        try:
            metadata = {
                "type": "job_description",
                "job_title": "unknown",
                "company": "unknown",
                "timestamp": datetime.now().isoformat(),
                "skills": "",
                "experience": "not specified",
                "location": "not specified",
            }
            document = {"raw_text": data}
            doc_id = f"unknown_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            job_collection.upsert(
                documents=[json.dumps(document)], metadatas=[metadata], ids=[doc_id]
            )
            logger.warning(f"Stored job data as raw text due to parsing errors")
        except Exception as final_error:
            logger.error(f"Final fallback also failed: {final_error}")
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
