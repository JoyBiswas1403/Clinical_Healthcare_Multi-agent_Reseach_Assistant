# =============================================================================
# Clinical Guideline Research Assistant
# Copyright (c) 2024. MIT License. See LICENSE file for details.
# =============================================================================
"""Quick demo that runs the REAL 3-agent pipeline.

This replaces the old fake demo with actual Ollama-powered agents.
Shows the full pipeline: Query Expansion → Search → Write Brief

Usage:
    python demo_quick.py
    python demo_quick.py "your research topic"
"""
import sys
import json
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.query_filter_agent_lite import QueryFilterAgentLite
from agents.retriever_summarizer_agent_lite import RetrieverSummarizerAgentLite
from agents.fact_check_writer_agent_lite import FactCheckWriterAgentLite
from data.search_lite import HybridSearch


def print_box(text: str, char: str = "="):
    """Print text in a box."""
    width = 70
    print(f"\n{char * width}")
    print(f"  {text}")
    print(f"{char * width}")


def print_section(title: str, emoji: str = "▶"):
    """Print a section header."""
    print(f"\n{emoji} {title}")
    print("-" * 50)


def format_brief(brief_text: str, max_width: int = 68) -> str:
    """Format brief text with word wrapping."""
    words = brief_text.split()
    lines = []
    current_line = []
    current_length = 0
    
    for word in words:
        if current_length + len(word) + 1 <= max_width:
            current_line.append(word)
            current_length += len(word) + 1
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
            current_length = len(word)
    
    if current_line:
        lines.append(" ".join(current_line))
    
    return "\n".join(lines)


def check_prerequisites():
    """Check if Ollama is running and documents are indexed."""
    # Check Ollama
    try:
        from openai import OpenAI
        client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
        client.models.list()
    except Exception as e:
        print("\n❌ Ollama is not running!")
        print("   Start it with: ollama serve")
        print("   Then pull a model: ollama pull llama3.2:3b")
        return False
    
    # Check documents
    search = HybridSearch()
    counts = search.count()
    if counts["vector_search"] == 0:
        print("\n❌ No documents indexed!")
        print("   Run: python scripts/ingest.py")
        return False
    
    print(f"✓ Ollama running")
    print(f"✓ {counts['vector_search']} documents indexed")
    return True


def run_demo(topic: str = None):
    """Run the full 3-agent demo."""
    
    if topic is None:
        topic = "diabetes management in elderly patients"
    
    print_box("🏥 CLINICAL GUIDELINE RESEARCH ASSISTANT", "=")
    print(f"\n📋 Topic: {topic}")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"💰 Cost: $0.00 (FREE with Ollama!)")
    
    print("\n🔧 Checking prerequisites...")
    if not check_prerequisites():
        return None
    
    start_time = time.time()
    
    # =========================================================================
    # AGENT 1: Query Expansion
    # =========================================================================
    print_section("AGENT 1: Query+Filter", "🔍")
    print("   Expanding query with MeSH terms...")
    
    agent1 = QueryFilterAgentLite()
    result1 = agent1.run(topic)
    
    expansion = result1.get("output_data", {}).get("expansion", {})
    queries = expansion.get("expanded_queries", [topic])
    mesh_terms = expansion.get("mesh_terms", [])
    
    print(f"   ✓ Generated {len(queries)} search queries")
    if mesh_terms:
        print(f"   ✓ MeSH terms: {', '.join(mesh_terms[:4])}")
    
    # =========================================================================
    # AGENT 2: Retrieval + Summarization  
    # =========================================================================
    print_section("AGENT 2: Retriever+Summarizer", "📚")
    print("   Searching documents (BM25 + Vector)...")
    
    agent2 = RetrieverSummarizerAgentLite()
    result2 = agent2.run(topic=topic, expanded_queries=queries)
    
    docs = result2.get("output_data", {}).get("retrieved_documents", [])
    summary = result2.get("output_data", {}).get("summary", {})
    
    print(f"   ✓ Found {len(docs)} relevant documents")
    if summary.get("contradictions"):
        print(f"   ⚠ Detected {len(summary['contradictions'])} contradiction(s)")
    
    # =========================================================================
    # AGENT 3: Fact-Check + Write
    # =========================================================================
    print_section("AGENT 3: Fact-Check+Writer", "✍️")
    print("   Writing executive brief with citations...")
    
    agent3 = FactCheckWriterAgentLite()
    result3 = agent3.run(topic=topic, retrieved_docs=docs, summary_data=summary)
    
    brief = result3.get("output_data", {}).get("research_brief", {})
    brief_text = brief.get("executive_brief", "No brief generated.")
    sources = brief.get("sources", [])
    risk_flags = brief.get("risk_flags", [])
    
    print(f"   ✓ Generated {brief.get('word_count', 0)} word brief")
    print(f"   ✓ {len(sources)} sources cited")
    print(f"   ✓ {len(risk_flags)} risk flags")
    
    total_time = time.time() - start_time
    
    # =========================================================================
    # OUTPUT: Executive Brief
    # =========================================================================
    print_box("📄 EXECUTIVE BRIEF", "=")
    print()
    print(format_brief(brief_text))
    
    # =========================================================================
    # OUTPUT: Sources
    # =========================================================================
    print_box("📚 SOURCES", "-")
    for i, src in enumerate(sources[:5], 1):
        title = src.get("title", "Unknown")[:55]
        print(f"   [{i}] {title}...")
    
    # =========================================================================
    # OUTPUT: Risk Flags
    # =========================================================================
    if risk_flags:
        print_box("⚠️  RISK FLAGS", "-")
        for flag in risk_flags[:3]:
            severity = flag.get("severity", "").upper()
            desc = flag.get("description", "")[:60]
            print(f"   [{severity}] {desc}...")
    
    # =========================================================================
    # OUTPUT: Metrics
    # =========================================================================
    print_box("📊 METRICS", "-")
    print(f"   • Total time: {total_time:.1f} seconds")
    print(f"   • Documents searched: {len(docs)}")
    print(f"   • Sources cited: {len(sources)}")
    print(f"   • Cost: $0.00 (FREE!)")
    
    print("\n" + "=" * 70)
    print("  ✅ Demo complete! This was generated by REAL AI agents.")
    print("=" * 70 + "\n")
    
    return {
        "topic": topic,
        "brief": brief,
        "sources": sources,
        "risk_flags": risk_flags,
        "time_seconds": total_time
    }


def main():
    """Main entry point."""
    topic = None
    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:])
    
    result = run_demo(topic)
    
    if result:
        # Save output
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        filename = f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_dir / filename, "w") as f:
            json.dump(result, f, indent=2, default=str)
        
        print(f"💾 Results saved to: output/{filename}")


if __name__ == "__main__":
    main()
