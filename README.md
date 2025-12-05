# 🏥 Clinical Guideline Research Assistant

[![CI](https://github.com/YOUR_USERNAME/clinical-guideline-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/clinical-guideline-assistant/actions/workflows/ci.yml)

A **FREE**, production-ready multi-agent AI system that generates evidence-based research briefs from clinical literature with full provenance tracking.

![Demo](docs/demo.webp)

> ⚡ **100% FREE** — Uses Ollama (local LLM), ChromaDB, and Whoosh. No paid APIs required!

---

## ✨ Features

- 🤖 **3-Agent Pipeline** — Query expansion → Retrieval → Brief writing
- 🔍 **Hybrid Search** — BM25 + Vector search with cross-encoder reranking
- 📝 **Cited Briefs** — Executive summaries with inline citations [1][2][3]
- ⚠️ **Risk Detection** — Flags contradictions and contraindications
- 🔒 **Full Traceability** — Every claim mapped to source passages
- 🌐 **Web UI** — Modern dark-themed interface
- 💰 **Zero Cost** — Everything runs locally

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- [Ollama](https://ollama.ai) installed

### Setup (5 minutes)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Pull LLM model
ollama pull llama3.2

# 3. Index sample documents
python scripts/ingest.py

# 4. Run demo!
python demo_quick.py "diabetes management in elderly patients"
```

### Web UI

```bash
# Start API server
python api/api_lite.py

# Open browser
# http://localhost:8888
```

---

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   AGENT 1       │────▶│   AGENT 2       │────▶│   AGENT 3       │
│  Query+Filter   │     │  Retriever+     │     │  Fact-Check+    │
│                 │     │  Summarizer     │     │  Writer         │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
   • MeSH Terms            • Hybrid Search         • Fact Checking
   • Query Expansion       • Reranking             • Brief Writing
   • Domain Vetting        • Summarization         • Risk Flags
```

### Tech Stack

| Component | Technology | Cost |
|-----------|------------|------|
| LLM | Ollama (llama3.2) | FREE |
| Vector DB | ChromaDB | FREE |
| Text Search | Whoosh (BM25) | FREE |
| Reranker | Cross-Encoder | FREE |
| API | FastAPI | FREE |
| Frontend | HTML/CSS/JS | FREE |

---

## 📁 Project Structure

```
clinical-guideline-assistant/
├── agents/                     # AI Agents
│   ├── query_filter_agent_lite.py
│   ├── retriever_summarizer_agent_lite.py
│   └── fact_check_writer_agent_lite.py
├── api/
│   └── api_lite.py             # FastAPI backend
├── config/
│   └── settings_lite.py        # Configuration
├── data/
│   ├── search_lite.py          # Hybrid search
│   └── reranker.py             # Cross-encoder
├── frontend/                   # Web UI
│   ├── index.html
│   ├── style.css
│   └── app.js
├── scripts/
│   └── ingest.py               # Document ingestion
├── tests/
│   └── test_agents_lite.py     # Unit tests
├── utils/
│   ├── audit_logger.py         # SQLite logging
│   └── rate_limiter.py         # Rate limiting
├── docs/
│   ├── ARCHITECTURE.md
│   ├── GETTING_STARTED.md
│   └── demo.webp               # Demo video
├── demo_quick.py               # Quick demo
├── run_local.py                # Full pipeline demo
└── requirements.txt
```

---

## 💻 Usage

### CLI Demo

```bash
# Quick demo
python demo_quick.py "hypertension treatment guidelines"

# Full pipeline with detailed output
python run_local.py "diabetes management in elderly patients"
```

### Output Example

```
📄 EXECUTIVE BRIEF
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Diabetes management in elderly patients requires careful individualization
to balance glycemic control with safety [1]. Current guidelines recommend
HbA1c targets between 7.0-8.0% for most patients aged 65+ [1][2]...

📚 SOURCES
   [1] Diabetes Management in Elderly: Updated Guidelines 2023
   [2] SGLT2 Inhibitors: Benefits and Risks in Geriatric Populations

⚠️ RISK FLAGS
   [MEDIUM] SGLT2 inhibitors require monitoring for dehydration in elderly

📊 METRICS
   • Time: 45.2 seconds
   • Documents: 8
   • Cost: $0.00
```

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Test imports
python -c "from agents import QueryFilterAgentLite; print('OK')"
```

---

## ⚙️ Configuration

Edit `config/settings_lite.py`:

```python
# Change LLM model
ollama_model: str = "llama3.2"  # or "mistral", "tinyllama"

# Adjust temperatures
query_filter_temperature: float = 0.3
writer_temperature: float = 0.5
```

---

## 📝 Adding Documents

```python
from data.search_lite import HybridSearch

search = HybridSearch()
search.add_document(
    doc_id="my_doc_001",
    title="My Clinical Document",
    abstract="Content goes here...",
    authors="Smith J, Jones K",
    source_type="clinical_guideline",
    quality_score=0.9
)
```

---

## 🔐 Security

- ✅ All processing runs **locally**
- ✅ No data sent to external APIs
- ✅ SQLite audit logging
- ✅ Rate limiting built-in

---

## 📄 License

MIT

---

<p align="center">
Built with ❤️ using Ollama, ChromaDB, and Whoosh<br>
<strong>100% FREE — No API keys required!</strong>
</p>
