from evaluation.scoring import score_finding_ids
from review_system.schemas import Evidence, EvidenceType, Finding, Severity


def make_finding(finding_id: str) -> Finding:
    return Finding(
        finding_id=finding_id,
        source="recorded",
        category="correctness",
        severity=Severity.MUST_FIX,
        confidence=1,
        file="app/service.py",
        line_start=1,
        claim="Recorded finding",
        evidence=[Evidence(type=EvidenceType.SOURCE, ref="app/service.py:1")],
        blocking=True,
    )


def test_scoring_counts_unique_finding_ids() -> None:
    metrics = score_finding_ids(
        [make_finding("MONEY-001"), make_finding("NOISE-001")], {"MONEY-001", "AUTHZ-001"}
    )
    assert metrics.true_positives == 1
    assert metrics.false_positives == 1
    assert metrics.false_negatives == 1
    assert metrics.precision == 0.5
    assert metrics.recall == 0.5
