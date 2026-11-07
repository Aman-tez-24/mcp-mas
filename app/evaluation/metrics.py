"""
Evaluation Metrics Computation Functions
Implements formulas from PDF Section 15, 20, and 23 using pure standard library.
"""

from typing import List


def compute_groundedness(supported_claims: int, total_claims: int) -> float:
    """claims supported by retrieved evidence / total claims (target >= 90%)"""
    if total_claims <= 0:
        return 1.0
    return round(min(1.0, supported_claims / total_claims), 4)


def compute_hallucination_rate(unsupported_claims: int, total_claims: int) -> float:
    """unsupported factual claims / total factual claims (target <= 10%)"""
    if total_claims <= 0:
        return 0.0
    return round(min(1.0, unsupported_claims / total_claims), 4)


def compute_citation_correctness(valid_citations: int, total_citations: int) -> float:
    """correct evidence links / cited evidence links (target >= 90%)"""
    if total_citations <= 0:
        return 1.0
    return round(min(1.0, valid_citations / total_citations), 4)


def compute_p95_latency(latencies: List[float]) -> float:
    """Calculates 95th percentile latency from run times."""
    if not latencies:
        return 0.0
    sorted_lats = sorted(latencies)
    idx = int(0.95 * len(sorted_lats))
    idx = min(idx, len(sorted_lats) - 1)
    return round(sorted_lats[idx], 2)


def compute_mean_latency(latencies: List[float]) -> float:
    """Mean end-to-end run time."""
    if not latencies:
        return 0.0
    return round(sum(latencies) / len(latencies), 2)
