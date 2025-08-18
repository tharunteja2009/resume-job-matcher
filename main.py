#!/usr/bin/env python3
"""
Resume Job Matcher - Main Application Entry Point
This is the main entry point for the resume-job matcher application.
It orchestrates the entire pipeline using AutoGen agents with comprehensive token tracking.
"""

import sys
import os
from pathlib import Path
import asyncio
import logging
import glob

# Add the src directory to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from src.core.parsers.ResumeParser import ResumeParserAgent
from src.core.parsers.JobParser import JobParserAgent
from src.ai.engines.TalentMatchingEngine import TalentMatchingEngine
from src.ai.tracking.token_tracker import get_token_tracker

# Configure logging for ultra-clean console output
logging.basicConfig(
    level=logging.ERROR,  # Only show errors
    format="",  # No format for absolute minimum output
    handlers=[logging.StreamHandler()],
)

# Suppress all verbose logging from external libraries and internal modules
for logger_name in [
    "httpx",
    "openai",
    "autogen",
    "chromadb",
    "pymongo",
    "urllib3",
    "src.ai.tracking.token_tracker",
    "src.ai.models.tracked_model_client",
    "autogen_core.events",
    "autogen_core",
    "autogen_ext",
    "src.core.processors",
    "src.core.parsers",
    "src.ai.engines",
    "AgentMessageProcessor",
    "DocumentChunkProcessor",
    "ResumeParserAgent",
    "JobParserAgent",
    "TalentMatchingEngine",
]:
    logging.getLogger(logger_name).setLevel(logging.ERROR)

logger = logging.getLogger(__name__)


def get_all_pdf_paths(project_root: Path) -> dict:
    """
    Dynamically scan for all PDF files in resume and job directories.

    Args:
        project_root: The root directory of the project

    Returns:
        Dictionary containing lists of resume and job PDF paths
    """
    # Define the directories to scan
    resume_dir = project_root / "src" / "data" / "resumes"
    job_dir = project_root / "src" / "data" / "job"

    # Also check for resumes/ and job/ in root directory for backward compatibility
    alt_resume_dir = project_root / "resumes"
    alt_job_dir = project_root / "job"

    # Get all PDF files from resume directories
    resume_paths = []
    for directory in [resume_dir, alt_resume_dir]:
        if directory.exists():
            pdf_files = list(directory.glob("*.pdf"))
            resume_paths.extend([str(pdf) for pdf in pdf_files])

    # Get all PDF files from job directories
    job_paths = []
    for directory in [job_dir, alt_job_dir]:
        if directory.exists():
            pdf_files = list(directory.glob("*.pdf"))
            job_paths.extend([str(pdf) for pdf in pdf_files])

    # Remove duplicates while preserving order
    resume_paths = list(dict.fromkeys(resume_paths))
    job_paths = list(dict.fromkeys(job_paths))

    print(f"📁 Found {len(resume_paths)} resume PDF(s)")
    print(f"📁 Found {len(job_paths)} job description PDF(s)")

    return {"resume_path": resume_paths, "job_desc_path": job_paths}


def clean_mongodb_collections() -> bool:
    """
    Clean up existing MongoDB collections for a fresh start.

    Returns:
        True if cleanup was successful, False otherwise
    """
    try:
        print("\n🗑️  Cleaning up existing MongoDB collections...")

        import sys

        src_path = project_root / "src"
        sys.path.insert(0, str(src_path))

        from src.database.mongo.mongo_util import get_mongo_client, get_collection_names

        # Get MongoDB client and collections
        db = get_mongo_client()
        collections = get_collection_names()

        # Clean candidates collection
        candidates_collection = db[collections["candidates"]]
        candidate_count = candidates_collection.count_documents({})
        if candidate_count > 0:
            print(f"   📄 Found {candidate_count} candidates in MongoDB")
            candidates_collection.delete_many({})
            print(f"   ✅ Deleted all {candidate_count} candidates")
        else:
            print("   📄 No candidates found in MongoDB")

        # Clean jobs collection
        jobs_collection = db[collections["jobs"]]
        job_count = jobs_collection.count_documents({})
        if job_count > 0:
            print(f"   💼 Found {job_count} jobs in MongoDB")
            jobs_collection.delete_many({})
            print(f"   ✅ Deleted all {job_count} jobs")
        else:
            print("   💼 No jobs found in MongoDB")

        print("   🎯 MongoDB cleanup completed - ready for fresh start!")
        return True

    except Exception as e:
        print(f"   ❌ Error during MongoDB cleanup: {e}")
        return False


