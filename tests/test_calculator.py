"""
Unit tests for Safe Calculator tool using AST parsing.
Verifies arithmetic correctness and strict security constraints (No eval).
"""

import pytest
from mcp_server.tools import safe_calculator


def test_basic_arithmetic():
    res = safe_calculator("2 + 3 * 4")
    assert res["success"] is True
    assert res["result"] == 14
    assert res["error"] is None


def test_parentheses_and_power():
    res = safe_calculator("(2 + 3) ** 2")
    assert res["success"] is True
    assert res["result"] == 25


def test_floating_point_division():
    res = safe_calculator("10 / 4")
    assert res["success"] is True
    assert res["result"] == 2.5


def test_cost_calculation_expression():
    # PDF Section 20 formula
    res = safe_calculator("(4000 / 1000000) * 1.0 + (1000 / 1000000) * 5.0")
    assert res["success"] is True
    assert abs(res["result"] - 0.009) < 1e-6


def test_zero_division_error_handling():
    res = safe_calculator("50 / 0")
    assert res["success"] is False
    assert "division by zero" in res["error"].lower()


def test_malicious_code_injection_rejected():
    # Attempt code execution via __import__
    res = safe_calculator("__import__('os').system('echo hack')")
    assert res["success"] is False
    assert "unsupported syntax" in res["error"].lower() or "disallowed" in res["error"].lower()


def test_function_call_rejected():
    res = safe_calculator("print('hello')")
    assert res["success"] is False


def test_variable_assignment_rejected():
    res = safe_calculator("x = 10")
    assert res["success"] is False


def test_empty_expression():
    res = safe_calculator("   ")
    assert res["success"] is False
    assert "empty" in res["error"].lower()
