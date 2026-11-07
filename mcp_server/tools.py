"""
MCP Server Tools Implementation
Provides the 5 core tools required by the MCP specification:
1. search_sources(query)
2. get_document(document_id)
3. calculator(expression)
4. save_evidence(run_id, evidence)
5. get_run_metrics(run_id)
"""

import ast
import json
import math
import operator
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DOCUMENTS_DIR = BASE_DIR / "data" / "documents"
RUNS_DIR = BASE_DIR / "results" / "runs"

# Ensure runtime directories exist
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
RUNS_DIR.mkdir(parents=True, exist_ok=True)


# --- 1. Safe Calculator using AST (Strict Security: No eval) ---

_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _eval_ast_node(node: ast.AST) -> float:
    """Recursively evaluate an AST node strictly restricted to numeric arithmetic."""
    if isinstance(node, ast.Expression):
        return _eval_ast_node(node.body)
    elif isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise ValueError(f"Disallowed constant type: {type(node.value).__name__}")
    elif isinstance(node, ast.BinOp):
        left = _eval_ast_node(node.left)
        right = _eval_ast_node(node.right)
        op_type = type(node.op)
        if op_type in _ALLOWED_OPERATORS:
            if op_type in (ast.Div, ast.FloorDiv, ast.Mod) and right == 0:
                raise ZeroDivisionError("Division by zero is undefined")
            # Guard against massive exponent computations (DoS protection)
            if op_type == ast.Pow:
                if right > 100 or left > 1e10:
                    raise ValueError("Exponentiation values exceeded safety bounds")
            return float(_ALLOWED_OPERATORS[op_type](left, right))
        raise ValueError(f"Disallowed binary operator: {op_type.__name__}")
    elif isinstance(node, ast.UnaryOp):
        operand = _eval_ast_node(node.operand)
        op_type = type(node.op)
        if op_type in _ALLOWED_OPERATORS:
            return float(_ALLOWED_OPERATORS[op_type](operand))
        raise ValueError(f"Disallowed unary operator: {op_type.__name__}")
    else:
        raise ValueError(f"Unsupported syntax: {type(node).__name__}. Only arithmetic operations allowed.")


def safe_calculator(expression: str) -> Dict[str, Any]:
    """
    Safely evaluate arithmetic expressions without using Python eval().
    Supports +, -, *, /, //, %, ** and parentheses.
    """
    if not expression or not expression.strip():
        return {
            "expression": expression,
            "success": False,
            "result": None,
            "error": "Empty expression provided",
        }

    cleaned = expression.strip()
    try:
        parsed = ast.parse(cleaned, mode="eval")
        result = _eval_ast_node(parsed)
        # Round cleanly to 6 decimal places if floating precision residue
        rounded = round(result, 6)
        if rounded.is_integer():
            rounded = int(rounded)
        return {
            "expression": cleaned,
            "success": True,
            "result": rounded,
            "error": None,
        }
    except ZeroDivisionError as zde:
        return {
            "expression": cleaned,
            "success": False,
            "result": None,
            "error": f"Math error: {str(zde)}",
        }
    except Exception as exc:
        return {
            "expression": cleaned,
            "success": False,
            "result": None,
            "error": f"Invalid or disallowed expression: {str(exc)}",
        }


# --- 2. Corpus Search & Document Lookup ---

def _load_all_documents() -> List[Dict[str, Any]]:
    """Loads all JSON documents from data/documents."""
    documents = []
    if not DOCUMENTS_DIR.exists():
        return documents

    for file_path in sorted(DOCUMENTS_DIR.glob("*.json")):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                data["_file"] = file_path.name
                documents.append(data)
        except Exception:
            continue
    return documents


