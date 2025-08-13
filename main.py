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
            client = PersistentClient(path=PERSIST_DIR)

            # Get collections
            candidate_collection = client.get_collection("candidate_profiles")
            job_collection = client.get_collection("job_descriptions")

            # Get sample data
            candidates = candidate_collection.get(limit=3, include=["metadatas"])
            jobs = job_collection.get(limit=3, include=["metadatas"])

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
        # Phase 1: Process documents (resumes and jobs)
        print("🚀 Phase 1: Processing Documents...")
        results = await pipeline.process_documents(documents_path)

        # Phase 2: Perform talent matching analysis
        print("\n🚀 Phase 2: Performing Talent Matching Analysis...")
        matching_results = await pipeline.perform_talent_matching_analysis()

        # Phase 3: Perform specific matching demonstrations
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

    documents_path = {
        "resume_path": [
            "/Users/tharuntejapeddi/Projects/resume-job-matcher/src/data/resumes/Anita_Daiya.pdf",
            "/Users/tharuntejapeddi/Projects/resume-job-matcher/src/data/resumes/rohini.pdf",
        ],
        "job_desc_path": [
            "/Users/tharuntejapeddi/Projects/resume-job-matcher/src/data/job/QA_Engineer_Contract_Job_Post_NTT_SINGAPORE.pdf"
        ],
    }

    async def run_pipeline():
        print("🚀 Resume-Job Matcher Pipeline Starting...")
        await main(documents_path)
        print("✅ Pipeline completed successfully!")

    asyncio.run(run_pipeline())
