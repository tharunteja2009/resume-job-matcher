import logging
from pathlib import Path
from typing import Optional, Dict, Any
from autogen_agentchat.messages import TextMessage
from src.core.parsers.base_document_parser import (
    BaseDocumentParser,
    DocumentProcessingError,
)
from src.ai.teams.resume_processing_team import get_resume_processing_team

# Configure logging
logger = logging.getLogger(__name__)


class ResumeParserAgent(BaseDocumentParser):
    """Agent responsible for parsing and processing resumes using AI."""

    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        """Initialize the resume parser agent.

        Args:
            model_name: The model name to use for processing
        """
        super().__init__(model_name)
        self._processing_team = None

    def get_processing_team(self, num_resumes: int = 1):
        """Get the resume processing team with optimized max_turns.

        Args:
            num_resumes: Number of resumes being processed in this batch
        """
        return get_resume_processing_team(num_resumes=num_resumes)

    def _build_resume_chunk_message(
        self, chunk: str, chunk_index: int, total_chunks: int
    ) -> TextMessage:
        """Build a task message for processing a resume chunk.

        Args:
            chunk: Text chunk to process
            chunk_index: Current chunk index (1-based)
            total_chunks: Total number of chunks

        Returns:
            TextMessage for the chunk processing task
        """
        return TextMessage(
            content=f"Please parse the following section of the resume (part {chunk_index}/{total_chunks}):\n\n{chunk}",
            source="user",
        )

    async def process_resume(self, resume_path: str) -> Optional[Dict[str, Any]]:
        """Process a resume file and store the extracted information."""
        try:
            self._print_processing_header("RESUME", resume_path)

            # Step 1: Extract and process text
            resume_text = self.extract_text_from_file(resume_path)
            chunks = self.prepare_text_for_processing(resume_text)

            if not chunks:
                self.logger.error("❌ No processable chunks generated")
                return None

            # Step 2: Process chunks with AI agents
            self._print_step_header(2, "Processing with AI Agents")
            processing_team = self.get_processing_team(num_resumes=1)

            # Use the reusable chunk processor
            processing_result = await self.process_chunks_with_team(
                chunks=chunks,
                processing_team=processing_team,
                chunk_message_builder=self._build_resume_chunk_message,
                document_type="resume",
            )

            combined_results = processing_result.get("combined_results", [])
            last_message = processing_result.get("last_message")
            total_steps = processing_result.get("total_steps", 0)

            if not combined_results and not last_message:
                self.logger.error("No responses received from processing agents")
                return None

            self._print_completion_message("RESUME", resume_path, total_steps)
            return last_message or combined_results[-1] if combined_results else None

        except DocumentProcessingError as e:
            self.logger.error(f"Document processing error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error processing resume: {e}")
            raise

    async def process_document(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Implement the abstract method to process resumes."""
        return await self.process_resume(file_path)
