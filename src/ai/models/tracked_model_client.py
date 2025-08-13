"""
Enhanced model client with token usage tracking.
This module wraps the OpenAI client to automatically track token consumption.
"""

from typing import Optional, Dict, Any, AsyncIterator, List
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import ChatCompletionClient, LLMMessage
from autogen_core.models._types import CreateResult
from config.settings import get_config
from src.ai.tracking.token_tracker import get_token_tracker
import logging

logger = logging.getLogger(__name__)


class TrackedOpenAIChatCompletionClient(OpenAIChatCompletionClient):
    """OpenAI chat completion client with automatic token usage tracking."""

    def __init__(self, operation_type: str = "unknown", **kwargs):
        """Initialize the tracked client.

        Args:
            operation_type: Type of operation for tracking (e.g., 'resume_parsing')
            **kwargs: Arguments passed to the base OpenAI client
        """
        super().__init__(**kwargs)
        self.operation_type = operation_type
        self.tracker = get_token_tracker()

    async def create(
        self,
        messages: List[LLMMessage],
        *,
        tools: Optional[List] = None,
        tool_choice: str = "auto",
        json_output: Optional[Any] = None,
        extra_create_args: Optional[Dict[str, Any]] = None,
        cancellation_token: Optional[Any] = None,
        **kwargs,
    ) -> CreateResult:
        """Create a chat completion with token tracking.

        Args:
            messages: List of messages for the conversation
            tools: Optional tools for function calling
            tool_choice: Tool choice strategy
            json_output: Optional JSON output specification
            extra_create_args: Extra arguments for the API call
            cancellation_token: Optional cancellation token
            **kwargs: Additional arguments for the completion

        Returns:
            CreateResult with the completion response
        """
        # Call the parent method to get the result
        result = await super().create(
            messages,
            tools=tools or [],
            tool_choice=tool_choice,
            json_output=json_output,
            extra_create_args=extra_create_args or {},
            cancellation_token=cancellation_token,
            **kwargs,
        )

        # Extract token usage from the result
        if hasattr(result, "usage") and result.usage:
            usage = result.usage
            prompt_tokens = getattr(usage, "prompt_tokens", 0)
            completion_tokens = getattr(usage, "completion_tokens", 0)

            # Get the model name properly
            model_name = (
                kwargs.get("model")
                or getattr(self, "model", None)
                or getattr(self, "_model", "gpt-3.5-turbo")
            )

            # Record the token usage
            cost = self.tracker.record_usage(
                operation_type=self.operation_type,
                model_name=model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )

            logger.info(
                f"Token usage - Operation: {self.operation_type}, "
                f"Model: {model_name}, "
                f"Tokens: {prompt_tokens + completion_tokens}, "
                f"Cost: ${cost:.4f}"
            )

        return result


def get_tracked_model_client(
    operation_type: str, model_type: Optional[str] = None
) -> TrackedOpenAIChatCompletionClient:
    """Get a tracked OpenAI model client with token usage monitoring.

    Args:
        operation_type: Type of operation for tracking purposes
        model_type: Optional type of model to use ('parsing', 'analysis', or None for default)

    Returns:
        Configured TrackedOpenAIChatCompletionClient instance
    """
    config = get_config()
    model_config = config.get_model_config(model_type or "default")

    return TrackedOpenAIChatCompletionClient(
        operation_type=operation_type, **model_config
    )
