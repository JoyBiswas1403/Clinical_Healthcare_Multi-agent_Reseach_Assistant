# =============================================================================
# Clinical Guideline Research Assistant
# Copyright (c) 2024. MIT License. See LICENSE file for details.
# =============================================================================
"""Simplified configuration for FREE-TIER stack.

Uses:
- Ollama (local LLM, free)
- ChromaDB (vector DB, free)
- Whoosh (text search, free)
- SQLite (database, free)
- Local filesystem (storage, free)
"""
import os
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent


class LiteSettings(BaseSettings):
    """Lightweight settings for free-tier deployment."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # ==========================================================================
    # API Configuration
    # ==========================================================================
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    
    # ==========================================================================
    # Ollama LLM (FREE - runs locally)
    # ==========================================================================
    ollama_base_url: str = Field(default="http://localhost:11434/v1")
    ollama_model: str = Field(default="llama3.2")  # Default model
    # Alternative models: "mistral", "tinyllama" (faster), "llama3.1:8b" (better)
    
    # ==========================================================================
    # Agent Temperatures
    # ==========================================================================
    query_filter_temperature: float = Field(default=0.3)
    summarizer_temperature: float = Field(default=0.4)
    fact_check_temperature: float = Field(default=0.1)
    writer_temperature: float = Field(default=0.5)
    
    # ==========================================================================
    # Retrieval Settings
    # ==========================================================================
    retriever_top_k: int = Field(default=20)
    retriever_rerank_top_k: int = Field(default=10)
    brief_max_words: int = Field(default=300)
    
    # ==========================================================================
    # Quality Thresholds  
    # ==========================================================================
    min_source_quality: float = Field(default=0.7)
    min_citation_confidence: float = Field(default=0.8)
    
    # ==========================================================================
    # Data Directories (FREE - local filesystem)
    # ==========================================================================
    @property
    def data_dir(self) -> Path:
        """Base data directory."""
        return PROJECT_ROOT / "data_store"
    
    @property
    def documents_dir(self) -> Path:
        """Where source documents are stored."""
        return self.data_dir / "documents"
    
    @property
    def chroma_dir(self) -> Path:
        """ChromaDB persistence directory."""
        return self.data_dir / "chroma"
    
    @property
    def whoosh_dir(self) -> Path:
        """Whoosh index directory."""
        return self.data_dir / "whoosh_index"
    
    @property
    def sqlite_path(self) -> Path:
        """SQLite database path."""
        return self.data_dir / "clinical_guidelines.db"
    
    @property
    def database_url(self) -> str:
        """SQLite connection URL."""
        return f"sqlite:///{self.sqlite_path}"
    
    def ensure_directories(self):
        """Create all necessary directories."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.documents_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.whoosh_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = LiteSettings()
