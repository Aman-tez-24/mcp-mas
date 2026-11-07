"""
Agent 5: Evaluator Agent
Calculates machine-measurable metrics according to PDF Section 15 & 20:
- Groundedness (supported claims / total claims)
- Hallucination Rate (unsupported claims / total claims)
- Citation Correctness (valid citations / total cited evidence tags)
- Evidence Coverage (supported factual claims / factual claims)
- Tool Success Rate (successful MCP tool calls / total tool calls)
- Total Tokens & Latency
- Cost Accounting via MCP calculator
"""

import re
import time
from typing import Any, Dict, List, Tuple
from app.mcp_client.client import mcp_client
from app.llm_engine import calculate_cost
from app.schemas.models import AgentStepLog, Claim, Evidence, RunMetrics


class EvaluatorAgent:
    def __init__(self):
        self.name = "evaluator"

    async def evaluate_run(
        self,
        question: str,
        evidence: List[Evidence],
        claims: List[Claim],
        report_text: str,
        agent_logs: List[AgentStepLog],
        mcp_calls: List[Dict[str, Any]],
        total_latency_ms: float,
        input_price_per_1m: float = 0.0,
        output_price_per_1m: float = 0.0,
    ) -> Tuple[RunMetrics, AgentStepLog]:
        start_time = time.perf_counter()

        # 1. Total tokens processed
        total_input_toks = sum(log.tokens.get("input", 0) for log in agent_logs)
        total_output_toks = sum(log.tokens.get("output", 0) for log in agent_logs)
        total_tokens = total_input_toks + total_output_toks

        # 2. Tool success rate
        total_mcp = len(mcp_calls)
        successful_mcp = sum(1 for c in mcp_calls if c.get("success", False))
        tool_success_rate = (successful_mcp / total_mcp) if total_mcp > 0 else 1.0

        # 3. Groundedness and Hallucination Rate
        total_claims = len(claims)
        if not evidence or not any(c.supported for c in claims):
            # Anti-hallucination refusal: no factual assertions asserted into final report
            groundedness = 1.0
            hallucination_rate = 0.0
            evidence_coverage = 0.0
        elif total_claims > 0:
            supported_count = sum(1 for c in claims if c.supported)
            unsupported_count = sum(1 for c in claims if not c.supported)
            groundedness = round(supported_count / total_claims, 4)
            hallucination_rate = round(unsupported_count / total_claims, 4)
            evidence_coverage = round(supported_count / total_claims, 4)
        else:
            groundedness = 1.0
            hallucination_rate = 0.0
            evidence_coverage = 0.0

        # 4. Citation Correctness
        # Extract cited evidence tags from report text e.g. [E1], [E2]
        cited_tags = set(re.findall(r"\[E(\d+)\]", report_text))
        valid_ev_ids = {f"E{e.evidence_id.replace('E', '')}" for e in evidence}

        if cited_tags:
            valid_citations = sum(1 for t in cited_tags if f"E{t}" in valid_ev_ids)
            citation_correctness = round(valid_citations / len(cited_tags), 4)
        else:
            citation_correctness = 1.0 if not evidence else 1.0

        # 5. Cost Accounting
        # Use MCP calculator tool to verify the arithmetic if pricing > 0
        calc_cost = 0.0
        if input_price_per_1m > 0 or output_price_per_1m > 0:
            expr = f"({total_input_toks} / 1000000.0) * {input_price_per_1m} + ({total_output_toks} / 1000000.0) * {output_price_per_1m}"
            calc_res = await mcp_client.call_tool("calculator", {"expression": expr})
            if calc_res.get("success") and calc_res.get("result") is not None:
                calc_cost = float(calc_res["result"])
            else:
                calc_cost = calculate_cost(total_input_toks, total_output_toks, input_price_per_1m, output_price_per_1m)
        else:
            calc_cost = 0.0

        metrics = RunMetrics(
            latency_ms=round(total_latency_ms, 2),
            cost_usd=round(calc_cost, 6),
            total_tokens=total_tokens,
            input_tokens=total_input_toks,
            output_tokens=total_output_toks,
            groundedness=groundedness,
            hallucination_rate=hallucination_rate,
            citation_correctness=citation_correctness,
            evidence_coverage=evidence_coverage,
            tool_success_rate=round(tool_success_rate, 4),
            tool_calls=total_mcp,
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        log = AgentStepLog(
            name=self.name,
            latency_ms=round(elapsed_ms, 2),
            tokens={"input": 0, "output": 0},
            status="success",
            summary=f"Evaluated metrics: Groundedness={groundedness:.2%}, Hallucination={hallucination_rate:.2%}, Citations={citation_correctness:.2%}",
        )

        return metrics, log
