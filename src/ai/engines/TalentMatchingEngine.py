import asyncio
import logging
from typing import Dict, Any, List, Optional
from autogen_agentchat.messages import TextMessage
from src.ai.teams.talent_matching_team import get_talent_matching_workflow
from src.common.formatters.project_formatter import ProjectFormatter

# Configure logging
logger = logging.getLogger(__name__)


class TalentMatchingEngine:
    """
    Engine for performing intelligent talent matching between candidates and job opportunities.
    Uses ChromaDB vector similarity and AI agents for comprehensive analysis.
    """

    def __init__(self, model_name: str = "gpt-4"):
        """Initialize the talent matching engine.

        Args:
            model_name: The model name to use for analysis (default: gpt-4 for better reasoning)
        """
        self.model_name = model_name
        self.logger = logging.getLogger(self.__class__.__name__)
        self._matching_team = None

    def get_matching_team(self):
        """Get the talent matching team."""
        if self._matching_team is None:
            self._matching_team = get_talent_matching_workflow()
        return self._matching_team

    def _print_processing_header(self, process_type: str, identifier: str):
        """Print processing header for better visibility."""
        ProjectFormatter.print_section_divider()
        print(f"🎯 {process_type}")
        print(f"📄 Processing: {identifier}")
        ProjectFormatter.print_section_divider()

    def _print_step_header(self, step_num: int, description: str):
        """Print step header."""
        ProjectFormatter.print_subsection_header(f"Step {step_num}: {description}")

    async def find_candidates_for_job(
        self, job_id: str, top_k: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        Find the best matching candidates for a specific job.

        Args:
            job_id: Unique identifier of the job
            top_k: Number of top candidates to return

        Returns:
            Dictionary containing ranked candidates with match scores and analysis
        """
        try:
            self._print_processing_header(
                "JOB-TO-CANDIDATES MATCHING", f"Job ID: {job_id}"
            )

            # Prepare the analysis request
            analysis_request = f"""
            Please find the best {top_k} candidates for job ID: {job_id}
            
            Use the find_candidates_for_job_tool with these parameters:
            - job_id: {job_id}
            - top_k: {top_k}
            
            Provide detailed analysis including:
            1. Candidate rankings with similarity scores
            2. Skills alignment analysis
            3. Experience level matching
            4. Recommendations for hiring decisions
            
            ANALYSIS_COMPLETE
            """

            # Process with matching team
            matching_team = self.get_matching_team()

            self._print_step_header(1, "Analyzing Job Requirements vs Candidate Pool")

            result = await matching_team.run(
                task=TextMessage(content=analysis_request, source="user")
            )

            if result and result.messages:
                last_message = result.messages[-1]
                self.logger.info(f"✅ Job-to-candidates analysis completed")
                return {"analysis_result": last_message.content}
            else:
                self.logger.error("❌ No analysis result generated")
                return None

        except Exception as e:
            error_msg = f"Failed to find candidates for job {job_id}: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}

    async def find_jobs_for_candidate(
        self, candidate_id: str, top_k: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        Find the best matching jobs for a specific candidate.

        Args:
            candidate_id: Unique identifier of the candidate
            top_k: Number of top jobs to return

        Returns:
            Dictionary containing ranked jobs with match scores and analysis
        """
        try:
            self._print_processing_header(
                "CANDIDATE-TO-JOBS MATCHING", f"Candidate ID: {candidate_id}"
            )

            # Prepare the analysis request
            analysis_request = f"""
            Please find the best {top_k} job opportunities for candidate ID: {candidate_id}
            
            Use the find_jobs_for_candidate_tool with these parameters:
            - candidate_id: {candidate_id}
            - top_k: {top_k}
            
            Provide detailed analysis including:
            1. Job rankings with similarity scores
            2. Skills utilization potential
            3. Career growth alignment
            4. Role fit recommendations
            
            ANALYSIS_COMPLETE
            """

            # Process with matching team
            matching_team = self.get_matching_team()

            self._print_step_header(1, "Analyzing Candidate Profile vs Job Market")

            result = await matching_team.run(
                task=TextMessage(content=analysis_request, source="user")
            )

            if result and result.messages:
                last_message = result.messages[-1]
                self.logger.info(f"✅ Candidate-to-jobs analysis completed")
                return {"analysis_result": last_message.content}
            else:
                self.logger.error("❌ No analysis result generated")
                return None

        except Exception as e:
            error_msg = f"Failed to find jobs for candidate {candidate_id}: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}

    async def perform_comprehensive_analysis(self) -> Optional[Dict[str, Any]]:
        """
        Perform comprehensive talent matching analysis across all data.

        Returns:
            Dictionary containing comprehensive matching insights and statistics
        """
        try:
            self._print_processing_header("COMPREHENSIVE MATCHING ANALYSIS", "All Data")

            # Directly call the analysis function to get results
            from src.ai.agents.talent_matcher_agent import (
                perform_comprehensive_matching_analysis,
            )

            self._print_step_header(1, "Performing System-wide Analysis")

            # Get comprehensive analysis directly
            analysis_result = perform_comprehensive_matching_analysis()

            # Parse the JSON result
            import json

            analysis_data = json.loads(analysis_result)

            if "error" not in analysis_data:
                self.logger.info(f"✅ Comprehensive analysis completed")
                return {"analysis_result": analysis_result}
            else:
                self.logger.error(f"❌ Analysis error: {analysis_data['error']}")
                return {"error": analysis_data["error"]}

        except Exception as e:
            error_msg = f"Failed to perform comprehensive analysis: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}

    def print_matching_summary(self, results: List[Dict[str, Any]]) -> None:
        """Print a summary of matching results."""
        print("\n" + "=" * 80)
        print("🎯 TALENT MATCHING SUMMARY")
        print("=" * 80)

        for i, result in enumerate(results, 1):
            if "error" in result:
                print(f"❌ Analysis {i}: {result['error']}")
            else:
                print(f"✅ Analysis {i}: Completed successfully")

        print("=" * 80)


async def main_matching_demo():
    """
    Demonstration of the talent matching engine capabilities.
    """
    engine = TalentMatchingEngine()

    try:
        # Example usage scenarios
        results = []

        # 1. Find candidates for a job (you'll need to replace with actual job_id)
        print("🔍 Scenario 1: Finding candidates for a specific job...")
        job_result = await engine.find_candidates_for_job("sample_job_id", top_k=3)
        if job_result:
            results.append(job_result)

        # 2. Find jobs for a candidate (you'll need to replace with actual candidate_id)
        print("\n🔍 Scenario 2: Finding jobs for a specific candidate...")
        candidate_result = await engine.find_jobs_for_candidate(
            "sample_candidate_id", top_k=3
        )
        if candidate_result:
            results.append(candidate_result)

        # 3. Comprehensive analysis
        print("\n🔍 Scenario 3: Comprehensive system analysis...")
        comprehensive_result = await engine.perform_comprehensive_analysis()
        if comprehensive_result:
            results.append(comprehensive_result)

        # Print summary
        engine.print_matching_summary(results)

    except Exception as e:
        logger.error(f"Matching demo failed: {e}")
        raise


if __name__ == "__main__":
    # Run the matching demo
    asyncio.run(main_matching_demo())
