# =============================================================================
# Clinical Guideline Research Assistant
# Copyright (c) 2024. MIT License. See LICENSE file for details.
# =============================================================================
"""Clinical Guideline Research Assistant - Agents.

FREE-TIER agents using Ollama (local LLM).
"""
from agents.query_filter_agent_lite import QueryFilterAgentLite
from agents.retriever_summarizer_agent_lite import RetrieverSummarizerAgentLite
from agents.fact_check_writer_agent_lite import FactCheckWriterAgentLite

__all__ = [
    "QueryFilterAgentLite",
    "RetrieverSummarizerAgentLite", 
    "FactCheckWriterAgentLite"
]
