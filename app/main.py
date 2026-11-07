"""
FastAPI Application Server
Exposes research query workflow, metrics, health, evaluation suite,
and serves the interactive frontend dashboard.
"""

import datetime
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.evaluation.runner import run_full_evaluation
from app.llm_engine import llm_engine
from app.mcp_client.client import mcp_client
from app.orchestrator import orchestrator
from app.schemas.models import QueryRequest, QueryResponse, RunMetrics

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
RESULTS_DIR = BASE_DIR / "results"
DOCS_DIR = BASE_DIR / "data" / "documents"

app = FastAPI(
    title="Multi-Agent Research Assistant (MCP)",
    version="1.0.0",
    description="Academic Multi-Agent System using the Model Context Protocol (MCP) for Grounded Research",
)

# Enable CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount frontend static assets if directory exists
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/health", tags=["System"])
async def health_check() -> Dict[str, Any]:
    """Health status check and deployment inspection."""
    mcp_tools = []
    try:
        mcp_tools = await mcp_client.list_available_tools()
        mcp_healthy = len(mcp_tools) > 0
    except Exception:
        mcp_healthy = False

    ollama_ok = llm_engine.is_ollama_available()
    doc_count = len(list(DOCS_DIR.glob("*.json"))) if DOCS_DIR.exists() else 0

    return {
        "status": "healthy" if mcp_healthy else "degraded",
        "timestamp": datetime.datetime.now().isoformat(),
        "mcp_server": {
            "status": "connected" if mcp_healthy else "unavailable",
            "available_tools": mcp_tools,
            "tool_count": len(mcp_tools),
        },
        "llm_engine": {
            "mode": "ollama" if ollama_ok else "deterministic",
            "model": llm_engine.model if ollama_ok else "deterministic-rules-v1",
            "ollama_available": ollama_ok,
            "zero_cost": True,
        },
        "corpus": {
            "documents_indexed": doc_count,
            "storage_path": str(DOCS_DIR),
        },
    }


@app.post("/query", response_model=QueryResponse, tags=["Research"])
async def run_query(payload: QueryRequest) -> QueryResponse:
    """Execute a research question through the Multi-Agent MCP workflow or Baseline."""
    clean_q = payload.question.strip()
    if not clean_q:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question parameter must not be empty.",
        )

    if payload.use_baseline:
        state = await orchestrator.execute_baseline(clean_q)
    else:
        state = await orchestrator.execute_query(
            question=clean_q, max_subtasks=payload.max_subtasks
        )

    metrics = RunMetrics(
        latency_ms=state.latency_ms,
        cost_usd=state.estimated_cost_usd,
        total_tokens=state.input_tokens + state.output_tokens,
        input_tokens=state.input_tokens,
        output_tokens=state.output_tokens,
        groundedness=state.groundedness,
        hallucination_rate=state.hallucination_rate,
        citation_correctness=state.citation_correctness,
        evidence_coverage=state.evidence_coverage,
        tool_success_rate=1.0 if not state.mcp_calls else sum(1 for c in state.mcp_calls if c.success) / len(state.mcp_calls),
        tool_calls=state.tool_calls,
    )

    return QueryResponse(
        run_id=state.run_id,
        question=state.question,
        answer=state.final_answer,
        claims=state.claims,
        evidence=state.evidence,
        metrics=metrics,
        agents=state.agents,
        llm_mode=state.llm_mode,
        model_name=state.model_name,
    )


@app.get("/metrics/{run_id}", tags=["Audit"])
async def get_run_metrics(run_id: str) -> Dict[str, Any]:
    """Retrieve full execution state, agent logs, and audit trail for a specific run."""
    clean_id = run_id.strip()
    run_file = RESULTS_DIR / "runs" / f"{clean_id}.json"
    if not run_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run ID '{run_id}' not found in audit logs.",
        )

    with open(run_file, "r", encoding="utf-8") as f:
        return json.load(f)


@app.post("/evaluation/run", tags=["Evaluation"])
async def trigger_evaluation() -> Dict[str, Any]:
    """Execute the full 36-test benchmark suite across Multi-Agent and Baseline."""
    summary = await run_full_evaluation()
    return summary


@app.get("/evaluation/results", tags=["Evaluation"])
async def get_evaluation_results() -> Dict[str, Any]:
    """Fetch previously persisted evaluation metrics and comparison summary."""
    results_json = RESULTS_DIR / "evaluation_results.json"
    if not results_json.exists():
        return {
            "status": "not_run",
            "message": "Evaluation suite has not been executed yet. Call POST /evaluation/run to execute.",
        }

    with open(results_json, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/", response_class=HTMLResponse, tags=["Frontend"])
async def serve_index():
    """Serve the interactive frontend dashboard."""
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return HTMLResponse("<h1>Multi-Agent MCP Server</h1><p>Visit /docs for Swagger API documentation.</p>")
