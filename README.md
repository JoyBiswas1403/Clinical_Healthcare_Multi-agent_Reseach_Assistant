# Clinical Guideline Research Assistant

A production-ready 3-agent multi-agent system for healthcare clinical guideline research briefs with full provenance tracking.

## 🎯 Key Features

- **💰 100% FREE Operation**: Uses Ollama (local LLM) - zero API costs
- **⚡ Fast Execution**: ~25 seconds for full 3-agent pipeline
- **🏗️ Production Ready**: Docker Compose infrastructure with 10+ services
- **📊 Full Observability**: Prometheus metrics, Jaeger tracing, Temporal workflows
- **🔄 Flexible LLM**: Switch between Ollama (free) and OpenAI (paid)
- **🪟 Windows Support**: Tested on Windows with Python 3.11

## 💰 Cost Comparison

| LLM Option | Cost per Query | Speed | Quality |
|------------|----------------|-------|---------|
| **Ollama (llama3.2:3b)** | $0.00 | ~25s | Good |
| OpenAI (gpt-4o-mini) | ~$0.03 | ~20s | Excellent |
| OpenAI (gpt-4-turbo) | ~$0.15 | ~25s | Best |

## Architecture

### Three-Agent Pipeline

1. **Query+Filter Agent**: Policy-aware search query expansion and domain vetting
2. **Retriever+Summarizer Agent**: Hybrid BM25+vector retrieval with hierarchical summarization
3. **Fact-Check+Writer Agent**: Claim-level verification, inline citations, and traceability appendix

### Tech Stack

- **Gateway**: FastAPI
- **Orchestration**: Temporal/Celery
- **Search**: Elasticsearch (BM25)
- **Vector DB**: Milvus/Weaviate
- **Storage**: MinIO/S3 + PostgreSQL
- **Parsing**: PyMuPDF, Unstructured
- **Observability**: Prometheus, Jaeger, OpenTelemetry

## Deliverables

Each research request generates:
- **Executive Brief**: ≤300 words with inline citations
- **Source List**: DOIs, URLs, publication metadata
- **Risk Flags**: Contradictions, contraindications, study quality issues
- **Traceability Appendix**: Every claim mapped to source passages

## Prerequisites

### Required
- Docker Desktop (for infrastructure services)
- Python 3.11+ (other versions may have dependency issues)
- Git (for cloning repository)

### Choose One LLM Option
- **Option A (Recommended)**: Ollama installed locally - [Download](https://ollama.com/)
- **Option B**: OpenAI API key with credits - [Get Key](https://platform.openai.com/api-keys)

### System Requirements
- RAM: 8GB minimum (16GB recommended for Ollama)
- Disk: 5GB free space (3GB for Ollama model + 2GB for Docker images)
- OS: Windows 10/11, macOS, or Linux

## Quick Start

### Option A: FREE with Ollama (Recommended)

**Windows:**
```cmd
# 1. Install Ollama
winget install Ollama.Ollama

# 2. Pull LLM model
ollama pull llama3.2:3b

# 3. Start Ollama (keep running in separate window)
ollama serve

# 4. Clone and navigate to project
git clone https://github.com/JoyBiswas1403/Clinical_Healthcare_Multi-agent_Reseach_Assistant.git
cd Clinical_Healthcare_Multi-agent_Reseach_Assistant

# 5. Copy environment template
copy .env.example .env

# 6. Start infrastructure
docker-compose up -d

# 7. Install dependencies (use Python 3.11)
python -m pip install -r requirements.txt

# 8. Run demo
python demo_full_pipeline.py
```

**Linux/macOS:**
```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull LLM model
ollama pull llama3.2:3b

# 3. Start Ollama (keep running in separate window)
ollama serve

# 4. Clone and navigate to project
git clone https://github.com/JoyBiswas1403/Clinical_Healthcare_Multi-agent_Reseach_Assistant.git
cd Clinical_Healthcare_Multi-agent_Reseach_Assistant

# 5. Copy environment template
cp .env.example .env

# 6. Start infrastructure
docker-compose up -d

# 7. Install dependencies
pip install -r requirements.txt

# 8. Run demo
python demo_full_pipeline.py
```

### Option B: Using OpenAI (Requires API key, costs money)

Edit `.env` and add your OpenAI API key:
```bash
OPENAI_API_KEY=sk-your-actual-key-here
```

Then follow steps 4-8 above (skip Ollama installation).

## Testing

```bash
# Quick demo (instant)
python demo_quick.py

# Full 3-agent pipeline (~25 seconds)
python demo_full_pipeline.py

# Single agent test
python test_with_ollama.py

# Start production API server
python -m uvicorn api.main:app --reload --port 8000
```

## API Usage

```bash
curl -X POST http://localhost:8000/api/v1/research \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "hypertension management in elderly patients",
    "max_sources": 15,
    "quality_threshold": 0.7
  }'
```

## Project Structure

```
├── agents/              # Three agent implementations
├── api/                 # FastAPI gateway
├── orchestration/       # Temporal workflows
├── data/                # Schemas, models, repositories
├── config/              # Configuration management
├── docker/              # Dockerfiles and compose
├── docs/                # Additional documentation
├── tests/               # Test suite
└── scripts/             # Utilities and migrations
```

## Development

```bash
# Run tests
pytest tests/ -v

# Type checking
mypy agents/ api/ orchestration/

# Linting
ruff check .

# Format
ruff format .
```

## KPIs & Monitoring

- **Retrieval Recall@10**: Target >0.85
- **Fact-Check Precision**: Target >0.95
- **Brief Quality Score**: Target >4.2/5
- **Latency P95**: Target <45s end-to-end

Metrics exposed at `/metrics` endpoint.

## Security

- API key authentication
- Rate limiting (100 req/hour per key)
- PII detection and redaction
- Audit logging for all requests

## License

MIT
