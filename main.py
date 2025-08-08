import asyncio
import logging
from util.ResumeParser import ResumeParserAgent
from util.JobParser import JobParserAgent

# Configure logging
logging.basicConfig(
    level=logging.WARNING, format="%(message)s", handlers=[logging.StreamHandler()]
)

# Only show important messages from autogen
for logger_name in ["autogen_core.events", "autogen_core"]:
    logging.getLogger(logger_name).setLevel(logging.ERROR)

# Set custom loggers for agent and tool interactions
for logger_name in ["agents", "tools"]:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    logger.propagate = False  # Prevent duplicate logging

logger = logging.getLogger(__name__)


async def main(documents_path: dict) -> None:
    """Main entry point for the resume processing application."""
    resume_agent_class = ResumeParserAgent()
    job_agent_class = JobParserAgent()

    resume_path = documents_path.get("resume_path", [])
    job_desc_path = documents_path.get("job_desc_path", [])

    for path in resume_path:
        logger.info(f"Processing resume: {path}")
        await resume_agent_class.process_resume(path)
    for path in job_desc_path:
        logger.info(f"Processing job description: {path}")
        await job_agent_class.process_job(path)


if __name__ == "__main__":
    documents_path = {
        "resume_path": [
            "/Users/tharuntejapeddi/Projects/resume-job-matcher/resumes/CV_Tharun Peddi_AI_QA.pdf",
            "/Users/tharuntejapeddi/Projects/resume-job-matcher/resumes/Huang_Anni-SDE-20250408.pdf",
            "/Users/tharuntejapeddi/Projects/resume-job-matcher/resumes/Rohini_Tilakam_Thyagarajan.pdf",
            "/Users/tharuntejapeddi/Projects/resume-job-matcher/resumes/MrinalAich-8.6yearsExp-Backend-SeniorSoftwareEngineer-Shopee-ExOracle-ExPolaris-IIT.pdf",
        ],
        "job_desc_path": [
            "/Users/tharuntejapeddi/Projects/resume-job-matcher/job/QA_Engineer_Contract_Job_Post_NTT_SINGAPORE.pdf"
        ],
    }
    asyncio.run(main(documents_path))