def clean_chromadb_collections() -> bool:
    """
    Clean up existing ChromaDB collections for a fresh start.

    Returns:
        True if cleanup was successful, False otherwise
    """
    try:
        print("\n🗑️  Cleaning up existing ChromaDB collections...")

        from chromadb import PersistentClient
        import os
        import shutil

        PERSIST_DIR = os.path.join(os.getcwd(), "src", "chromadb")

        # Check if ChromaDB directory exists
        if os.path.exists(PERSIST_DIR):
            print(f"   📂 Found ChromaDB directory: {PERSIST_DIR}")

            try:
                # Try to connect and delete collections properly first
                client = PersistentClient(path=PERSIST_DIR)
                collections = client.list_collections()

                if collections:
                    print(f"   📋 Found {len(collections)} existing collections:")
                    for collection in collections:
                        print(f"      • {collection.name}")
                        try:
                            client.delete_collection(collection.name)
                            print(f"      ✅ Deleted collection: {collection.name}")
                        except Exception as e:
                            print(
                                f"      ⚠️  Could not delete collection {collection.name}: {e}"
                            )
                else:
                    print("   📋 No existing collections found")

                # Also remove the entire directory for a complete clean start
                print("   🗑️  Removing ChromaDB directory for complete cleanup...")
                shutil.rmtree(PERSIST_DIR)
                print("   ✅ ChromaDB directory removed successfully")

            except Exception as e:
                print(f"   ⚠️  Could not connect to ChromaDB, removing directory: {e}")
                # If we can't connect, just remove the directory
                shutil.rmtree(PERSIST_DIR)
                print("   ✅ ChromaDB directory removed successfully")
        else:
            print("   📂 No existing ChromaDB directory found - starting fresh")

        print("   🎯 ChromaDB cleanup completed - ready for fresh start!")
        return True

    except Exception as e:
        print(f"   ❌ Error during ChromaDB cleanup: {e}")
        return False


def get_user_choice(documents_path: dict) -> str:
    """
    Prompt user to choose between parsing new files or using existing ChromaDB data.

    Args:
        documents_path: Dictionary containing available PDF paths

    Returns:
        User's choice: 'parse', 'existing', or 'clean_restart'
    """
    resume_paths = documents_path.get("resume_path", [])
    job_desc_paths = documents_path.get("job_desc_path", [])

    print("\n" + "=" * 80)
    print("🚀 RESUME-JOB MATCHER - EXECUTION OPTIONS")
    print("=" * 80)

    # Show available files
    print(f"📁 Available Files:")
    print(f"   📄 Resumes: {len(resume_paths)} PDF(s)")
    if resume_paths:
        for i, path in enumerate(resume_paths[:3], 1):  # Show first 3
            print(f"      {i}. {Path(path).name}")
        if len(resume_paths) > 3:
            print(f"      ... and {len(resume_paths) - 3} more")

    print(f"   💼 Job Descriptions: {len(job_desc_paths)} PDF(s)")
    if job_desc_paths:
        for i, path in enumerate(job_desc_paths[:3], 1):  # Show first 3
            print(f"      {i}. {Path(path).name}")
        if len(job_desc_paths) > 3:
            print(f"      ... and {len(job_desc_paths) - 3} more")

    print("\n" + "-" * 60)
    print("Choose your execution mode:")
    print("\n1️⃣  PARSE & ANALYZE (Full Pipeline)")
    print("   📝 Parse all PDF files from scratch")
    print("   💾 Store processed data in ChromaDB")
    print("   🎯 Run comprehensive talent matching analysis")

    print("\n2️⃣  DIRECT MATCHING (Use Existing Data)")
    print("   📊 Skip parsing phase entirely")
    print("   🔄 Use existing data from ChromaDB")
    print("   🎯 Run talent matching analysis directly")

    print("\n3️⃣  CLEAN & RESTART (Fresh Start)")
    print("   🗑️  Clean up existing ChromaDB & MongoDB collections")
    print("   📝 Parse all PDF files from scratch")
    print("   💾 Store processed data in both ChromaDB & MongoDB")
    print("   🎯 Run comprehensive talent matching analysis")

    print("\n" + "-" * 60)

    while True:
        try:
            choice = input("Enter your choice (1, 2, or 3): ").strip()
            if choice == "1":
                return "parse"
            elif choice == "2":
                return "existing"
            elif choice == "3":
                return "clean_restart"
            else:
                print("❌ Invalid choice. Please enter 1, 2, or 3.")
        except KeyboardInterrupt:
            print("\n\n👋 Execution cancelled by user.")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Input error: {e}. Please try again.")


