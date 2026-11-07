"""
MCP Server Instance
Registers tools using official Python MCP SDK v2 (MCPServer).
Can be run via stdio transport or imported by MCP clients.
"""

import sys
import os
from typing import Any, Dict, List

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from mcp.server.mcpserver import MCPServer
from mcp_server import tools

# Initialize MCP Server with metadata
mcp_server = MCPServer(
    name="academic-research-mcp-server",
    version="1.0.0",
    description="Multi-Agent Academic Research MCP Server for Local Corpus Exploration",
)


@mcp_server.tool()
def search_sources(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    Search the curated local document collection for passages relevant to a query.

    Args:
        query: Search keywords or research question.
        max_results: Maximum number of passage records to return (default 5).

    Returns:
        Dictionary with matching passages, document IDs, relevance scores, and sources.
    """
    return tools.search_sources(query=query, max_results=max_results)


@mcp_server.tool()
def get_document(document_id: str) -> Dict[str, Any]:
    """
    Retrieve full content and metadata for a specific document ID.

    Args:
        document_id: Unique identifier of the document (e.g. 'DOC-001').

    Returns:
        Dictionary with document text, source, publication date, and quality rating.
    """
    return tools.get_document(document_id=document_id)


@mcp_server.tool()
def calculator(expression: str) -> Dict[str, Any]:
    """
    Perform safe mathematical and arithmetic calculations without unrestricted eval.

    Args:
        expression: Mathematical expression string containing numbers and operators (+, -, *, /, %, **).

    Returns:
        Dictionary with evaluation result or descriptive error message.
    """
    return tools.safe_calculator(expression=expression)


@mcp_server.tool()
def save_evidence(run_id: str, evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Persist evidence records for a research run for auditability and verification.

    Args:
        run_id: Unique identifier for the research execution run.
        evidence: List of evidence items with evidence_id, source, text, and relevance.

    Returns:
        Dictionary confirming persistence status and file path.
    """
    return tools.save_evidence(run_id=run_id, evidence=evidence)


@mcp_server.tool()
def get_run_metrics(run_id: str) -> Dict[str, Any]:
    """
    Retrieve execution metrics and audit trail for a research run.

    Args:
        run_id: Unique identifier for the run.

    Returns:
        Dictionary with run latency, token usage, cost, and hallucination scores.
    """
    return tools.get_run_metrics(run_id=run_id)


def main():
    """Run the MCP server in standard input/output mode (stdio transport)."""
    # stdio transport is the official and robust local transport in MCP
    mcp_server.run(transport="stdio")


if __name__ == "__main__":
    main()
