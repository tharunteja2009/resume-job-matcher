import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from util.pdf_to_text_extractor import extract_text_from_pdf
from util.mongo_util import insert_candidate_to_mongo
from model.model_client import get_model_client
from teams.tech_recruiting_team import get_tech_recruiter_team

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResumeProcessor:
    def __init__(self, output_dir: str = "output-json"):
        self.base_dir = Path(__file__).parent
        self.output_dir = self.base_dir / output_dir
        self._ensure_output_directory()

    def _ensure_output_directory(self) -> None:
        """Create output directory if it doesn't exist."""
        self.output_dir.mkdir(exist_ok=True)

    def _clean_json_content(self, content: str) -> str:
        """Remove markdown formatting from JSON content."""
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        return content.strip()

    def _parse_json_content(self, content: str) -> Dict[str, Any]:
        """Parse JSON content into a dictionary."""
        try:
            cleaned_content = self._clean_json_content(content)
            return json.loads(cleaned_content)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON content: {e}")
            raise

    def _generate_output_path(self, resume_data: Dict[str, Any]) -> Path:
        """Generate output file path based on candidate name and timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        candidate_name = resume_data.get("full_name", "unknown").replace(" ", "_")
        filename = f"{candidate_name}_{timestamp}.json"
        return self.output_dir / filename

    def save_resume_data(self, resume_data: Dict[str, Any]) -> Optional[Path]:
        """Save resume data to JSON file."""
        try:
            output_path = self._generate_output_path(resume_data)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(resume_data, f, indent=4, ensure_ascii=False)
            logger.info(f"JSON output saved to: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error saving JSON file: {e}")
            return None


class ResumeAgent:
    def __init__(self):
        self.model_client = get_model_client()
        self.team = get_tech_recruiter_team(self.model_client)
        self.processor = ResumeProcessor()

    async def process_resume(self, resume_path: str) -> None:
        """Process a resume file and store the extracted information."""
        try:
            # Extract text from resume
            resume_text = extract_text_from_pdf(resume_path)
            if not resume_text:
                logger.error("Failed to extract text from resume")
                return

            # Parse resume using agent
            result = await self.team.run(
                task=f"Please parse the following resume:\n\n{resume_text}"
            )

            if not hasattr(result, "messages") or not result.messages:
                logger.error("No response received from agent")
                return

            # Get the last message
            last_message = result.messages[-1]
            logger.info("Last Message Content:")
            print(last_message.content)

            # Process and save resume data
            resume_data = self.processor._parse_json_content(last_message.content)
            output_path = self.processor.save_resume_data(resume_data)

            # Store in MongoDB if save was successful
            if output_path:
                insert_candidate_to_mongo(output_path)

        except Exception as e:
            logger.error(f"Error processing resume: {e}")
            raise


async def main(resume_path: str) -> None:
    """Main entry point for the resume processing application."""
    agent = ResumeAgent()
    await agent.process_resume(resume_path)


if __name__ == "__main__":
    resume_path = "/Users/tharuntejapeddi/Projects/resume-job-matcher/resumes/CV_Tharun Peddi_AI_QA.pdf"
    asyncio.run(main(resume_path))