class DocumentProcessingPipeline:
    """Main pipeline for processing resumes and job descriptions."""

    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        """Initialize the processing pipeline.

        Args:
            model_name: Model name to use for processing
        """
        self.resume_processor = ResumeParserAgent(model_name)
        self.job_processor = JobParserAgent(model_name)
        self.talent_matcher = TalentMatchingEngine(
            "gpt-4"
        )  # Use GPT-4 for better matching analysis
        self.logger = logging.getLogger(self.__class__.__name__)

    async def process_documents(self, documents_path: dict) -> dict:
        """Process all documents and return results with clean progress indicators.

        Args:
            documents_path: Dictionary containing resume and job paths

        Returns:
            Dictionary containing processing results
        """
        results = {"resumes": [], "jobs": [], "errors": []}

        resume_paths = documents_path.get("resume_path", [])
        job_desc_paths = documents_path.get("job_desc_path", [])

        # Process resumes with clean progress
        for i, path in enumerate(resume_paths, 1):
            try:
                print(
                    f"\n🔄 Processing Resume {i}/{len(resume_paths)}: {Path(path).name}"
                )
                print("  📝 Analyzing document with AI agents...")
                result = await self.resume_processor.process_resume(path)
                if result:
                    print(f"  ✅ Successfully processed: {Path(path).name}")
                    results["resumes"].append(
                        {"path": path, "result": result, "status": "success"}
                    )
                else:
                    print(f"  ❌ Failed to process: {Path(path).name}")
                    results["resumes"].append(
                        {"path": path, "result": None, "status": "failed"}
                    )
            except Exception as e:
                error_msg = f"Failed to process resume {Path(path).name}: {str(e)}"
                print(f"  ❌ Error: {error_msg}")
                results["errors"].append(error_msg)

        # Process job descriptions with clean progress
        for i, path in enumerate(job_desc_paths, 1):
            try:
                print(
                    f"\n🔄 Processing Job Description {i}/{len(job_desc_paths)}: {Path(path).name}"
                )
                print("  📝 Analyzing job requirements with AI agents...")
                result = await self.job_processor.process_job(path)
                if result:
                    print(f"  ✅ Successfully processed: {Path(path).name}")
                    results["jobs"].append(
                        {"path": path, "result": result, "status": "success"}
                    )
                else:
                    print(f"  ❌ Failed to process: {Path(path).name}")
                    results["jobs"].append(
                        {"path": path, "result": None, "status": "failed"}
                    )
            except Exception as e:
                error_msg = (
                    f"Failed to process job description {Path(path).name}: {str(e)}"
                )
                print(f"  ❌ Error: {error_msg}")
                results["errors"].append(error_msg)

        return results

    async def perform_talent_matching_analysis(self) -> dict:
        """
        Perform comprehensive talent matching analysis with detailed results display.

        Returns:
            Dictionary containing matching analysis results
        """
        try:
            print("\n🎯 Performing comprehensive talent matching analysis...")
            print("  📊 Comparing candidates with job requirements...")

            # Perform comprehensive analysis
            comprehensive_result = (
                await self.talent_matcher.perform_comprehensive_analysis()
            )

            if comprehensive_result:
                print("  ✅ Talent matching analysis completed successfully")

                # Display the actual analysis results
                if "analysis_result" in comprehensive_result:
                    print("\n" + "=" * 80)
                    print("🎯 DETAILED MATCHING ANALYSIS RESULTS")
                    print("=" * 80)
                    print(comprehensive_result["analysis_result"])
                    print("=" * 80)

                return {
                    "comprehensive_analysis": comprehensive_result,
                    "status": "success",
                }
            else:
                print("  ⚠️  Talent matching analysis returned no results")
                return {"status": "no_results"}

        except Exception as e:
            error_msg = f"Talent matching analysis failed: {str(e)}"
            print(f"  ❌ Error: {error_msg}")
            return {"error": error_msg, "status": "failed"}

    async def perform_specific_matching_demos(self) -> None:
        """Perform specific matching demonstrations with real data from ChromaDB."""
        try:
            print("\n🎯 SPECIFIC MATCHING DEMONSTRATIONS")
            print("=" * 60)

            # Get real data from ChromaDB instead of MongoDB
            from chromadb import PersistentClient
            import os

            PERSIST_DIR = os.path.join(os.getcwd(), "src", "chromadb")

            # Check if ChromaDB directory exists
            if not os.path.exists(PERSIST_DIR):
                print("\n⚠️  No ChromaDB directory found.")
                print(
                    "   Collections need to be created first by processing documents."
                )
                print("   Skipping specific matching demonstrations.")
                print("=" * 60)
                return

            client = PersistentClient(path=PERSIST_DIR)

            # Check if required collections exist
            try:
                existing_collections = [col.name for col in client.list_collections()]

                if "candidate_profiles" not in existing_collections:
                    print("\n⚠️  Candidate profiles collection not found.")
                    print("   Process some resumes first to create candidate data.")
                    print("   Skipping specific matching demonstrations.")
                    print("=" * 60)
                    return

                if "job_descriptions" not in existing_collections:
                    print("\n⚠️  Job descriptions collection not found.")
                    print("   Process some job descriptions first to create job data.")
                    print("   Skipping specific matching demonstrations.")
                    print("=" * 60)
                    return

                # Get collections
                candidate_collection = client.get_collection("candidate_profiles")
                job_collection = client.get_collection("job_descriptions")

                # Get sample data
                candidates = candidate_collection.get(limit=3, include=["metadatas"])
                jobs = job_collection.get(limit=3, include=["metadatas"])

            except Exception as e:
                print(f"\n⚠️  Error accessing ChromaDB collections: {e}")
                print("   The collections may not be properly initialized.")
                print("   Try running option 1 or 3 first to process documents.")
                print("   Skipping specific matching demonstrations.")
                print("=" * 60)
                return

            if candidates["metadatas"] and jobs["metadatas"]:
                # Demo 1: Job to Candidates matching
                job_metadata = jobs["metadatas"][0]
                job_title = job_metadata.get("job_title", "Sample Job")

                print(f"\n📋 Finding Best Candidates for Job: {job_title}")
                print("-" * 40)

                # Use direct function call
                from src.ai.agents.talent_matcher_agent import (
                    get_best_candidates_for_job,
                )
                import json

                # Get first job ID (use ChromaDB index as ID)
                candidates_result = get_best_candidates_for_job(
                    "0", top_k=3
                )  # ChromaDB uses index as ID
                candidates_data = json.loads(candidates_result)

                if "error" not in candidates_data:
                    print(
                        f"🎯 Top Candidates for: {candidates_data.get('job_title', 'Unknown')}"
                    )
                    for candidate in candidates_data.get("top_candidates", []):
                        print(
                            f"   {candidate['rank']}. {candidate['candidate_name']} - {candidate['similarity_score']:.1f}% match"
                        )
                        print(f"      Skills: {candidate['skills_match'][:100]}...")
                        print(f"      Experience: {candidate['experience']}")
                        print()
                else:
                    print(f"   ❌ Error: {candidates_data['error']}")

                print("-" * 60)

                # Demo 2: Candidate to Jobs matching
                candidate_metadata = candidates["metadatas"][0]
                candidate_name = candidate_metadata.get(
                    "candidate_name", "Sample Candidate"
                )

                print(f"\n👤 Finding Best Jobs for Candidate: {candidate_name}")
                print("-" * 40)

                from src.ai.agents.talent_matcher_agent import (
                    get_best_jobs_for_candidate,
                )

                # Get first candidate ID (use ChromaDB index as ID)
                jobs_result = get_best_jobs_for_candidate(
                    "0", top_k=3
                )  # ChromaDB uses index as ID
                jobs_data = json.loads(jobs_result)

                if "error" not in jobs_data:
                    print(
                        f"🎯 Top Jobs for: {jobs_data.get('candidate_name', 'Unknown')}"
                    )
                    print(f"   Skills: {jobs_data.get('candidate_skills', 'N/A')}")
                    print(
                        f"   Experience: {jobs_data.get('candidate_experience', 'N/A')}"
                    )
                    print()
                    for job in jobs_data.get("top_jobs", []):
                        print(
                            f"   {job['rank']}. {job['job_title']} at {job['company']} - {job['similarity_score']:.1f}% match"
                        )
                        print(f"      Location: {job['location']}")
                        print(f"      Required: {job['required_skills'][:100]}...")
                        print()
                else:
                    print(f"   ❌ Error: {jobs_data['error']}")

            else:
                print(
                    "\n⚠️  No sufficient data available in ChromaDB for matching demonstrations"
                )
                print(
                    f"   Candidates: {len(candidates['metadatas']) if candidates['metadatas'] else 0}"
                )
                print(f"   Jobs: {len(jobs['metadatas']) if jobs['metadatas'] else 0}")

            print("=" * 60)

        except Exception as e:
            print(f"\n❌ Error in specific matching demos: {str(e)}")
            import traceback

            traceback.print_exc()
            # Continue without failing the entire pipeline

    async def find_best_candidates_for_job(self, job_id: str, top_k: int = 5) -> dict:
        """
        Find the best candidates for a specific job.

        Args:
            job_id: The job identifier to find candidates for
            top_k: Number of top candidates to return

        Returns:
            Dictionary containing ranked candidates
        """
        try:
            self.logger.info(f"Finding best candidates for job: {job_id}")
            result = await self.talent_matcher.find_candidates_for_job(job_id, top_k)
            return {
                "matching_result": result,
                "status": "success" if result else "failed",
            }
        except Exception as e:
            error_msg = f"Failed to find candidates for job {job_id}: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg, "status": "failed"}

    async def find_best_jobs_for_candidate(
        self, candidate_id: str, top_k: int = 5
    ) -> dict:
        """
        Find the best jobs for a specific candidate.

        Args:
            candidate_id: The candidate identifier to find jobs for
            top_k: Number of top jobs to return

        Returns:
            Dictionary containing ranked jobs
        """
        try:
            self.logger.info(f"Finding best jobs for candidate: {candidate_id}")
            result = await self.talent_matcher.find_jobs_for_candidate(
                candidate_id, top_k
            )
            return {
                "matching_result": result,
                "status": "success" if result else "failed",
            }
        except Exception as e:
            error_msg = f"Failed to find jobs for candidate {candidate_id}: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg, "status": "failed"}

    def print_summary(self, results: dict, matching_results: dict = None) -> None:
        """Print a simplified processing summary."""
        print("\n📊 Processing Summary:")

        resume_count = len(results["resumes"])
        job_count = len(results["jobs"])
        error_count = len(results["errors"])

        print(f"📄 Resumes Processed: {resume_count}")
        resume_success = sum(1 for r in results["resumes"] if r["status"] == "success")
        print(f"   ✅ Successful: {resume_success}")
        print(f"   ❌ Failed: {resume_count - resume_success}")

        print(f"\n💼 Job Descriptions Processed: {job_count}")
        job_success = sum(1 for j in results["jobs"] if j["status"] == "success")
        print(f"   ✅ Successful: {job_success}")
        print(f"   ❌ Failed: {job_count - job_success}")

        if matching_results:
            print(f"\n🎯 TALENT MATCHING ANALYSIS")
            print("-" * 40)
            if matching_results.get("status") == "success":
                print("✅ Comprehensive matching analysis completed")
            else:
                print("❌ Matching analysis failed")
                if "error" in matching_results:
                    print(f"   Error: {matching_results['error']}")

        if error_count > 0:
            print(f"\n⚠️ Errors Encountered: {error_count}")
            for error in results["errors"]:
                print(f"   • {error}")

        print("=" * 80)

        # Print token usage and cost analysis
        token_tracker = get_token_tracker()
        token_tracker.print_session_summary()


