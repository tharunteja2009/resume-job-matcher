from autogen_ext.models.openai import OpenAIChatCompletionClient
from config.settings import get_config
from typing import Optional


def get_model_client(model_type: Optional[str] = None) -> OpenAIChatCompletionClient:
    """Get an OpenAI model client with appropriate configuration.

    Args:
        model_type: Optional type of model to use ('parsing', 'analysis', or None for default).

    Returns:
        Configured OpenAIChatCompletionClient instance
    """
    config = get_config()
    model_config = config.get_model_config(model_type or "default")

    return OpenAIChatCompletionClient(**model_config)
