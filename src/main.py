import asyncio
import logging
from src.core.parsers.ResumeParser import ResumeParserAgent
from src.core.parsers.JobParser import JobParserAgent
from src.ai.engines.TalentMatchingEngine import TalentMatchingEngine
from src.ai.tracking.token_tracker import get_token_tracker

# Configure logging for better readability
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

# Control autogen logging
for logger_name in ["autogen_core.events", "autogen_core"]:
    logging.getLogger(logger_name).setLevel(logging.WARNING)

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
        """Process all documents and return results.

        Args:
            documents_path: Dictionary containing resume and job paths

        Returns:
            Dictionary containing processing results
        """
        results = {"resumes": [], "jobs": [], "errors": []}

        resume_paths = documents_path.get("resume_path", [])
        job_desc_paths = documents_path.get("job_desc_path", [])

        # Process resumes
        for path in resume_paths:
            try:
                self.logger.info(f"Processing resume: {path}")
                result = await self.resume_processor.process_resume(path)
                results["resumes"].append(
                    {
                        "path": path,
                        "result": result,
                        "status": "success" if result else "failed",
                    }
                )
            except Exception as e:
                error_msg = f"Failed to process resume {path}: {str(e)}"
                self.logger.error(error_msg)
                results["errors"].append(error_msg)

        # Process job descriptions
        for path in job_desc_paths:
            try:
                self.logger.info(f"Processing job description: {path}")
                result = await self.job_processor.process_job(path)
                results["jobs"].append(
                    {
                        "path": path,
                        "result": result,
                        "status": "success" if result else "failed",
                    }
                )
            except Exception as e:
                error_msg = f"Failed to process job description {path}: {str(e)}"
                self.logger.error(error_msg)
                results["errors"].append(error_msg)

        return results

    async def perform_talent_matching_analysis(self) -> dict:
        """
        Perform comprehensive talent matching analysis after document processing.

        Returns:
            Dictionary containing matching analysis results
        """
        try:
            self.logger.info("Starting talent matching analysis...")

            # Perform comprehensive analysis
            comprehensive_result = (
                await self.talent_matcher.perform_comprehensive_analysis()
            )

            # You can also demonstrate specific matching scenarios
            matching_results = {
                "comprehensive_analysis": comprehensive_result,
                "status": "success" if comprehensive_result else "failed",
            }

            return matching_results

        except Exception as e:
            error_msg = f"Failed to perform talent matching analysis: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg, "status": "failed"}

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
        """Print processing summary including matching analysis."""
        print("\n" + "=" * 80)
        print("📊 PROCESSING SUMMARY")
        print("=" * 80)

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
    """Main entry point for the document processing application."""
    pipeline = DocumentProcessingPipeline()

    try:
        # Phase 1: Process documents (resumes and jobs)
        print("🚀 Phase 1: Processing Documents...")
        results = await pipeline.process_documents(documents_path)

        # Phase 2: Perform talent matching analysis
        print("\n🚀 Phase 2: Performing Talent Matching Analysis...")
        matching_results = await pipeline.perform_talent_matching_analysis()

        # Print comprehensive summary
        pipeline.print_summary(results, matching_results)

    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        raise


async def demo_specific_matching():
    """
    Demonstration of specific matching scenarios.
    Note: You'll need to replace these IDs with actual ones from your database.
    """
    pipeline = DocumentProcessingPipeline()

    print("\n" + "=" * 80)
    print("🎯 SPECIFIC MATCHING DEMONSTRATIONS")
    print("=" * 80)

    try:
        # Demo 1: Find candidates for a specific job
        # Note: Replace 'sample_job_id' with an actual job index from ChromaDB (e.g., "0", "1", "2")
        print("\n📋 Demo 1: Finding candidates for a specific job...")
        job_matching_result = await pipeline.find_best_candidates_for_job(
            "sample_job_id", top_k=3
        )
        if job_matching_result.get("status") == "success":
            print("✅ Job-to-candidates matching completed")
        else:
            print("⚠️ Job-to-candidates matching demo skipped (no valid job ID)")

        # Demo 2: Find jobs for a specific candidate
        # Note: Replace 'sample_candidate_id' with an actual candidate index from ChromaDB (e.g., "0", "1", "2")
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
        print(
            "   with actual indices from your ChromaDB collections (e.g., '0', '1', '2')."
        )

    except Exception as e:
        logger.error(f"Matching demonstration failed: {e}")

    print("=" * 80)


if __name__ == "__main__":
    documents_path = {
        "resume_path": [
            "/Users/tharuntejapeddi/Projects/resume-job-matcher/resumes/Anita_Daiya.pdf",
            "/Users/tharuntejapeddi/Projects/resume-job-matcher/resumes/rohini.pdf",
        ],
        "job_desc_path": [
            "/Users/tharuntejapeddi/Projects/resume-job-matcher/job/QA_Engineer_Contract_Job_Post_NTT_SINGAPORE.pdf"
        ],
    }

    async def run_complete_pipeline():
        """Run the complete pipeline with document processing and talent matching."""
        # Main processing pipeline
        await main(documents_path)

        # Demonstrate specific matching capabilities
        await demo_specific_matching()

    # Run the complete pipeline
    asyncio.run(run_complete_pipeline())