async def main(documents_path: dict) -> None:
    """Main entry point with clean user experience and detailed matching results."""
    pipeline = DocumentProcessingPipeline()

    try:
        # Get user's choice
        user_choice = get_user_choice(documents_path)

        print("\n" + "=" * 80)

        if user_choice == "parse":
            # Full pipeline: Parse documents and then perform matching
            resume_paths = documents_path.get("resume_path", [])
            job_desc_paths = documents_path.get("job_desc_path", [])

            if len(resume_paths) == 0 and len(job_desc_paths) == 0:
                print("❌ No PDF files found to process!")
                print(
                    "   Please add PDF files to the resume or job directories and try again."
                )
                return

            print("🚀 FULL PIPELINE MODE - Parse & Analyze")
            print("=" * 80)

            # Phase 1: Process documents (resumes and jobs)
            print("🚀 Phase 1: Processing Documents...")
            results = await pipeline.process_documents(documents_path)

            # Phase 2: Perform talent matching analysis
            print("\n🚀 Phase 2: Performing Talent Matching Analysis...")
            matching_results = await pipeline.perform_talent_matching_analysis()

        elif user_choice == "clean_restart":
            # Clean ChromaDB and then do full pipeline
            resume_paths = documents_path.get("resume_path", [])
            job_desc_paths = documents_path.get("job_desc_path", [])

            if len(resume_paths) == 0 and len(job_desc_paths) == 0:
                print("❌ No PDF files found to process!")
                print(
                    "   Please add PDF files to the resume or job directories and try again."
                )
                return

            print("🚀 CLEAN & RESTART MODE - Fresh Start")
            print("=" * 80)

            # Step 1: Clean up both databases
            chromadb_cleanup_success = clean_chromadb_collections()
            mongodb_cleanup_success = clean_mongodb_collections()

            if not chromadb_cleanup_success:
                print("❌ ChromaDB cleanup failed. Continuing anyway...")
            if not mongodb_cleanup_success:
                print("❌ MongoDB cleanup failed. Continuing anyway...")

            # Step 2: Process documents (resumes and jobs)
            print("\n🚀 Phase 1: Processing Documents...")
            results = await pipeline.process_documents(documents_path)

            # Step 3: Perform talent matching analysis
            print("\n🚀 Phase 2: Performing Talent Matching Analysis...")
            matching_results = await pipeline.perform_talent_matching_analysis()

        else:  # user_choice == "existing"
            # Direct matching using existing ChromaDB data
            print("🚀 DIRECT MATCHING MODE - Using Existing Data")
            print("=" * 80)
            print("📊 Skipping document parsing phase...")
            print("🔄 Using existing data from ChromaDB...")

            # Skip processing, go directly to matching
            results = {"resumes": [], "jobs": [], "errors": []}

            # Phase 2: Perform talent matching analysis with existing data
            print("\n🚀 Phase 2: Performing Talent Matching Analysis...")
            matching_results = await pipeline.perform_talent_matching_analysis()

        # Phase 3: Perform specific matching demonstrations (for all modes)
        print("\n🚀 Phase 3: Specific Matching Demonstrations...")
        await pipeline.perform_specific_matching_demos()

        # Print comprehensive summary
        pipeline.print_summary(results, matching_results)

    except Exception as e:
        print(f"❌ Pipeline execution failed: {e}")
        raise


