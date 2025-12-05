# Getting Started Guide

## Prerequisites

- **Python 3.10+**
- **Ollama** ([download here](https://ollama.ai))

That's it! No Docker, no cloud accounts, no API keys needed.

## Quick Start (5 minutes)

### Step 1: Clone & Install

```bash
cd clinical-guideline-assistant
pip install -r requirements.txt
```

### Step 2: Install Ollama & Pull Model

```bash
# Download Ollama from https://ollama.ai
# Then pull a model:
ollama pull llama3.2:3b
```

### Step 3: Index Sample Documents

```bash
python scripts/ingest.py
```

This indexes 10 sample clinical documents into the search system.

### Step 4: Run Demo

```bash
python demo_quick.py "diabetes management in elderly patients"
```

You should see output like:
```
🏥 CLINICAL GUIDELINE RESEARCH ASSISTANT
======================================================================

📋 Topic: diabetes management in elderly patients
⏰ Time: 2024-01-15 10:30:45
💰 Cost: $0.00 (FREE with Ollama!)

🔍 AGENT 1: Query+Filter
--------------------------------------------------
   ✓ Generated 3 search queries
   ✓ MeSH terms: Diabetes Mellitus, Aged, Blood Glucose

📚 AGENT 2: Retriever+Summarizer
--------------------------------------------------
   ✓ Found 8 relevant documents
   ⚠ Detected 1 contradiction(s)

✍️ AGENT 3: Fact-Check+Writer
--------------------------------------------------
   ✓ Generated 287 word brief
   ✓ 5 sources cited
   ✓ 2 risk flags

📄 EXECUTIVE BRIEF
======================================================================
Diabetes management in elderly patients requires careful individualization
to balance glycemic control with safety [1]. Current guidelines recommend
HbA1c targets between 7.0-8.0% for most patients aged 65 and older [1][2]...
```

## Project Structure

```
├── demo_quick.py           # Quick demo - start here!
├── run_local.py            # Full pipeline with detailed output
├── scripts/
│   └── ingest.py           # Index documents
├── agents/                 # 3 AI agents
├── data/                   # Search & storage
└── config/                 # Settings
```

## Common Commands

```bash
# Run quick demo
python demo_quick.py "your topic"

# Run with full output
python run_local.py "your topic"

# Re-index documents
python scripts/ingest.py

# Run tests
pytest tests/test_agents_lite.py -v

# Check indexed document count
python -c "from data.search_lite import HybridSearch; print(HybridSearch().count())"
```

## Adding Your Own Documents

```python
from data.search_lite import HybridSearch

search = HybridSearch()
search.add_document(
    doc_id="my_doc_001",
    title="My Clinical Guideline",
    abstract="Content of the document...",
    authors="Smith J, Jones K",
    source_type="clinical_guideline",
    quality_score=0.9
)

# Verify
print(search.count())
```

## Changing the LLM Model

Edit `config/settings_lite.py`:

```python
# Faster, smaller model
ollama_model: str = "llama3.2:1b"

# Better quality (requires more RAM)
ollama_model: str = "llama3.1:8b"

# Alternative model
ollama_model: str = "mistral"
```

Then pull the model:
```bash
ollama pull <model_name>
```

## Troubleshooting

### "Cannot connect to Ollama"
```bash
# Make sure Ollama is running
ollama serve

# In another terminal, run your command
python demo_quick.py "test"
```

### "No documents found"
```bash
# Re-index sample documents
python scripts/ingest.py

# Check count
python -c "from data.search_lite import HybridSearch; print(HybridSearch().count())"
```

### Slow first run
The first run downloads embedding models (~90MB). Subsequent runs are faster.

## Next Steps

1. **Read the architecture**: `docs/ARCHITECTURE.md`
2. **Add your own documents**: Use the ingestion example above
3. **Customize prompts**: Edit `agents/*_lite.py` files
4. **Run tests**: `pytest tests/ -v`

## Support

- Check `docs/ARCHITECTURE.md` for system design
- Review agent code in `agents/` directory
- Open an issue on GitHub for bugs
