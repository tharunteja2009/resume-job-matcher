"""
Base document parser class providing common functionality for parsing documents.
This serves as the foundation for both resume and job description parsing.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from autogen_agentchat.messages import TextMessage

from src.common.text.text_processor import TextProcessor
from src.common.text.pdf_to_text_extractor import extract_text_from_pdf
from src.core.processors.agent_message_processor import DocumentChunkProcessor
from src.common.formatters.project_formatter import ProjectFormatter


# Configure logging
logger = logging.getLogger(__name__)


class DocumentProcessingError(Exception):
    """Custom exception for document processing errors."""

    pass


class BaseDocumentParser(ABC):
    """Abstract base class for document parsing operations."""

    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        """Initialize the document parser.

        Args:
            model_name: The model name to use for token processing
        """
        self.text_processor = TextProcessor(model_name)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.chunk_processor = DocumentChunkProcessor(self.__class__.__name__)

    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text from a document file.

        Args:
            file_path: Path to the document file

        Returns:
            Extracted text content

        Raises:
            DocumentProcessingError: If text extraction fails
        """
        try:
            file_path_obj = Path(file_path)

            if not file_path_obj.exists():
                raise DocumentProcessingError(f"File not found: {file_path}")

            if file_path_obj.suffix.lower() == ".pdf":
                text = extract_text_from_pdf(file_path)
            else:
                # Handle other file types if needed
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()

            if not text or not text.strip():
                raise DocumentProcessingError(
                    f"No text content extracted from: {file_path}"
                )

            # Clean and normalize the text
            cleaned_text = self.text_processor.clean_text(text)

            self.logger.info(f"Successfully extracted text from {file_path_obj.name}")
            return cleaned_text

        except Exception as e:
            error_msg = f"Failed to extract text from {file_path}: {str(e)}"
            self.logger.error(error_msg)
            raise DocumentProcessingError(error_msg) from e

    def prepare_text_for_processing(
        self, text: str, max_tokens: int = 800
    ) -> List[str]:
        """Prepare text for processing by chunking it appropriately.

        Args:
            text: Raw text to prepare
            max_tokens: Maximum tokens per chunk

        Returns:
            List of text chunks ready for processing
        """
        if not text:
            return []

        # Get text statistics for logging
        stats = self.text_processor.get_text_stats(text)
        self._log_text_stats(stats)

        # Chunk the text
        chunks = self.text_processor.chunk_text(text, max_tokens)
        self._log_chunking_info(chunks)

        return chunks

    async def process_chunks_with_team(
        self,
        chunks: List[str],
        processing_team,
        chunk_message_builder: Callable,
        document_type: str = "document",
    ) -> Dict[str, Any]:
        """Process chunks using the reusable chunk processor.

        Args:
            chunks: List of text chunks to process
            processing_team: AutoGen team for processing
            chunk_message_builder: Function to build task messages
            document_type: Type of document being processed

        Returns:
            Processing results with last_message and combined_results
        """
        return await self.chunk_processor.process_chunks_with_agents(
            chunks=chunks,
            processing_team=processing_team,
            text_processor=self.text_processor,
            chunk_message_builder=chunk_message_builder,
            document_type=document_type,
        )

    def _log_text_stats(self, stats: Dict[str, Any]) -> None:
        """Log text statistics."""
        self.logger.info("📊 Document Statistics:")
        self.logger.info(f"   • Characters: {stats['characters']:,}")
        self.logger.info(f"   • Words: {stats['words']:,}")
        self.logger.info(f"   • Lines: {stats['lines']:,}")
        self.logger.info(f"   • Paragraphs: {stats['paragraphs']:,}")
        self.logger.info(f"   • Estimated Tokens: {stats['estimated_tokens']:,}")

    def _log_chunking_info(self, chunks: List[str]) -> None:
        """Log chunking information."""
        self.logger.info(f"📑 Chunking Results:")
        self.logger.info(f"   • Total Chunks: {len(chunks)}")
        for i, chunk in enumerate(chunks, 1):
            chunk_tokens = self.text_processor.estimate_tokens(chunk)
            self.logger.info(
                f"   • Chunk {i}: ~{chunk_tokens:,} tokens ({len(chunk):,} chars)"
            )

    def _print_processing_header(self, document_type: str, source_file: str) -> None:
        """Print a formatted processing header."""
        ProjectFormatter.print_processing_header(document_type, source_file)

    def _print_step_header(self, step_number: int, step_name: str) -> None:
        """Print a formatted step header."""
        ProjectFormatter.print_step_header(step_number, step_name)

    def _print_completion_message(
        self, document_type: str, source_file: str, steps: int
    ) -> None:
        """Print processing completion message."""
        ProjectFormatter.print_completion_message(document_type, source_file, steps)

    @abstractmethod
    async def process_document(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Process a document and return extracted information.

        This method must be implemented by subclasses to define specific
        document processing logic.

        Args:
            file_path: Path to the document file

        Returns:
            Extracted information as a dictionary, or None if processing fails
        """
        pass

    @abstractmethod
    def get_processing_team(self, **kwargs):
        """Get the processing team for this document type.

        Args:
            **kwargs: Team configuration parameters

        Returns:
            The processing team instance
        """
        pass
