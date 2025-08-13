"""
Agent message processing utilities for handling AutoGen agent communications.
This module provides reusable functionality for processing agent messages, tool calls, and content.
"""

import json
import logging
from typing import Optional, Dict, Any
from src.common.formatters.project_formatter import ProjectFormatter

logger = logging.getLogger(__name__)


class AgentMessageProcessor:
    """Handles processing of AutoGen agent messages with clean, minimal output."""

    def __init__(self, logger_name: str = "AgentMessageProcessor"):
        """Initialize the message processor.

        Args:
            logger_name: Name for the logger instance
        """
        self.logger = logging.getLogger(logger_name)
        self.step_counter = 0

    async def process_agent_message(
        self, message, chunk_index: int, total_chunks: int, step: int
    ) -> Optional[Dict[str, Any]]:
        """Process a message from the agent processing stream with minimal output.

        Args:
            message: The message from the agent
            chunk_index: Current chunk index
            total_chunks: Total number of chunks
            step: Current conversation step

        Returns:
            Processing result with last_message and results
        """
        try:
            # Only show progress for important steps, suppress verbose agent communication
            self.step_counter += 1

            # Track message chain quietly
            last_message = None
            results = []
            if hasattr(message, "messages"):
                last_message = message.messages[-1]
                results.append(last_message)
            elif hasattr(message, "content"):
                # Capture content without displaying verbose details
                results.append(message)
                last_message = message

            return {"last_message": last_message, "results": results}

        except Exception as e:
            self.logger.error(f"Error processing agent message: {e}")
            return None

    def handle_tool_calls(self, message) -> None:
        """Handle tool calls quietly - suppress verbose output."""
        # Process tool calls silently for cleaner user experience
        pass

    def handle_agent_content(self, message) -> None:
        """Handle content quietly - suppress verbose agent communication."""
        # Process agent content silently for cleaner user experience
        pass


class DocumentChunkProcessor:
    """Handles chunked document processing with AI agents."""

    def __init__(self, logger_name: str = "DocumentChunkProcessor"):
        """Initialize the chunk processor.

        Args:
            logger_name: Name for the logger instance
        """
        self.logger = logging.getLogger(logger_name)
        self.message_processor = AgentMessageProcessor(logger_name)

    async def process_chunks_with_agents(
        self,
        chunks: list,
        processing_team,
        text_processor,
        chunk_message_builder,
        document_type: str = "document",
    ) -> Dict[str, Any]:
        """Process document chunks with AI agents.

        Args:
            chunks: List of text chunks to process
            processing_team: AutoGen team for processing
            text_processor: TextProcessor instance for token estimation
            chunk_message_builder: Function to build task message for each chunk
            document_type: Type of document being processed (for logging)

        Returns:
            Dictionary with last_message and combined_results
        """
        last_message = None
        conversation_step = 1
        combined_results = []

        for chunk_index, chunk in enumerate(chunks, 1):
            ProjectFormatter.print_chunk_processing_header(
                chunk_index, len(chunks), text_processor.estimate_tokens(chunk)
            )

            # Build task message using provided builder function
            task = chunk_message_builder(chunk, chunk_index, len(chunks))

            try:
                async for message in processing_team.run_stream(task=task):
                    result = await self.message_processor.process_agent_message(
                        message, chunk_index, len(chunks), conversation_step
                    )
                    if result:
                        last_message = result.get("last_message")
                        combined_results.extend(result.get("results", []))
                    conversation_step += 1

            except Exception as stream_err:
                self.logger.error(f"Error processing chunk {chunk_index}: {stream_err}")
                continue

        return {
            "last_message": last_message,
            "combined_results": combined_results,
            "total_steps": conversation_step,
        }
