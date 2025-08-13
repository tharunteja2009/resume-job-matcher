"""
Common formatting utilities for consistent UI/logging across the resume-job-matcher project.
This module provides standardized printing and display functions to maintain visual consistency.
"""

from pathlib import Path
from typing import Any, Dict, List


class ProjectFormatter:
    """Provides clean, user-friendly formatting for project output."""

    @staticmethod
    def print_processing_header(document_type: str, source_file: str) -> None:
        """Print a clean processing header."""
        print(f"\n🔄 Processing {document_type}: {Path(source_file).name}")

    @staticmethod
    def print_step_header(step_number: int, step_name: str) -> None:
        """Print a minimal step header - only for essential steps."""
        print(f"  📝 {step_name}")

    @staticmethod
    def print_completion_message(
        document_type: str, source_file: str, steps: int
    ) -> None:
        """Print clean completion message."""
        print(f"  ✅ {document_type.title()} processed: {Path(source_file).name}")

    @staticmethod
    def print_phase_header(phase_num: int, description: str) -> None:
        """Print a clean phase header."""
        print(f"\n🚀 Phase {phase_num}: {description}")

    @staticmethod
    def print_section_divider(title: str = "") -> None:
        """Print a minimal section divider."""
        if title:
            print(f"\n{title}")

    @staticmethod
    def print_subsection_header(title: str) -> None:
        """Print a clean subsection header."""
        print(f"  📌 {title}")

    @staticmethod
    def print_processing_stats(stats: Dict[str, Any]) -> None:
        """Skip detailed processing stats for cleaner output."""
        pass  # Suppressed for cleaner user experience

    @staticmethod
    def print_chunk_processing_header(
        chunk_index: int, total_chunks: int, tokens: int
    ) -> None:
        """Show minimal chunk progress for multi-part documents."""
        if total_chunks > 1:
            print(f"  📄 Processing part {chunk_index} of {total_chunks}")

    @staticmethod
    def print_error_message(error_type: str, message: str) -> None:
        """Print a clean error message."""
        print(f"  ❌ {message}")

    @staticmethod
    def print_success_message(message: str) -> None:
        """Print a clean success message."""
        print(f"  ✅ {message}")

    @staticmethod
    def print_info_message(message: str) -> None:
        """Print a clean info message."""
        print(f"  ℹ️  {message}")

    @staticmethod
    def print_warning_message(message: str) -> None:
        """Print a clean warning message."""
        print(f"  ⚠️  {message}")

    # Convenience methods for shorter names
    @staticmethod
    def print_success(message: str) -> None:
        """Convenience method for success messages."""
        ProjectFormatter.print_success_message(message)

    @staticmethod
    def print_info(message: str) -> None:
        """Convenience method for info messages."""
        ProjectFormatter.print_info_message(message)

    @staticmethod
    def print_error(message: str) -> None:
        """Convenience method for error messages."""
        ProjectFormatter.print_error_message("ERROR", message)

    @staticmethod
    def print_warning(message: str) -> None:
        """Convenience method for warning messages."""
        ProjectFormatter.print_warning_message(message)

    @staticmethod
    def print_section_header(title: str) -> None:
        """Convenience method for section headers."""
        print(f"\n{'=' * 60}")
        print(f"{title}")
        print("=" * 60)
