# =============================================================================
# Clinical Guideline Research Assistant
# Copyright (c) 2024. MIT License. See LICENSE file for details.
# =============================================================================
"""One-command demo for Clinical Guideline Research Assistant.

Runs the full 3-agent pipeline locally using FREE tools:
- Ollama for LLM (free, local)
- ChromaDB for vectors (free)
- Whoosh for text search (free)

Usage:
    python run_local.py "diabetes management in elderly patients"
"""
import sys
import json
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, ".")

from agents.query_filter_agent_lite import QueryFilterAgentLite
from agents.retriever_summarizer_agent_lite import RetrieverSummarizerAgentLite
from agents.fact_check_writer_agent_lite import FactCheckWriterAgentLite


def print_header(text: str, emoji: str = ""):
    """Print a formatted header."""
    print(f"\n{'='*70}")
    print(f"  {emoji} {text}")
    print(f"{'='*70}")


def print_step(step: int, text: str):
    """Print a step indicator."""
    print(f"\n▶ STEP {step}: {text}")
    print("-" * 50)


def run_pipeline(topic: str, verbose: bool = True):
    """Run the full 3-agent research pipeline.
    
    Args:
        topic: Research topic/query
        verbose: Whether to print progress
    
    Returns:
        Complete research brief dictionary
    """
    start_time = time.time()
    
    if verbose:
        print_header("CLINICAL GUIDELINE RESEARCH ASSISTANT", "🏥")
        print(f"\n📋 Research Topic: {topic}")
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n🔧 Using FREE stack: Ollama + ChromaDB + Whoosh")
    
    # =========================================================================
    # AGENT 1: Query Expansion
    # =========================================================================
    if verbose:
        print_step(1, "Query+Filter Agent (Expanding query)")
        print("   → Generating MeSH terms and optimized queries...")
    
    agent1 = QueryFilterAgentLite()
    agent1_result = agent1.run(topic)
    
    expansion = agent1_result.get("output_data", {}).get("expansion", {})
    expanded_queries = expansion.get("expanded_queries", [topic])
    mesh_terms = expansion.get("mesh_terms", [])
    
    if verbose:
        print(f"   ✓ Generated {len(expanded_queries)} queries")
        print(f"   ✓ Found {len(mesh_terms)} MeSH terms")
        if mesh_terms:
            print(f"   → Terms: {', '.join(mesh_terms[:5])}")
    
    # =========================================================================
    # AGENT 2: Retrieval + Summarization
    # =========================================================================
    if verbose:
        print_step(2, "Retriever+Summarizer Agent (Searching & summarizing)")
        print("   → Hybrid search (BM25 + Vector)...")
    
    agent2 = RetrieverSummarizerAgentLite()
    agent2_result = agent2.run(
        topic=topic,
        expanded_queries=expanded_queries
    )
    
    retrieved_docs = agent2_result.get("output_data", {}).get("retrieved_documents", [])
    summary = agent2_result.get("output_data", {}).get("summary", {})
    
    if verbose:
        print(f"   ✓ Retrieved {len(retrieved_docs)} documents")
        if summary.get("synthesis"):
            print(f"   → Synthesis: {summary['synthesis'][:100]}...")
        if summary.get("contradictions"):
            print(f"   ⚠ Found {len(summary['contradictions'])} contradiction(s)")
    
    # =========================================================================
    # AGENT 3: Fact-Check + Write
    # =========================================================================
    if verbose:
        print_step(3, "Fact-Check+Writer Agent (Verifying & writing)")
        print("   → Generating executive brief with citations...")
    
    agent3 = FactCheckWriterAgentLite()
    agent3_result = agent3.run(
        topic=topic,
        retrieved_docs=retrieved_docs,
        summary_data=summary
    )
    
    research_brief = agent3_result.get("output_data", {}).get("research_brief", {})
    
    if verbose:
        word_count = research_brief.get("word_count", 0)
        num_sources = len(research_brief.get("sources", []))
        num_risks = len(research_brief.get("risk_flags", []))
        print(f"   ✓ Generated brief: {word_count} words")
        print(f"   ✓ {num_sources} sources cited")
        print(f"   ✓ {num_risks} risk flag(s) identified")
    
    # =========================================================================
    # RESULTS
    # =========================================================================
    total_time = time.time() - start_time
    
    if verbose:
        print_header("EXECUTIVE BRIEF", "📄")
        print(research_brief.get("executive_brief", "No brief generated."))
        
        print_header("SOURCES", "📚")
        for source in research_brief.get("sources", [])[:5]:
            print(f"   [{source.get('citation_id')}] {source.get('title', 'Unknown')}")
        
        if research_brief.get("risk_flags"):
            print_header("RISK FLAGS", "⚠️")
            for flag in research_brief.get("risk_flags", []):
                severity = flag.get("severity", "unknown").upper()
                print(f"   [{severity}] {flag.get('description', 'No description')}")
        
        print_header("METRICS", "📊")
        print(f"   • Total time: {total_time:.2f} seconds")
        print(f"   • Agent 1 time: {agent1_result.get('execution_time_ms', 0)/1000:.2f}s")
        print(f"   • Agent 2 time: {agent2_result.get('execution_time_ms', 0)/1000:.2f}s")
        print(f"   • Agent 3 time: {agent3_result.get('execution_time_ms', 0)/1000:.2f}s")
        print(f"   • Documents retrieved: {len(retrieved_docs)}")
        print(f"   • Cost: $0.00 (FREE with Ollama!)")
        
        print("\n" + "="*70 + "\n")
    
    # Return full result
    return {
        "topic": topic,
        "research_brief": research_brief,
        "expansion": expansion,
        "retrieved_documents": retrieved_docs,
        "summary": summary,
        "metrics": {
            "total_time_seconds": total_time,
            "agent1_time_ms": agent1_result.get("execution_time_ms", 0),
            "agent2_time_ms": agent2_result.get("execution_time_ms", 0),
            "agent3_time_ms": agent3_result.get("execution_time_ms", 0),
            "documents_retrieved": len(retrieved_docs)
        }
    }


def main():
    """Main entry point."""
    # Get topic from command line or use default
    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:])
    else:
        topic = "diabetes management in elderly patients"
        print("No topic provided, using default:")
        print(f"  '{topic}'")
        print("\nUsage: python run_local.py \"your research topic\"")
    
    # Check if Ollama is running
    try:
        from openai import OpenAI
        client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
        client.models.list()
    except Exception as e:
        print("\n❌ ERROR: Cannot connect to Ollama")
        print("   Please make sure Ollama is running:")
        print("   1. Install from https://ollama.ai")
        print("   2. Start with: ollama serve")
        print("   3. Pull a model: ollama pull llama3.2:3b")
        print(f"\n   Error: {e}")
        sys.exit(1)
    
    # Run pipeline
    result = run_pipeline(topic)
    
    # Save result to file
    output_file = f"output/research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        import os
        os.makedirs("output", exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"💾 Full results saved to: {output_file}")
    except Exception as e:
        print(f"⚠ Could not save results: {e}")


if __name__ == "__main__":
    main()
