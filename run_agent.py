"""
CLI Runner for Multi-Agent Research Assistant (MCP)
Allows running the 5-Agent research pipeline directly from the terminal.

Usage:
    python run_agent.py "Your research question here"
    python run_agent.py --fast "Your research question here"
    python run_agent.py --baseline "Your research question here"
    python run_agent.py   (runs interactive prompt or default question)
"""

import argparse
import asyncio
import os
import sys
import time

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


async def main():
    parser = argparse.ArgumentParser(description="Multi-Agent Research Assistant using MCP")
    parser.add_argument(
        "question",
        nargs="?",
        default="Compare retrieval-augmented generation (RAG) and fine-tuning for a university chatbot.",
        help="The research question to analyze.",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Force fast deterministic rule-based engine instead of waiting for local Ollama LLM.",
    )
    parser.add_argument(
        "--baseline",
        action="store_true",
        help="Run single-agent ungrounded baseline instead of multi-agent MCP workflow.",
    )
    args = parser.parse_args()

    if args.fast:
        os.environ["LLM_PROVIDER"] = "deterministic"
        print("[Mode] Fast deterministic rule-based engine forced.")

    from app.llm_engine import llm_engine
    from app.orchestrator import orchestrator

    question = args.question.strip()
    print("=" * 80)
    print("  MULTI-AGENT RESEARCH ASSISTANT (MODEL CONTEXT PROTOCOL)")
    print("=" * 80)
    print(f"Question : {question}")
    ollama_ready = llm_engine.is_ollama_available()
    print(f"Engine   : {'Ollama (' + llm_engine.model + ')' if ollama_ready else 'Deterministic Rule Engine (Fast)'}")
    print(f"Variant  : {'Single-Agent Baseline (Variant A)' if args.baseline else '5-Agent MCP Pipeline (Variant D)'}")
    print("-" * 80)

    start_time = time.perf_counter()

    if args.baseline:
        print("\n>>> Running Single-Agent Baseline...")
        state = await orchestrator.execute_baseline(question)
    else:
        print("\n>>> Executing 5-Agent MCP Workflow...")
        print("  [1/5] Planner Agent     : Decomposing research question...")
        print("  [2/5] Researcher Agent  : Querying MCP tools (search_sources, get_document, calculator)...")
        print("  [3/5] Verifier Agent    : Checking evidence entailment & source conflicts...")
        print("  [4/5] Writer Agent      : Synthesizing verified report with citations...")
        print("  [5/5] Evaluator Agent   : Computing groundedness, hallucination rate & metrics...")
        state = await orchestrator.execute_query(question)

    elapsed = (time.perf_counter() - start_time) * 1000

    print("\n" + "=" * 80)
    print("  FINAL SYNTHESIZED REPORT")
    print("=" * 80)
    print(state.final_answer)

    print("\n" + "=" * 80)
    print("  EVIDENCE & CLAIMS AUDIT")
    print("=" * 80)
    print(f"Total Evidence Items Retrieved : {len(state.evidence)}")
    for ev in state.evidence:
        print(f"  [{ev.evidence_id}] {ev.source} (Doc: {ev.document_id}, Relevance: {ev.relevance:.2f})")
        clean_text = ev.text.replace("\n", " ")[:100]
        print(f"       Passage: \"{clean_text}...\"")

    print(f"\nTotal Claims Extracted & Verified : {len(state.claims)}")
    for c in state.claims:
        status_symbol = "OK" if c.status.value.lower() in ["supported", "partially_supported"] else "FLAG"
        print(f"  [{c.claim_id}] [{status_symbol}] ({c.status.value.upper()}) {c.statement}")
        if c.evidence_ids:
            print(f"       Cited Evidence: {', '.join(c.evidence_ids)}")

    print("\n" + "=" * 80)
    print("  EVALUATION METRICS (Section 25 / Section 26)")
    print("=" * 80)
    print(f"  Run ID               : {state.run_id}")
    print(f"  Groundedness Score   : {state.groundedness * 100:.1f}%")
    print(f"  Hallucination Rate   : {state.hallucination_rate * 100:.1f}%")
    print(f"  Evidence Coverage    : {state.evidence_coverage * 100:.1f}%")
    print(f"  Citation Correctness : {state.citation_correctness * 100:.1f}%")
    print(f"  MCP Tool Calls       : {state.tool_calls}")
    print(f"  Input Tokens         : {state.input_tokens}")
    print(f"  Output Tokens        : {state.output_tokens}")
    print(f"  Total Tokens         : {state.input_tokens + state.output_tokens}")
    print(f"  Total Cost           : ${state.estimated_cost_usd:.6f} USD (Zero-Cost Localhost)")
    print(f"  End-to-End Latency   : {state.latency_ms:.0f} ms (Measured: {elapsed:.0f} ms)")
    print("=" * 80)
    print(f"Audit record persisted to: results/runs/{state.run_id}.json\n")


if __name__ == "__main__":
    asyncio.run(main())
