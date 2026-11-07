"""
Unit and integration tests for the 5 agents:
Planner, Researcher, Verifier, Writer, Evaluator.
"""

import pytest
from app.agents.planner import PlannerAgent
from app.agents.researcher import ResearcherAgent
from app.agents.verifier import VerifierAgent
from app.agents.writer import WriterAgent
from app.agents.evaluator import EvaluatorAgent
from app.schemas.models import Claim, ClaimStatus, Evidence, ResearchTask


@pytest.mark.asyncio
async def test_planner_agent_decomposition():
    planner = PlannerAgent()
    tasks, log = await planner.plan("Compare RAG and fine-tuning for a university chatbot.", max_subtasks=4)
    assert len(tasks) >= 2
    assert len(tasks) <= 5
    assert log.status == "success"
    assert all(isinstance(t, ResearchTask) for t in tasks)


@pytest.mark.asyncio
async def test_researcher_agent_mcp_gathering():
    researcher = ResearcherAgent()
    subtasks = [ResearchTask(id="T1", task="Retrieval-Augmented Generation RAG advantages")]
    evidence, log = await researcher.research(subtasks, "test-research-001")
    assert len(evidence) > 0
    first = evidence[0]
    assert isinstance(first, Evidence)
    assert first.evidence_id.startswith("E")
    assert first.relevance > 0.0


@pytest.mark.asyncio
async def test_verifier_agent_supported_claim():
    verifier = VerifierAgent()
    sample_evidence = [
        Evidence(
            evidence_id="E1",
            document_id="DOC-001",
            source="Test Source",
            text="Retrieval-Augmented Generation combines parametric language models with non-parametric retrieval memory.",
            relevance=0.9,
            source_quality=0.95
        )
    ]
    candidate_claims = [
        Claim(
            claim_id="C1",
            statement="RAG combines parametric language models with non-parametric retrieval memory.",
            evidence_ids=["E1"],
            supported=True
        )
    ]
    verified, has_conflict, conflict_notes, log = await verifier.verify(candidate_claims, sample_evidence)
    assert len(verified) == 1
    assert verified[0].status == ClaimStatus.SUPPORTED
    assert verified[0].supported is True
    assert has_conflict is False


@pytest.mark.asyncio
async def test_verifier_agent_unsupported_claim():
    verifier = VerifierAgent()
    sample_evidence = [
        Evidence(
            evidence_id="E1",
            document_id="DOC-001",
            source="Test Source",
            text="Central Science Library operates until 11:00 PM on weekdays.",
            relevance=0.9,
            source_quality=0.95
        )
    ]
    # Claim completely absent from evidence
    candidate_claims = [
        Claim(
            claim_id="C1",
            statement="Astronauts discovered alien ruins on Jupiter's moon Europa.",
            evidence_ids=["E1"],
            supported=True
        )
    ]
    verified, has_conflict, conflict_notes, log = await verifier.verify(candidate_claims, sample_evidence)
    assert len(verified) == 1
    assert verified[0].status == ClaimStatus.UNSUPPORTED
    assert verified[0].supported is False


@pytest.mark.asyncio
async def test_verifier_contradiction_detection():
    verifier = VerifierAgent()
    conflicting_evidence = [
        Evidence(
            evidence_id="E1",
            document_id="DOC-006",
            source="Bulletin A",
            text="The library maintains standard operating hours from 8:00 AM to 11:00 PM on weekdays.",
            relevance=0.9,
            source_quality=0.9
        ),
        Evidence(
            evidence_id="E2",
            document_id="DOC-007",
            source="Bulletin B",
            text="Special Energy Conservation Order: The Central Science Library will restrict weekday operations to closing strictly at 8:00 PM.",
            relevance=0.85,
            source_quality=0.85
        )
    ]
    claims = [
        Claim(claim_id="C1", statement="Library closes at 11:00 PM on weekdays", evidence_ids=["E1"]),
        Claim(claim_id="C2", statement="Library closes at 8:00 PM on weekdays", evidence_ids=["E2"])
    ]
    verified, has_conflict, conflict_notes, log = await verifier.verify(claims, conflicting_evidence)
    assert has_conflict is True
    assert "conflict detected" in conflict_notes.lower()