async def demo_specific_matching():
    """Demo specific matching scenarios."""
    pipeline = DocumentProcessingPipeline()

    print("\n" + "=" * 80)
    print("🎯 SPECIFIC MATCHING DEMONSTRATIONS")
    print("=" * 80)

    try:
        # Demo 1: Find candidates for a specific job
        # Note: Replace 'sample_job_id' with an actual job ID from your MongoDB
        print("\n📋 Demo 1: Finding candidates for a specific job...")
        job_matching_result = await pipeline.find_best_candidates_for_job(
            "sample_job_id", top_k=3
        )
        if job_matching_result.get("status") == "success":
            print("✅ Job-to-candidates matching completed")
        else:
            print("⚠️ Job-to-candidates matching demo skipped (no valid job ID)")

        # Demo 2: Find jobs for a specific candidate
        # Note: Replace 'sample_candidate_id' with an actual candidate ID from your MongoDB
        print("\n👤 Demo 2: Finding jobs for a specific candidate...")
        candidate_matching_result = await pipeline.find_best_jobs_for_candidate(
            "sample_candidate_id", top_k=3
        )
        if candidate_matching_result.get("status") == "success":
            print("✅ Candidate-to-jobs matching completed")
        else:
            print("⚠️ Candidate-to-jobs matching demo skipped (no valid candidate ID)")

        print(
            "\n💡 Note: To use specific matching, replace 'sample_job_id' and 'sample_candidate_id'"
        )
        print("   with actual IDs from your MongoDB database.")

    except Exception as e:
        logger.error(f"Matching demonstration failed: {e}")

    print("=" * 80)


if __name__ == "__main__":
    # Set environment variables for cleaner output
    os.environ["AUTOGEN_LOGGING"] = "ERROR"

    # Dynamically get all PDF files from resume and job directories
    documents_path = get_all_pdf_paths(project_root)

    async def run_pipeline():
        print("🚀 Resume-Job Matcher Pipeline Starting...")
        await main(documents_path)
        print("✅ Pipeline completed successfully!")

    asyncio.run(run_pipeline())