def _tokenize(text: str) -> set[str]:
    """Extract lowercase alpha-numeric words for lexical matching."""
    return set(re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", text.lower()))


def search_sources(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    Search curated local documents using term frequency-inverse term matching.
    Returns matched passages, document IDs, relevance score, and source quality.
    """
    if not query or not query.strip():
        return {
            "query": query,
            "total_matches": 0,
            "results": [],
            "message": "Empty query returned 0 results.",
        }

    query_tokens = _tokenize(query)
    if not query_tokens:
        return {
            "query": query,
            "total_matches": 0,
            "results": [],
            "message": "No searchable tokens in query.",
        }

    documents = _load_all_documents()
    scored_results = []

    for doc in documents:
        doc_id = doc.get("document_id", "UNKNOWN")
        title = doc.get("title", "")
        content = doc.get("content", "")
        source = doc.get("source", "Local Corpus")
        source_quality = float(doc.get("source_quality", 0.8))

        doc_text = f"{title} {content}".lower()
        content_tokens = _tokenize(doc_text)

        # Calculate Jaccard / Overlap score
        matched = query_tokens.intersection(content_tokens)
        if not matched:
            continue

        token_overlap = len(matched) / len(query_tokens)

        # Exact phrase bonus
        clean_q = query.strip().lower()
        phrase_bonus = 0.3 if (clean_q in doc_text and len(clean_q) > 3) else 0.0

        # Title match bonus
        title_bonus = 0.2 if any(t in title.lower() for t in query_tokens) else 0.0

        relevance = min(1.0, round(token_overlap * 0.6 + phrase_bonus + title_bonus, 3))
        # Filter weak irrelevant matches (e.g. single word match on unknown topics)
        if relevance < 0.35:
            continue

        # Extract snippet around matched terms
        snippet = _extract_snippet(content, list(matched))

        scored_results.append({
            "document_id": doc_id,
            "title": title,
            "source": source,
            "source_quality": source_quality,
            "relevance": relevance,
            "matched_terms": list(matched),
            "text": snippet,
        })

    # Sort descending by relevance score, then source quality
    scored_results.sort(key=lambda x: (x["relevance"], x["source_quality"]), reverse=True)
    top_results = scored_results[:max_results]

    return {
        "query": query,
        "total_matches": len(top_results),
        "results": top_results,
    }


def _extract_snippet(content: str, terms: List[str], max_len: int = 1200) -> str:
    """Extract a contextual window of text containing matching terms."""
    if len(content) <= max_len:
        return content

    if not terms:
        return content[:max_len] + "..."

    lower_content = content.lower()
    first_idx = len(content)
    for term in terms:
        pos = lower_content.find(term)
        if 0 <= pos < first_idx:
            first_idx = pos

    if first_idx >= len(content):
        first_idx = 0

    start = max(0, first_idx - 60)
    end = min(len(content), start + max_len)

    snippet = content[start:end].strip()
    if start > 0:
        snippet = "..." + snippet
    if end < len(content):
        snippet = snippet + "..."
    return snippet


def get_document(document_id: str) -> Dict[str, Any]:
    """Retrieve full content and metadata for a specific document ID."""
    if not document_id:
        return {
            "success": False,
            "error": "Document ID must not be empty.",
            "document": None,
        }

    clean_id = document_id.strip().upper()
    documents = _load_all_documents()

    for doc in documents:
        if doc.get("document_id", "").upper() == clean_id:
            return {
                "success": True,
                "error": None,
                "document": {
                    "document_id": doc.get("document_id"),
                    "title": doc.get("title"),
                    "source": doc.get("source"),
                    "source_quality": doc.get("source_quality", 1.0),
                    "category": doc.get("category", "general"),
                    "published_date": doc.get("published_date"),
                    "content": doc.get("content", ""),
                },
            }

    return {
        "success": False,
        "error": f"Document with ID '{document_id}' was not found in the local corpus.",
        "document": None,
    }


# --- 3. Run State & Evidence Persistence ---

def save_evidence(run_id: str, evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Persist evidence list for auditability and grading inspection."""
    if not run_id:
        return {"success": False, "error": "run_id is required."}

    # Sanitize run_id against directory traversal
    clean_run_id = re.sub(r"[^a-zA-Z0-9_\-]", "_", run_id)
    out_file = RUNS_DIR / f"{clean_run_id}_evidence.json"

    try:
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump({
                "run_id": run_id,
                "count": len(evidence),
                "evidence": evidence,
            }, f, indent=2)

        return {
            "success": True,
            "run_id": run_id,
            "file": str(out_file.name),
            "count": len(evidence),
        }
    except Exception as exc:
        return {"success": False, "error": f"Failed to persist evidence: {str(exc)}"}


def get_run_metrics(run_id: str) -> Dict[str, Any]:
    """Retrieve accumulated metrics and audit records for an active or completed run."""
    if not run_id:
        return {"success": False, "error": "run_id is required."}

    clean_run_id = re.sub(r"[^a-zA-Z0-9_\-]", "_", run_id)
    run_file = RUNS_DIR / f"{clean_run_id}.json"

    if not run_file.exists():
        # Check evidence file as fallback
        ev_file = RUNS_DIR / f"{clean_run_id}_evidence.json"
        if ev_file.exists():
            with open(ev_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                "success": True,
                "run_id": run_id,
                "status": "partial_evidence_only",
                "evidence_count": data.get("count", 0),
            }
        return {
            "success": False,
            "error": f"Run '{run_id}' not found.",
            "metrics": None,
        }

    try:
        with open(run_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            "success": True,
            "run_id": run_id,
            "metrics": data.get("metrics", {}),
            "tool_calls": data.get("tool_calls", 0),
            "latency_ms": data.get("latency_ms", 0),
            "total_tokens": data.get("total_tokens", 0),
            "cost_usd": data.get("estimated_cost_usd", 0.0),
        }
    except Exception as exc:
        return {"success": False, "error": f"Error reading run metrics: {str(exc)}"}
