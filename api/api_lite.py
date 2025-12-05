# =============================================================================
# Clinical Guideline Research Assistant
# Copyright (c) 2024. MIT License. See LICENSE file for details.
# =============================================================================
"""FastAPI backend for the web UI.

Provides a simple REST API for the research pipeline.
Run with: python api/api_lite.py
"""
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from agents.query_filter_agent_lite import QueryFilterAgentLite
from agents.retriever_summarizer_agent_lite import RetrieverSummarizerAgentLite
from agents.fact_check_writer_agent_lite import FactCheckWriterAgentLite
from utils.audit_logger import log_request
from utils.rate_limiter import get_rate_limiter


# Frontend files - hardcoded absolute paths
FRONTEND_DIR = Path("e:/Projects/clinical-guideline-assistant/frontend")

# FastAPI app
app = FastAPI(
    title="Clinical Guideline Research API",
    description="AI-powered clinical research briefs",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class ResearchRequest(BaseModel):
    topic: str
    max_sources: int = 10


class ResearchResponse(BaseModel):
    topic: str
    research_brief: dict
    metrics: dict


# Lazy load agents
_agents = {}

def get_agents():
    if not _agents:
        _agents['query'] = QueryFilterAgentLite()
        _agents['retriever'] = RetrieverSummarizerAgentLite()
        _agents['writer'] = FactCheckWriterAgentLite()
    return _agents


# =============================================================================
# ROUTES
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serve the main HTML page."""
    html_file = FRONTEND_DIR / "index.html"
    if html_file.exists():
        return HTMLResponse(content=html_file.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Frontend not found</h1>", status_code=404)


@app.get("/style.css")
async def serve_css():
    """Serve CSS file."""
    css_file = FRONTEND_DIR / "style.css"
    if css_file.exists():
        return FileResponse(str(css_file), media_type="text/css")
    raise HTTPException(status_code=404, detail="CSS not found")


@app.get("/app.js")
async def serve_js():
    """Serve JavaScript file."""
    js_file = FRONTEND_DIR / "app.js"
    if js_file.exists():
        return FileResponse(str(js_file), media_type="application/javascript")
    raise HTTPException(status_code=404, detail="JS not found")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


@app.post("/api/research", response_model=ResearchResponse)
async def research(request: ResearchRequest):
    """Run the 3-agent research pipeline."""
    start_time = time.time()
    
    # Rate limiting
    limiter = get_rate_limiter()
    allowed, error = limiter.check_and_record("global")
    if not allowed:
        log_request(
            endpoint="/api/research",
            method="POST",
            topic=request.topic,
            status_code=429,
            error=error
        )
        raise HTTPException(status_code=429, detail=error)
    
    try:
        agents = get_agents()
        
        # Agent 1: Query Expansion
        result1 = agents['query'].run(request.topic)
        expansion = result1.get("output_data", {}).get("expansion", {})
        queries = expansion.get("expanded_queries", [request.topic])
        
        # Agent 2: Retrieval + Summarization
        result2 = agents['retriever'].run(
            topic=request.topic,
            expanded_queries=queries,
            top_k=request.max_sources
        )
        retrieved_docs = result2.get("output_data", {}).get("retrieved_documents", [])
        summary = result2.get("output_data", {}).get("summary", {})
        
        # Agent 3: Fact-Check + Write
        result3 = agents['writer'].run(
            topic=request.topic,
            retrieved_docs=retrieved_docs,
            summary_data=summary
        )
        research_brief = result3.get("output_data", {}).get("research_brief", {})
        
        total_time = time.time() - start_time
        
        response = ResearchResponse(
            topic=request.topic,
            research_brief=research_brief,
            metrics={
                "total_time_seconds": total_time,
                "agent1_time_ms": result1.get("execution_time_ms", 0),
                "agent2_time_ms": result2.get("execution_time_ms", 0),
                "agent3_time_ms": result3.get("execution_time_ms", 0),
                "documents_retrieved": len(retrieved_docs)
            }
        )
        
        # Log success
        log_request(
            endpoint="/api/research",
            method="POST",
            topic=request.topic,
            status_code=200,
            response_time_ms=total_time * 1000
        )
        
        return response
        
    except Exception as e:
        log_request(
            endpoint="/api/research",
            method="POST",
            topic=request.topic,
            status_code=500,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("  Clinical Guideline Research API")
    print("=" * 60)
    print(f"  Frontend: {FRONTEND_DIR}")
    print(f"  Exists: {FRONTEND_DIR.exists()}")
    print()
    print("  Open http://localhost:8888 in your browser")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8888)
