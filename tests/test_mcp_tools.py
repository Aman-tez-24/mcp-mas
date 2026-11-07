"""
Tests for MCP Server Tools: search_sources, get_document, save_evidence, get_run_metrics.
"""

import pytest
from mcp_server.tools import (
    get_document,
    get_run_metrics,
    save_evidence,
    search_sources,
)


def test_search_sources_valid_query():
    res = search_sources("RAG university chatbot", max_results=3)
    assert res["total_matches"] > 0
    assert len(res["results"]) <= 3
    first = res["results"][0]
    assert "document_id" in first
    assert "relevance" in first
    assert "text" in first
    assert first["relevance"] > 0.0


def test_search_sources_empty_query():
    res = search_sources("")
    assert res["total_matches"] == 0
    assert res["results"] == []


def test_get_document_valid():
    res = get_document("DOC-001")
    assert res["success"] is True
    doc = res["document"]
    assert doc["document_id"] == "DOC-001"
    assert "Retrieval-Augmented Generation" in doc["title"]
    assert "content" in doc


def test_get_document_invalid():
    res = get_document("DOC-NONEXISTENT-999")
    assert res["success"] is False
    assert "not found" in res["error"].lower()


def test_save_evidence_and_metrics():
    sample_evidence = [
        {"evidence_id": "E1", "source": "Test Source", "text": "Sample text", "relevance": 0.9}
    ]
    save_res = save_evidence("test-run-pytest-001", sample_evidence)
    assert save_res["success"] is True
    assert save_res["count"] == 1

    # Verify metric retrieval fallback
    metrics_res = get_run_metrics("test-run-pytest-001")
    assert metrics_res["success"] is True
