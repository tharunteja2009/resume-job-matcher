"""
Text processing utilities for token estimation, chunking, and document processing.
This module provides common functionality for processing text documents across the application.
"""

import re
from typing import List, Dict, Any
import tiktoken
from pathlib import Path


class TextProcessor:
    """Utility class for text processing operations."""

    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        """Initialize TextProcessor with the specified model for token counting.

        Args:
            model_name: The model name to use for token encoding (default: gpt-3.5-turbo)
        """
        try:
            self.encoding = tiktoken.encoding_for_model(model_name)
        except KeyError:
            # Fallback to cl100k_base encoding if model not found
            self.encoding = tiktoken.get_encoding("cl100k_base")

    def estimate_tokens(self, text: str) -> int:
        """Accurately estimate the number of tokens in a text string.

        Args:
            text: The text to analyze

        Returns:
            The estimated number of tokens
        """
        if not text:
            return 0
        return len(self.encoding.encode(text))

    def chunk_text(
        self, text: str, max_tokens: int = 800, overlap: int = 50
    ) -> List[str]:
        """Split text into chunks with optional overlap for better context preservation.

        Args:
            text: Text to split into chunks
            max_tokens: Maximum number of tokens per chunk
            overlap: Number of tokens to overlap between chunks

        Returns:
            List of text chunks
        """
        if not text:
            return []

        chunks = []
        current_chunk = []
        current_tokens = 0

        # Split by paragraphs first to maintain structure
        paragraphs = text.split("\n\n")

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            paragraph_tokens = self.estimate_tokens(paragraph)

            # If paragraph is too large, split by sentences
            if paragraph_tokens > max_tokens:
                sentences = self._split_into_sentences(paragraph)
                for sentence in sentences:
                    sentence_tokens = self.estimate_tokens(sentence)

                    if current_tokens + sentence_tokens > max_tokens and current_chunk:
                        chunks.append("\n".join(current_chunk))

                        # Add overlap from previous chunk
                        if overlap > 0 and chunks:
                            overlap_text = self._get_overlap_text(
                                current_chunk, overlap
                            )
                            current_chunk = [overlap_text] if overlap_text else []
                            current_tokens = (
                                self.estimate_tokens(overlap_text)
                                if overlap_text
                                else 0
                            )
                        else:
                            current_chunk = []
                            current_tokens = 0

                    current_chunk.append(sentence)
                    current_tokens += sentence_tokens
            else:
                # Check if adding this paragraph would exceed the limit
                if current_tokens + paragraph_tokens > max_tokens and current_chunk:
                    chunks.append("\n".join(current_chunk))

                    # Add overlap from previous chunk
                    if overlap > 0 and chunks:
                        overlap_text = self._get_overlap_text(current_chunk, overlap)
                        current_chunk = [overlap_text] if overlap_text else []
                        current_tokens = (
                            self.estimate_tokens(overlap_text) if overlap_text else 0
                        )
                    else:
                        current_chunk = []
                        current_tokens = 0

                current_chunk.append(paragraph)
                current_tokens += paragraph_tokens

        # Add the last chunk if it exists
        if current_chunk:
            chunks.append("\n".join(current_chunk))

        return chunks

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using regex patterns.

        Args:
            text: Text to split into sentences

        Returns:
            List of sentences
        """
        # Pattern to split on sentence endings while preserving structure
        sentence_pattern = r"(?<=[.!?])\s+"
        sentences = re.split(sentence_pattern, text)
        return [s.strip() for s in sentences if s.strip()]

    def _get_overlap_text(self, chunk_lines: List[str], overlap_tokens: int) -> str:
        """Get overlap text from the end of a chunk.

        Args:
            chunk_lines: List of lines in the chunk
            overlap_tokens: Number of tokens for overlap

        Returns:
            Overlap text or empty string
        """
        if not chunk_lines:
            return ""

        # Start from the end and work backwards until we have enough tokens
        overlap_lines = []
        current_tokens = 0

        for line in reversed(chunk_lines):
            line_tokens = self.estimate_tokens(line)
            if current_tokens + line_tokens > overlap_tokens:
                break
            overlap_lines.insert(0, line)
            current_tokens += line_tokens

        return "\n".join(overlap_lines)

    def clean_text(self, text: str) -> str:
        """Clean and normalize text for processing.

        Args:
            text: Raw text to clean

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove special characters that might cause issues
        text = re.sub(r"[^\w\s\-.,!?()@+/:]", " ", text)

        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        return text.strip()

    def get_text_stats(self, text: str) -> Dict[str, Any]:
        """Get comprehensive statistics about text.

        Args:
            text: Text to analyze

        Returns:
            Dictionary containing text statistics
        """
        if not text:
            return {
                "characters": 0,
                "words": 0,
                "lines": 0,
                "paragraphs": 0,
                "estimated_tokens": 0,
            }

        stats = {
            "characters": len(text),
            "words": len(text.split()),
            "lines": len(text.split("\n")),
            "paragraphs": len([p for p in text.split("\n\n") if p.strip()]),
            "estimated_tokens": self.estimate_tokens(text),
        }

        return stats


def create_text_processor(model_name: str = "gpt-3.5-turbo") -> TextProcessor:
    """Factory function to create a TextProcessor instance.

    Args:
        model_name: The model name to use for token encoding

    Returns:
        Configured TextProcessor instance
    """
    return TextProcessor(model_name)
