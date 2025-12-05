# Architecture Documentation

## System Overview

The Clinical Guideline Research Assistant is a **3-agent multi-agent system** that generates evidence-based research briefs from clinical literature.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         CLINICAL RESEARCH PIPELINE                           │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   User Query                                                                 │
│       │                                                                      │
│       ▼                                                                      │
│   ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐       │
│   │   AGENT 1       │────▶│   AGENT 2       │────▶│   AGENT 3       │       │
│   │ Query+Filter    │     │ Retriever+      │     │ Fact-Check+     │       │
│   │                 │     │ Summarizer      │     │ Writer          │       │
│   └────────┬────────┘     └────────┬────────┘     └────────┬────────┘       │
│            │                       │                       │                │
│            ▼                       ▼                       ▼                │
│   ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐       │
│   │ • MeSH Terms    │     │ • Hybrid Search │     │ • Fact Checking │       │
│   │ • Query         │     │   (BM25+Vector) │     │ • Brief Writing │       │
│   │   Expansion     │     │ • Reranking     │     │ • Risk Flags    │       │
│   │ • Domain Vet    │     │ • Summarization │     │ • Traceability  │       │
│   └─────────────────┘     └─────────────────┘     └─────────────────┘       │
│                                                                              │
│       ▼                                                                      │
│   Research Brief + Sources + Risk Flags + Traceability                       │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Technology Stack (100% FREE)

```
┌─────────────────────────────────────────────────────────────────┐
│                        APPLICATION LAYER                         │
├─────────────────────────────────────────────────────────────────┤
│  demo_quick.py / run_local.py                                    │
│  ├── QueryFilterAgentLite      (query expansion)                │
│  ├── RetrieverSummarizerAgentLite (search + summarize)          │
│  └── FactCheckWriterAgentLite  (verify + write)                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        INTELLIGENCE LAYER                        │
├─────────────────────────────────────────────────────────────────┤
│  Ollama (Local LLM)                                              │
│  ├── llama3.2:3b (default)                                      │
│  ├── mistral (alternative)                                       │
│  └── OpenAI-compatible API at localhost:11434                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        SEARCH & STORAGE                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  ChromaDB   │  │   Whoosh    │  │ Reranker    │              │
│  │  (Vectors)  │  │  (BM25)     │  │ (CrossEnc)  │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│                           │                                      │
│                           ▼                                      │
│  ┌──────────────────────────────────────────────┐               │
│  │              HybridSearch                     │               │
│  │   Reciprocal Rank Fusion + Cross-Encoder     │               │
│  └──────────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                                │
├─────────────────────────────────────────────────────────────────┤
│  data_store/                                                     │
│  ├── chroma/          (vector embeddings)                       │
│  ├── whoosh_index/    (full-text index)                         │
│  ├── audit.db         (request logs)                            │
│  └── documents/       (source files)                            │
└─────────────────────────────────────────────────────────────────┘
```

## Agent Details

### Agent 1: Query+Filter

**Purpose**: Transform user query into optimized search terms

**Input**: Research topic (e.g., "diabetes management in elderly")

**Output**:
- Expanded search queries
- MeSH terms
- Synonyms
- Exclusion criteria
- Source type priorities

**Technology**: Ollama LLM with structured JSON output

### Agent 2: Retriever+Summarizer

**Purpose**: Find and synthesize relevant documents

**Pipeline**:
1. **Hybrid Search**: BM25 (Whoosh) + Vector (ChromaDB)
2. **Fusion**: Reciprocal Rank Fusion (RRF)
3. **Reranking**: Cross-encoder (ms-marco-MiniLM)
4. **Summarization**: Hierarchical with contradiction detection

**Output**:
- Retrieved documents with relevance scores
- Synthesis of key findings
- Contradiction detection
- Quality assessment

### Agent 3: Fact-Check+Writer

**Purpose**: Verify claims and generate executive brief

**Pipeline**:
1. **Brief Writing**: ≤300 words with inline citations
2. **Risk Assessment**: Identify contradictions, contraindications
3. **Traceability**: Map claims to source passages

**Output**:
- Executive brief with [1][2][3] citations
- Source list with metadata
- Risk flags (severity: high/medium/low)
- Traceability appendix

## Data Flow

```
 ┌──────────┐
 │  User    │
 └────┬─────┘
      │ "diabetes management elderly"
      ▼
 ┌──────────────────────────────────────────────────────────────┐
 │                        Agent 1                                │
 │  ┌────────────────────────────────────────────────────────┐  │
 │  │ LLM: "Generate MeSH terms and expanded queries"        │  │
 │  └────────────────────────────────────────────────────────┘  │
 │  Output: ["diabetes mellitus AND elderly", "glycemic..."]   │
 └──────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
 ┌──────────────────────────────────────────────────────────────┐
 │                        Agent 2                                │
 │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │
 │  │ BM25 Search │  │Vector Search│  │ Cross-Encoder Rerank│   │
 │  │   (Whoosh)  │  │ (ChromaDB)  │  │ (sentence-transf.)  │   │
 │  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘   │
 │         └────────┬───────┘                    │               │
 │                  ▼                            │               │
 │         ┌─────────────┐                       │               │
 │         │ RRF Fusion  │───────────────────────┘               │
 │         └─────────────┘                                       │
 │  Output: [doc1, doc2, doc3, ...] with scores                  │
 └──────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
 ┌──────────────────────────────────────────────────────────────┐
 │                        Agent 3                                │
 │  ┌────────────────────────────────────────────────────────┐  │
 │  │ LLM: "Write brief with citations, assess risks"        │  │
 │  └────────────────────────────────────────────────────────┘  │
 │  Output:                                                      │
 │    • Executive Brief (≤300 words)                            │
 │    • Sources [1] [2] [3]                                     │
 │    • Risk Flags                                               │
 │    • Traceability                                             │
 └──────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
                         ┌──────────┐
                         │ Research │
                         │  Brief   │
                         └──────────┘
```

## File Structure

```
clinical-guideline-assistant/
├── agents/                          # 3 Agent implementations
│   ├── __init__.py
│   ├── query_filter_agent_lite.py   # Agent 1
│   ├── retriever_summarizer_agent_lite.py  # Agent 2 (with reranker)
│   └── fact_check_writer_agent_lite.py     # Agent 3
│
├── data/                            # Data handling
│   ├── search_lite.py               # ChromaDB + Whoosh hybrid
│   ├── reranker.py                  # Cross-encoder reranking
│   └── models.py                    # Data models
│
├── config/                          # Configuration
│   └── settings_lite.py             # Free-tier settings
│
├── utils/                           # Utilities
│   ├── audit_logger.py              # SQLite logging
│   └── rate_limiter.py              # In-memory rate limiting
│
├── scripts/                         # CLI tools
│   └── ingest.py                    # Document ingestion
│
├── tests/                           # Test suite
│   └── test_agents_lite.py          # Unit + integration tests
│
├── demo_quick.py                    # Quick demo
├── run_local.py                     # Full pipeline demo
└── requirements.txt                 # Dependencies
```

## Performance Characteristics

| Metric | Value |
|--------|-------|
| End-to-end latency | 30-60 seconds |
| Documents indexed | 10 sample docs |
| Retrieval top-k | 20 docs |
| Brief length | ≤300 words |
| Cost per request | $0.00 (FREE) |

## Security Notes

- All processing runs **locally** (no cloud)
- No API keys required for core functionality
- SQLite audit logging for compliance
- Rate limiting prevents abuse
