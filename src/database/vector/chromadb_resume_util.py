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
    """Create a concise, searchable representation of candidate data."""
    sections = []

    # Extract name with multiple fallback options
    candidate_name = (
        candidate_data.get("candidate_name")
        or candidate_data.get("Full Name")
        or candidate_data.get("name")
        or "Unknown"
    )

    # Extract experience with multiple fallback options
    total_experience = (
        candidate_data.get("candidate_total_experience")
        or candidate_data.get("Total Years of Experience")
        or candidate_data.get("total_experience")
        or ""
    )

    # Basic Information - Keep it minimal
    sections.append(f"{candidate_name} - {total_experience} Experience")

    # Contact info
    email = (
        candidate_data.get("candidate_email")
        or candidate_data.get("Email")
        or candidate_data.get("email")
        or ""
    )
    if email:
        sections.append(f"Contact: {email}")

    # Skills with multiple fallback options
    skills = candidate_data.get("candidate_skills", "")
    if not skills:
        skills = candidate_data.get("skills", "")
    if isinstance(skills, list):
        skills = ", ".join(skills)
    if skills:
        sections.append(f"Skills: {skills}")

    # Professional Experience
    exp = candidate_data.get("professional_experience")
    if exp:
        if isinstance(exp, list) and exp:
            exp = exp[0]  # Take the first experience
        if isinstance(exp, dict):
            sections.append("\nProfessional Experience:")
            if exp.get("company"):
                sections.append(f"Company: {exp.get('company', '')}")
            if exp.get("role"):
                sections.append(f"Role: {exp.get('role', '')}")
            if exp.get("duration_of_job"):
                sections.append(f"Duration: {exp.get('duration_of_job', '')}")
            if exp.get("start_date") or exp.get("end_date"):
                sections.append(
                    f"Period: {exp.get('start_date', '')} to {exp.get('end_date', '')}"
                )
            if exp.get("responsibilities"):
                sections.append(f"Responsibilities: {exp.get('responsibilities', '')}")

            # Projects
            projects = exp.get("projects", [])
            if projects and isinstance(projects, list):
                sections.append("\nProjects:")
                for project in projects[:2]:  # Limit to 2 projects
                    if isinstance(project, dict):
                        if project.get("project_name"):
                            sections.append(f"- {project.get('project_name', '')}")
                        if project.get("description"):
                            sections.append(
                                f"  Description: {project.get('description', '')}"
                            )
                        if project.get("technologies_used"):
                            sections.append(
                                f"  Technologies: {project.get('technologies_used', '')}"
                            )

    # Education
    edu = candidate_data.get("education")
    if edu and isinstance(edu, dict):
        sections.append("\nEducation:")
        degree = edu.get("degree", "")
        institution = edu.get("institution", "")
        if degree or institution:
            sections.append(f"{degree} from {institution}")
        if edu.get("graduation_year"):
            sections.append(f"Graduated: {edu.get('graduation_year', '')}")

    # Languages
    languages = candidate_data.get("languages", "")
    if isinstance(languages, list):
        languages = ", ".join(languages)
    if languages:
        sections.append(f"\nLanguages: {languages}")

    return "\n".join(filter(None, sections))  # Filter out empty sections


def extract_from_natural_language(text: str) -> Dict[str, Any]:
    """Extract structured data from natural language summary text."""
    candidate_data = {}

    # Extract name (usually at the beginning)
    lines = text.strip().split("\n")
    first_line = lines[0] if lines else ""

    # Try to extract name from first line - it's often "Name - Experience" or just "Name"
    if " - " in first_line:
        name_part = first_line.split(" - ")[0].strip()
        if name_part and not name_part.lower().startswith(
            ("contact", "email", "phone", "skills")
        ):
            candidate_data["candidate_name"] = name_part
    elif first_line and not first_line.lower().startswith(
        ("contact", "email", "phone", "skills")
    ):
        # If first line seems like a name (contains capital letters, no colons)
        if ":" not in first_line and any(c.isupper() for c in first_line):
            candidate_data["candidate_name"] = first_line.strip()

    # Extract email
    import re

    email_match = re.search(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text
    )
    if email_match:
        candidate_data["candidate_email"] = email_match.group()

    # Extract phone
    phone_match = re.search(r"[+]?[\d\s\-()]{10,}", text)
    if phone_match:
        candidate_data["candidate_phone"] = phone_match.group().strip()

    # Extract experience years
    exp_match = re.search(
        r"(\d+)\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience)?", text, re.IGNORECASE
    )
    if exp_match:
        candidate_data["total_experience"] = f"{exp_match.group(1)} years"

    # Extract skills (look for "Skills:" section)
    skills_match = re.search(r"Skills:\s*([^\n]+)", text, re.IGNORECASE)
    if skills_match:
        skills_text = skills_match.group(1)
        # Split by comma and clean up
        skills = [skill.strip() for skill in skills_text.split(",")]
        candidate_data["skills"] = skills

    # Extract company/role information
    companies = re.findall(
        r"(?:Company|worked?\s+(?:at|for)):\s*([^\n]+)", text, re.IGNORECASE
    )
    roles = re.findall(r"(?:Role|Position|Title):\s*([^\n]+)", text, re.IGNORECASE)

    if companies or roles:
        exp_info = {}
        if companies:
            exp_info["company"] = companies[0].strip()
        if roles:
            exp_info["role"] = roles[0].strip()
        candidate_data["professional_experience"] = exp_info

    return candidate_data


