"""
Tests for FastAPI Web Endpoints.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "mcp_server" in data
    assert "llm_engine" in data
    assert data["llm_engine"]["zero_cost"] is True


@pytest.mark.asyncio
async def test_query_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "question": "Compare RAG and fine-tuning for a university chatbot.",
            "max_subtasks": 3,
            "use_baseline": False
        }
        response = await ac.post("/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data
    assert "answer" in data
    assert "metrics" in data
    assert len(data["evidence"]) > 0
    assert data["metrics"]["groundedness"] >= 0.80


@pytest.mark.asyncio
async def test_query_baseline_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "question": "Compare RAG and fine-tuning for a university chatbot.",
            "use_baseline": True
        }
        response = await ac.post("/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data
    assert data["run_id"].startswith("baseline-")
