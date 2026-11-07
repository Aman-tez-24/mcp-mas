"""
Tests for MCP Client Manager: Tool discovery, execution, and error handling.
"""

import pytest
from app.mcp_client.client import mcp_client


@pytest.mark.asyncio
async def test_client_list_tools():
    tools = await mcp_client.list_available_tools()
    assert isinstance(tools, list)
    expected_tools = {"search_sources", "get_document", "calculator", "save_evidence", "get_run_metrics"}
    for exp in expected_tools:
        assert exp in tools, f"Expected tool {exp} not found in client discovery"


@pytest.mark.asyncio
async def test_client_call_calculator_tool():
    res = await mcp_client.call_tool("calculator", {"expression": "25 * 4"})
    assert isinstance(res, dict)
    assert res.get("success") is True
    assert res.get("result") == 100


@pytest.mark.asyncio
async def test_client_call_search_sources_tool():
    res = await mcp_client.call_tool("search_sources", {"query": "fine-tuning LoRA", "max_results": 2})
    assert isinstance(res, dict)
    assert "results" in res
    assert len(res["results"]) > 0


@pytest.mark.asyncio
async def test_client_call_invalid_tool_name():
    res = await mcp_client.call_tool("nonexistent_tool_xyz", {})
    assert isinstance(res, dict)
    assert res.get("success") is False or "error" in res
