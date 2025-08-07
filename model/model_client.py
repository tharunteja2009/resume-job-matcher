from autogen_ext.models.openai import OpenAIChatCompletionClient
from config.constants import MODEL_OPENAI
import os
from dotenv import load_dotenv

load_dotenv()


def get_model_client():
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    model_client = OpenAIChatCompletionClient(model="gpt-4o", api_key=OPENAI_API_KEY)
    return model_client
