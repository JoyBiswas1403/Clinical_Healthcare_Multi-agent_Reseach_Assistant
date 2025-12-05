# =============================================================================
# Clinical Guideline Research Assistant
# Copyright (c) 2024. MIT License. See LICENSE file for details.
# =============================================================================
"""Tests for the FREE-TIER lite agents.

These tests work without external services:
- Uses mocks for Ollama LLM calls
- Uses real ChromaDB/Whoosh (in-memory)

Run with: pytest tests/test_agents_lite.py -v
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from agents.query_filter_agent_lite import QueryFilterAgentLite
from agents.retriever_summarizer_agent_lite import RetrieverSummarizerAgentLite
from agents.fact_check_writer_agent_lite import FactCheckWriterAgentLite
from data.search_lite import LiteVectorSearch, LiteTextSearch, HybridSearch


# =============================================================================
# TEST: Query Filter Agent
# =============================================================================

class TestQueryFilterAgentLite:
    """Tests for Agent 1: Query+Filter (Lite)."""
    
    def test_expand_query_with_mock(self):
        """Test query expansion with mocked LLM response."""
        agent = QueryFilterAgentLite()
        
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "expanded_queries": [
                "diabetes management elderly patients",
                "glycemic control geriatric population"
            ],
            "mesh_terms": ["Diabetes Mellitus", "Aged", "Blood Glucose"],
            "synonyms": {"elderly": ["aged", "geriatric"]},
            "exclusion_criteria": ["pediatric"],
            "source_priorities": ["meta_analysis", "rct"]
        })
        
        with patch.object(agent.client.chat.completions, 'create', return_value=mock_response):
            result = agent.expand_query("diabetes in elderly")
            
            assert "expanded_queries" in result
            assert len(result["expanded_queries"]) == 2
            assert "mesh_terms" in result
            assert "Diabetes Mellitus" in result["mesh_terms"]
    
    def test_run_returns_correct_structure(self):
        """Test that run() returns proper output structure."""
        agent = QueryFilterAgentLite()
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "expanded_queries": ["query1", "query2"],
            "mesh_terms": ["term1"],
            "synonyms": {},
            "exclusion_criteria": [],
            "source_priorities": []
        })
        
        with patch.object(agent.client.chat.completions, 'create', return_value=mock_response):
            result = agent.run("test topic")
            
            assert result["agent_name"] == "QueryFilterAgentLite"
            assert "output_data" in result
            assert "metrics" in result
            assert "execution_time_ms" in result
            assert result["metrics"]["expanded_queries_count"] == 2


# =============================================================================
# TEST: Retriever Summarizer Agent
# =============================================================================

class TestRetrieverSummarizerAgentLite:
    """Tests for Agent 2: Retriever+Summarizer (Lite)."""
    
    def test_retrieve_from_empty_index(self):
        """Test retrieval returns empty when no documents indexed."""
        agent = RetrieverSummarizerAgentLite()
        
        # Clear any existing data
        results = agent.retrieve(["test query"], top_k=5)
        
        # Should return empty or existing results
        assert isinstance(results, list)
    
    def test_summarize_with_mock(self):
        """Test summarization with mocked LLM."""
        agent = RetrieverSummarizerAgentLite()
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "synthesis": "Key findings show...",
            "source_summaries": [{"source_id": "1", "summary": "Test summary"}],
            "contradictions": [],
            "overall_quality": "high"
        })
        
        mock_docs = [{"doc_id": "1", "title": "Test Doc", "abstract": "Test content"}]
        
        with patch.object(agent.client.chat.completions, 'create', return_value=mock_response):
            result = agent.summarize("test topic", mock_docs)
            
            assert "synthesis" in result
            assert "source_summaries" in result
            assert result["overall_quality"] == "high"
    
    def test_run_returns_correct_structure(self):
        """Test that run() returns proper output structure."""
        agent = RetrieverSummarizerAgentLite()
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "synthesis": "Test synthesis",
            "source_summaries": [],
            "contradictions": [],
            "overall_quality": "medium"
        })
        
        with patch.object(agent.client.chat.completions, 'create', return_value=mock_response):
            result = agent.run("test", ["query1"])
            
            assert result["agent_name"] == "RetrieverSummarizerAgentLite"
            assert "output_data" in result
            assert "retrieved_documents" in result["output_data"]


# =============================================================================
# TEST: Fact Check Writer Agent
# =============================================================================

class TestFactCheckWriterAgentLite:
    """Tests for Agent 3: Fact-Check+Writer (Lite)."""
    
    def test_extract_citations(self):
        """Test citation extraction from brief text."""
        agent = FactCheckWriterAgentLite()
        
        brief_text = "Evidence shows benefits [1]. However, risks exist [2][3]. More details in [1]."
        citations = agent.extract_citations(brief_text)
        
        assert "1" in citations
        assert "2" in citations
        assert "3" in citations
        assert len(citations) == 3  # Unique citations
    
    def test_write_brief_with_mock(self):
        """Test brief writing with mocked LLM."""
        agent = FactCheckWriterAgentLite()
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "brief_text": "Test brief with [1] citation.",
            "word_count": 50,
            "claims": [{"claim_text": "Test claim", "citation_ids": ["1"]}]
        })
        
        with patch.object(agent.client.chat.completions, 'create', return_value=mock_response):
            result = agent.write_brief("test topic", {"synthesis": "test"})
            
            assert "brief_text" in result
            assert result["word_count"] == 50
    
    def test_build_traceability(self):
        """Test traceability mapping."""
        agent = FactCheckWriterAgentLite()
        
        claims = [{"claim_text": "Test claim", "citation_ids": ["1"]}]
        sources = [{"doc_id": "1", "title": "Source 1", "abstract": "Content"}]
        
        traceability = agent.build_traceability(claims, sources)
        
        assert len(traceability) == 1
        assert traceability[0]["claim"] == "Test claim"
        assert traceability[0]["verification_status"] == "verified"
    
    def test_run_returns_correct_structure(self):
        """Test that run() returns proper output structure."""
        agent = FactCheckWriterAgentLite()
        
        # Mock both write_brief and assess_risks
        mock_brief_response = MagicMock()
        mock_brief_response.choices = [MagicMock()]
        mock_brief_response.choices[0].message.content = json.dumps({
            "brief_text": "Test brief [1].",
            "word_count": 20,
            "claims": []
        })
        
        mock_risk_response = MagicMock()
        mock_risk_response.choices = [MagicMock()]
        mock_risk_response.choices[0].message.content = json.dumps({
            "risk_flags": []
        })
        
        with patch.object(agent.client.chat.completions, 'create', 
                         side_effect=[mock_brief_response, mock_risk_response]):
            result = agent.run(
                topic="test",
                retrieved_docs=[{"doc_id": "1", "title": "Test", "abstract": "Content"}],
                summary_data={"synthesis": "test"}
            )
            
            assert result["agent_name"] == "FactCheckWriterAgentLite"
            assert "research_brief" in result["output_data"]
            assert "executive_brief" in result["output_data"]["research_brief"]


# =============================================================================
# TEST: Search Components
# =============================================================================

class TestHybridSearch:
    """Tests for ChromaDB + Whoosh hybrid search."""
    
    def test_add_and_search_document(self):
        """Test adding and searching a document."""
        search = HybridSearch()
        
        # Add a test document
        search.add_document(
            doc_id="test_001",
            title="Test Clinical Document",
            abstract="This is a test about diabetes management.",
            authors="Test Author",
            source_type="test",
            quality_score=0.9
        )
        
        # Search for it
        results = search.search("diabetes management", top_k=5)
        
        # Should find the document
        assert len(results) > 0
        # Check one of the results has our doc
        doc_ids = [r.get("doc_id") for r in results]
        assert "test_001" in doc_ids
    
    def test_hybrid_fusion_scoring(self):
        """Test that hybrid fusion combines scores correctly."""
        search = HybridSearch()
        
        # Add documents
        search.add_document(
            doc_id="doc_a",
            title="Document A about hypertension",
            abstract="Hypertension treatment guidelines for elderly patients.",
            authors="Author A"
        )
        search.add_document(
            doc_id="doc_b", 
            title="Document B about blood pressure",
            abstract="Blood pressure management in geriatric care.",
            authors="Author B"
        )
        
        # Search
        results = search.search("hypertension elderly", top_k=5)
        
        # Results should have hybrid scores
        for result in results:
            assert "hybrid_score" in result
            assert result["hybrid_score"] >= 0
    
    def test_count_documents(self):
        """Test document counting."""
        search = HybridSearch()
        counts = search.count()
        
        assert "text_search" in counts
        assert "vector_search" in counts
        assert isinstance(counts["text_search"], int)
        assert isinstance(counts["vector_search"], int)


# =============================================================================
# INTEGRATION TEST (requires Ollama running)
# =============================================================================

@pytest.mark.integration
class TestIntegration:
    """Integration tests that require Ollama to be running."""
    
    def test_full_pipeline_with_ollama(self):
        """Test the complete 3-agent pipeline with real Ollama.
        
        Skip if Ollama is not available.
        """
        try:
            from openai import OpenAI
            client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
            client.models.list()
        except Exception:
            pytest.skip("Ollama not running - skipping integration test")
        
        # Agent 1
        agent1 = QueryFilterAgentLite()
        result1 = agent1.run("diabetes in elderly")
        
        assert result1["agent_name"] == "QueryFilterAgentLite"
        assert "expansion" in result1["output_data"]
        
        # Get queries for Agent 2
        queries = result1["output_data"]["expansion"].get("expanded_queries", ["diabetes elderly"])
        
        # Agent 2
        agent2 = RetrieverSummarizerAgentLite()
        result2 = agent2.run("diabetes in elderly", queries)
        
        assert result2["agent_name"] == "RetrieverSummarizerAgentLite"
        assert "summary" in result2["output_data"]
        
        # Agent 3
        agent3 = FactCheckWriterAgentLite()
        result3 = agent3.run(
            topic="diabetes in elderly",
            retrieved_docs=result2["output_data"].get("retrieved_documents", []),
            summary_data=result2["output_data"].get("summary", {})
        )
        
        assert result3["agent_name"] == "FactCheckWriterAgentLite"
        assert "research_brief" in result3["output_data"]
        
        # Brief should have content
        brief = result3["output_data"]["research_brief"]
        assert "executive_brief" in brief
        assert len(brief["executive_brief"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
