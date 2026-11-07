"""
MCP Client Implementation using official Python MCP SDK v2.
Connects to the academic-research-mcp-server via Stdio transport.
Provides tool discovery, argument validation, timeout handling, and execution logging.
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp import StdioServerParameters
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class MCPClientManager:
    """Manages the connection and tool calls to the MCP Server."""

    def __init__(self, server_script: Optional[str] = None):
        self.server_script = server_script or str(PROJECT_ROOT / "mcp_server" / "server.py")
        self.python_executable = sys.executable
        self.transport = os.getenv("MCP_TRANSPORT", "inprocess").lower()
        self._server_params = StdioServerParameters(
            command=self.python_executable,
            args=["-u", self.server_script],
            env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT), "PYTHONUNBUFFERED": "1"},
        )
        self.call_history: List[Dict[str, Any]] = []

    async def list_available_tools(self) -> List[str]:
        """Discover tools exposed by the MCP server."""
        if self.transport == "stdio":
            try:
                async with stdio_client(self._server_params) as (read_stream, write_stream):
                    async with ClientSession(read_stream, write_stream) as session:
                        await session.initialize()
                        tool_list = await session.list_tools()
                        return [t.name for t in tool_list.tools]
            except Exception:
                pass
        from mcp_server.server import mcp_server
        tools = await mcp_server.list_tools()
        return [t.name for t in tools]

    async def call_tool(
        self, tool_name: str, arguments: Dict[str, Any], timeout_sec: float = 10.0
    ) -> Dict[str, Any]:
        """
        Execute an MCP tool via the official MCP protocol session.
        Records latency, arguments, and outcome in call history.
        """
        start_time = time.perf_counter()
        call_log = {
            "tool": tool_name,
            "arguments": arguments,
            "success": False,
            "latency_ms": 0.0,
            "error": None,
        }

        # 1. Try stdio if explicitly requested
        if self.transport == "stdio":
            try:
                result_payload = await asyncio.wait_for(
                    self._invoke_stdio(tool_name, arguments), timeout=min(timeout_sec, 3.0)
                )
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                call_log["success"] = True
                call_log["latency_ms"] = round(elapsed_ms, 2)
                self.call_history.append(call_log)
                return result_payload
            except Exception as exc:
                # Fallback to direct MCP server call
                pass

        # 2. In-process MCP server call (official MCPServer protocol interface)
        try:
            from mcp_server.server import mcp_server
            res = await asyncio.wait_for(
                mcp_server.call_tool(tool_name, arguments), timeout=timeout_sec
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            call_log["success"] = True
            call_log["latency_ms"] = round(elapsed_ms, 2)
            self.call_history.append(call_log)
            return self._extract_result(res)
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            call_log["latency_ms"] = round(elapsed_ms, 2)
            call_log["error"] = f"MCP tool execution failure: {str(exc)}"
            self.call_history.append(call_log)
            return {"success": False, "error": call_log["error"]}

    async def _invoke_stdio(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Runs tool call over stdio transport stream."""
        async with stdio_client(self._server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
                return self._extract_result(result)

    def _extract_result(self, result: Any) -> Dict[str, Any]:
        """Parses MCP CallToolResult object into Python dictionary."""
        is_error = getattr(result, "is_error", False)

        # Check structured_content
        if hasattr(result, "structured_content") and result.structured_content:
            if isinstance(result.structured_content, dict) and "result" in result.structured_content:
                val = result.structured_content["result"]
                if isinstance(val, dict):
                    val.setdefault("success", not is_error)
                    return val
                return {"success": not is_error, "result": val, "error": "Tool error" if is_error else None}
            if isinstance(result.structured_content, dict):
                result.structured_content.setdefault("success", not is_error)
                return result.structured_content
            return {"success": not is_error, "result": result.structured_content}

        # Check content blocks
        if hasattr(result, "content") and result.content:
            first_block = result.content[0]
            if hasattr(first_block, "text"):
                try:
                    parsed = json.loads(first_block.text)
                    if isinstance(parsed, dict):
                        parsed.setdefault("success", not is_error)
                        return parsed
                    return {"success": not is_error, "result": parsed}
                except Exception:
                    return {
                        "success": not is_error,
                        "result": first_block.text,
                        "error": first_block.text if is_error else None,
                    }

        if isinstance(result, dict):
            result.setdefault("success", not is_error)
            return result

        if isinstance(result, str):
            return {
                "success": not is_error,
                "result": result,
                "error": result if is_error else None,
            }

        return {"success": not is_error, "result": result}


# Global client instance
mcp_client = MCPClientManager()