def store_candidate_in_chromadb(data: str) -> None:
    """
    Store candidate data in ChromaDB with RAG capabilities for future retrieval and querying.

    Args:
        data (str): Candidate data in string format (can be JSON, structured text, or natural language summary)
    """
    try:
        # Try to parse as JSON first (from resume parsing agent)
        candidate_data = {}
        try:
            # Attempt JSON parsing
            candidate_data = json.loads(data)
            logger.info(
                f"Successfully parsed JSON data for candidate: {candidate_data.get('candidate_name', 'unknown')}"
            )
        except json.JSONDecodeError:
            # Try to extract from natural language summary (from RAG builder agent)
            logger.info("JSON parsing failed, attempting natural language extraction")
            candidate_data = extract_from_natural_language(data)

            # If natural language extraction failed, fall back to manual parsing
            if not candidate_data.get("candidate_name"):
                logger.info(
                    "Natural language extraction failed, attempting manual parsing of structured text"
                )
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

        # Create searchable text for RAG (use original data if it's already natural language)
        if isinstance(candidate_data, dict) and candidate_data.get("candidate_name"):
            searchable_text = create_searchable_text(candidate_data)
        else:
            # If we couldn't extract structured data, use the original text as searchable
            searchable_text = data

        # Extract proper candidate information with fallbacks
        candidate_name = (
            candidate_data.get("candidate_name")
            or candidate_data.get("Full Name")
            or candidate_data.get("name")
            or "unknown"
        )

        total_experience = (
            candidate_data.get("candidate_total_experience")
            or candidate_data.get("Total Years of Experience")
            or candidate_data.get("total_experience")
            or ""
        )

        skills = candidate_data.get("candidate_skills", "")
        if not skills:
            skills = candidate_data.get("skills", "")
        if isinstance(skills, list):
            skills = ", ".join(skills)

        # Prepare metadata
        metadata = {
            "type": "candidate_profile",
            "candidate_name": candidate_name,
            "timestamp": datetime.now().isoformat(),
            "total_experience": total_experience,
            "skills": skills,
            "content_type": "both",  # Indicates this document contains both structured and searchable data
        }

        # Create a combined document that includes both structured and searchable data
        document = {
            "structured_data": json.dumps(candidate_data),
            "searchable_text": searchable_text,
            "original_data": data,  # Keep original for debugging
        }

        # Generate a unique ID for the document
        doc_id = f"{candidate_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Store in ChromaDB
        candidate_collection.upsert(
            documents=[json.dumps(document)], metadatas=[metadata], ids=[doc_id]
        )

        logger.info(
            f"Successfully stored candidate data in ChromaDB for {candidate_name}"
        )

    except Exception as e:
        logger.error(f"Error storing candidate data in ChromaDB: {e}")
        # Store as raw text if all else fails
        try:
            metadata = {
                "type": "candidate_profile",
                "candidate_name": "unknown",
                "timestamp": datetime.now().isoformat(),
                "total_experience": "",
                "skills": "",
                "content_type": "raw",
            }
            document = {"raw_text": data}
            doc_id = f"unknown_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            candidate_collection.upsert(
                documents=[json.dumps(document)], metadatas=[metadata], ids=[doc_id]
            )
            logger.warning(f"Stored candidate data as raw text due to parsing errors")
        except Exception as final_error:
            logger.error(f"Final fallback also failed: {final_error}")
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


def match_candidates_to_job(
    required_skills: List[str], required_experience: str, limit: int = 5
) -> List[Dict]:
    """
    Find matching candidates for a job based on required skills and experience.
    Args:
        required_skills: List of skills required for the job
        required_experience: Required years of experience (e.g., "5 years")
        limit: Maximum number of candidates to return
    Returns:
        List[Dict]: List of matching candidates with similarity scores
    """
    # Create a query combining required skills and experience
    skills_query = ", ".join(required_skills)
    query = f"Looking for candidates with skills in {skills_query} and around {required_experience} of experience"

    # Get matching candidates
    results = candidate_collection.query(
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
                candidate_data = json.loads(document["structured_data"])

                # Calculate match score (convert distance to similarity score)
                similarity_score = 1 - distance

                # Calculate skill match percentage
                candidate_skills = set(
                    candidate_data.get("candidate_skills", "").lower().split(", ")
                )
                required_skills_set = set(skill.lower() for skill in required_skills)
                matching_skills = candidate_skills.intersection(required_skills_set)
                skill_match_percentage = (
                    len(matching_skills) / len(required_skills_set) * 100
                    if required_skills_set
                    else 0
                )

                # Combine semantic similarity with skill match for final score
                final_score = similarity_score * 0.6 + skill_match_percentage * 0.4

                # Add scores to candidate data
                candidate_data["match_score"] = round(final_score, 2)
                candidate_data["skill_match_percentage"] = round(
                    skill_match_percentage, 2
                )
                candidate_data["matching_skills"] = list(matching_skills)
                candidate_data["missing_skills"] = list(
                    required_skills_set - candidate_skills
                )

                matches.append(candidate_data)

            except json.JSONDecodeError:
                continue

    # Sort by match score
    matches.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    return matches
