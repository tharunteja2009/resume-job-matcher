import logging
from pathlib import Path
from typing import Optional, Dict, Any
from autogen_agentchat.messages import TextMessage
from src.core.parsers.base_document_parser import (
    BaseDocumentParser,
    DocumentProcessingError,
)
from src.ai.teams.job_processing_team import get_job_processing_team

# Configure logging
logger = logging.getLogger(__name__)


class JobParserAgent(BaseDocumentParser):
    """Agent responsible for parsing and processing job descriptions using AI."""

    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        """Initialize the job parser agent.

        Args:
            model_name: The model name to use for processing
        """
        super().__init__(model_name)
        self._processing_team = None

    def get_processing_team(self, num_jobs: int = 1):
        """Get the job processing team with optimized max_turns.

        Args:
            num_jobs: Number of jobs being processed in this batch
        """
        return get_job_processing_team(num_jobs=num_jobs)

    def _build_job_chunk_message(
        self, chunk: str, chunk_index: int, total_chunks: int
    ) -> TextMessage:
        """Build a task message for processing a job description chunk.

        Args:
            chunk: Text chunk to process
            chunk_index: Current chunk index (1-based)
            total_chunks: Total number of chunks

        Returns:
            TextMessage for the chunk processing task
        """
        task_prompt = (
            f"Please analyze this part ({chunk_index}/{total_chunks}) of the job description and extract:\n"
            "1. Basic Information (title, company, location)\n"
            "2. Required Skills and Experience\n"
            "3. Key Responsibilities\n"
            "4. Qualifications and Requirements\n"
            "5. Benefits and Additional Information\n\n"
            f"Job Description Text Part {chunk_index}:\n{chunk}"
        )

        return TextMessage(content=task_prompt, source="user")

    async def process_job(self, job_desc_path: str) -> Optional[Dict[str, Any]]:
        """Process a job description file and extract structured information."""
        try:
            self._print_processing_header("JOB DESCRIPTION", job_desc_path)

            # Step 1: Extract and process text
            job_text = self.extract_text_from_file(job_desc_path)
            chunks = self.prepare_text_for_processing(job_text)

            if not chunks:
                self.logger.error("❌ No processable chunks generated")
                return None

            # Step 2: Process chunks with AI agents
            self._print_step_header(2, "Processing with AI Agents")
            processing_team = self.get_processing_team(num_jobs=1)

            # Use the reusable chunk processor
            processing_result = await self.process_chunks_with_team(
                chunks=chunks,
                processing_team=processing_team,
                chunk_message_builder=self._build_job_chunk_message,
                document_type="job description",
            )

            last_message = processing_result.get("last_message")
            total_steps = processing_result.get("total_steps", 0)

            if not last_message:
                self.logger.error("No response received from processing agents")
                return None

            self._print_completion_message(
                "JOB DESCRIPTION", job_desc_path, total_steps
            )
            return last_message

        except DocumentProcessingError as e:
            self.logger.error(f"Document processing error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error processing job description: {e}")
            raise

    async def process_document(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Implement the abstract method to process job descriptions."""
        return await self.process_job(file_path)
