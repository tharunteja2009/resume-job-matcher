import asyncio
import logging
from util.ResumeParser import ResumeParserAgent

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


async def main(resume_path: list) -> None:
    """Main entry point for the resume processing application."""
    agent = ResumeParserAgent()
    for path in resume_path:
        logger.info(f"Processing resume: {path}")
        await agent.process_resume(path)


if __name__ == "__main__":
    resume_path = [
        "/Users/tharuntejapeddi/Projects/resume-job-matcher/resumes/CV_Tharun Peddi_AI_QA.pdf",
        "/Users/tharuntejapeddi/Projects/resume-job-matcher/resumes/Mounika_CV_QA.pdf",
    ]
    asyncio.run(main(resume_path))
