"""
Configuration management for the resume-job-matcher application.
Centralizes all configuration settings and provides environment-based configuration.
"""

import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from dataclasses import dataclass

# Load environment variables
load_dotenv()


@dataclass
class DatabaseConfig:
    """Database configuration settings."""

    hostname: str = "gwypnx.h.filess.io"
    database: str = "resumejobmatcher_closerzulu"
    port: str = "27018"
    username: Optional[str] = None
    password: Optional[str] = None

    def __post_init__(self):
        """Load database credentials from environment."""
        self.username = os.getenv("DB_USERNAME")
        self.password = os.getenv("DB_PASSWORD")

    @property
    def uri(self) -> str:
        """Get MongoDB connection URI."""
        if self.username and self.password:
            return f"mongodb://{self.username}:{self.password}@{self.hostname}:{self.port}/{self.database}"
        return f"mongodb://{self.hostname}:{self.port}/{self.database}"


@dataclass
class ModelConfig:
    """AI model configuration settings."""

    default_model: str = "gpt-3.5-turbo"
    parsing_model: str = "gpt-3.5-turbo"
    analysis_model: str = "gpt-4"
    max_tokens: int = 1500
    temperature: float = 0.5
    api_key: Optional[str] = None

    def __post_init__(self):
        """Load API key from environment."""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")


@dataclass
class ProcessingConfig:
    """Document processing configuration."""

    max_chunk_tokens: int = 800
    chunk_overlap: int = 50
    max_turns: int = 2
    timeout: int = 120


@dataclass
class ChromaDBConfig:
    """ChromaDB configuration settings."""

    persist_directory: str = "./chromadb"
    collection_candidates: str = "candidate_profiles"
    collection_jobs: str = "job_descriptions"

    def __post_init__(self):
        """Ensure persist directory exists."""
        import os

        os.makedirs(self.persist_directory, exist_ok=True)


@dataclass
class ApplicationConfig:
    """Main application configuration."""

    database: DatabaseConfig
    models: ModelConfig
    processing: ProcessingConfig
    chromadb: ChromaDBConfig

    # Collection names
    candidates_collection: str = "candidates"
    jobs_collection: str = "job"

    # Logging configuration
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    def __init__(self):
        """Initialize all configuration sections."""
        self.database = DatabaseConfig()
        self.models = ModelConfig()
        self.processing = ProcessingConfig()
        self.chromadb = ChromaDBConfig()

        # Override from environment variables if available
        self._load_from_environment()

    def _load_from_environment(self):
        """Load configuration overrides from environment variables."""
        if os.getenv("MAX_CHUNK_TOKENS"):
            self.processing.max_chunk_tokens = int(os.getenv("MAX_CHUNK_TOKENS"))

        if os.getenv("MAX_TURNS"):
            self.processing.max_turns = int(os.getenv("MAX_TURNS"))

        if os.getenv("LOG_LEVEL"):
            self.log_level = os.getenv("LOG_LEVEL")

    def get_model_config(self, model_type: str = "default") -> Dict[str, Any]:
        """Get model configuration for specific use case."""
        base_config = {
            "api_key": self.models.api_key,
            "max_tokens": self.models.max_tokens,
            "temperature": self.models.temperature,
        }

        if model_type == "parsing":
            base_config.update(
                {
                    "model": self.models.parsing_model,
                    "temperature": 0.3,  # More deterministic for parsing
                    "max_tokens": 1000,
                }
            )
        elif model_type == "analysis":
            base_config.update(
                {
                    "model": self.models.analysis_model,
                    "temperature": 0.7,  # More creative for analysis
                    "max_tokens": 2000,
                }
            )
        else:
            base_config.update({"model": self.models.default_model})

        return base_config


# Global configuration instance
config = ApplicationConfig()


def get_config() -> ApplicationConfig:
    """Get the global configuration instance."""
    return config
