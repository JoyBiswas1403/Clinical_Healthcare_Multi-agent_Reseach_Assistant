# =============================================================================
# Clinical Guideline Research Assistant
# Copyright (c) 2024. MIT License. See LICENSE file for details.
# =============================================================================
"""Agent 2: Retriever+Summarizer - Using Ollama + ChromaDB + Whoosh (FREE).

Performs hybrid search, reranking, and hierarchical summarization.
"""
import json
import time
from typing import List, Dict, Any
from openai import OpenAI

from config.settings_lite import settings
from data.search_lite import HybridSearch
from data.reranker import rerank_results


SUMMARIZATION_PROMPT = """You are a clinical research summarization expert. Create a hierarchical summary of the following sources.

Topic: {topic}
Sources: {sources}

Create:
1. High-level synthesis (2-3 sentences) - what are the key findings across all sources?
2. Source-level summaries - 1-2 sentences per source highlighting unique contributions
3. Contradiction detection - identify any conflicting findings
4. Quality assessment - note any methodological concerns

Return a JSON object:
{{
  "synthesis": "...",
  "source_summaries": [
    {{
      "source_id": "...",
      "summary": "...",
      "key_findings": ["finding1", "finding2"]
    }}
  ],
  "contradictions": [
    {{
      "claim": "...",
      "conflicting_sources": ["id1", "id2"],
      "severity": "high|medium|low"
    }}
  ],
  "overall_quality": "high|medium|low"
}}

Return ONLY valid JSON, no other text."""


class RetrieverSummarizerAgentLite:
    """Retriever+Summarizer using Ollama + local search (FREE)."""
    
    def __init__(self, use_reranker: bool = True):
        # Ollama for summarization
        self.client = OpenAI(
            base_url=settings.ollama_base_url,
            api_key="ollama"
        )
        self.model = settings.ollama_model
        self.temperature = settings.summarizer_temperature
        
        # Local hybrid search (ChromaDB + Whoosh)
        self.search = HybridSearch()
        
        # Whether to use cross-encoder reranking
        self.use_reranker = use_reranker
    
    def retrieve(
        self,
        queries: List[str],
        topic: str = "",
        top_k: int = 20
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant documents using hybrid search + reranking."""
        all_results = []
        seen_ids = set()
        
        for query in queries:
            results = self.search.search(query, top_k=top_k * 2)  # Get more for reranking
            for result in results:
                if result["doc_id"] not in seen_ids:
                    seen_ids.add(result["doc_id"])
                    all_results.append(result)
        
        # Sort by hybrid score first
        all_results.sort(key=lambda x: x.get("hybrid_score", 0), reverse=True)
        
        # Apply cross-encoder reranking for better quality
        if self.use_reranker and all_results:
            rerank_query = topic if topic else " ".join(queries)
            all_results = rerank_results(rerank_query, all_results, top_k=top_k)
        
        return all_results[:top_k]
    
    def summarize(
        self,
        topic: str,
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create hierarchical summary of retrieved documents."""
        if not documents:
            return {
                "synthesis": "No documents found for this query.",
                "source_summaries": [],
                "contradictions": [],
                "overall_quality": "low"
            }
        
        # Format sources for LLM
        sources_text = []
        for i, doc in enumerate(documents[:10]):  # Limit to 10 for context
            sources_text.append(
                f"Source {i+1} (ID: {doc.get('doc_id', 'unknown')}):\n"
                f"Title: {doc.get('title', 'N/A')}\n"
                f"Abstract: {doc.get('abstract', doc.get('text', 'N/A'))[:500]}..."
            )
        
        prompt = SUMMARIZATION_PROMPT.format(
            topic=topic,
            sources="\n\n".join(sources_text)
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a clinical research summarization expert. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            return json.loads(content)
            
        except Exception as e:
            return {
                "synthesis": f"Error generating summary: {str(e)}",
                "source_summaries": [],
                "contradictions": [],
                "overall_quality": "unknown",
                "error": str(e)
            }
    
    def run(
        self,
        topic: str,
        expanded_queries: List[str],
        top_k: int = 20
    ) -> Dict[str, Any]:
        """Execute hybrid retrieval and summarization pipeline."""
        start_time = time.time()
        errors = []
        metrics = {}
        
        try:
            # Use original topic if no expanded queries
            if not expanded_queries:
                expanded_queries = [topic]
            
            # Step 1: Retrieve documents
            retrieved_docs = self.retrieve(expanded_queries, top_k)
            metrics["retrieved_count"] = len(retrieved_docs)
            
            # Step 2: Summarize
            summary = self.summarize(topic, retrieved_docs)
            
            output_data = {
                "retrieved_documents": retrieved_docs,
                "summary": summary,
                "topic": topic
            }
            
        except Exception as e:
            errors.append(str(e))
            output_data = {"error": str(e), "topic": topic}
        
        execution_time_ms = (time.time() - start_time) * 1000
        
        return {
            "agent_name": "RetrieverSummarizerAgentLite",
            "output_data": output_data,
            "metrics": metrics,
            "errors": errors,
            "execution_time_ms": execution_time_ms
        }


# Quick test
if __name__ == "__main__":
    print("Testing RetrieverSummarizerAgentLite...")
    print("Make sure Ollama is running: ollama serve")
    print()
    
    agent = RetrieverSummarizerAgentLite()
    
    # Check if we have indexed documents
    counts = agent.search.count()
    print(f"Document counts: {counts}")
    
    if counts["vector_search"] == 0:
        print("\nNo documents indexed yet. Run scripts/ingest.py first.")
    else:
        result = agent.run(
            topic="diabetes management in elderly",
            expanded_queries=["diabetes elderly", "glycemic control geriatric"]
        )
        print("Result:")
        print(json.dumps(result, indent=2, default=str))
