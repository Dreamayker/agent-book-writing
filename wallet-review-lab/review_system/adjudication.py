from collections import defaultdict

from review_system.schemas import Evidence, Finding, Severity

SEVERITY_RANK = {
    Severity.NITPICK: 0,
    Severity.CONCERN: 1,
    Severity.MUST_FIX: 2,
}


def evidence_key(evidence: Evidence) -> tuple[str, str]:
    return (evidence.type.value, evidence.ref)


def finding_key(finding: Finding) -> tuple[str, str, str, str]:
    """Explicit root IDs merge across files; legacy fixtures retain location scope."""
    if finding.root_cause_id:
        return (finding.root_cause_id, finding.symbol or "", finding.invariant or "", "")
    return (finding.finding_id, finding.file, str(finding.line_start), "")


def deduplicate_findings(findings: list[Finding]) -> list[Finding]:
    grouped: dict[tuple[str, str, str, str], list[Finding]] = defaultdict(list)
    for finding in findings:
        grouped[finding_key(finding)].append(finding)

    merged: list[Finding] = []
    for candidates in grouped.values():
        strongest = max(
            candidates,
            key=lambda item: (SEVERITY_RANK[item.severity], item.confidence, len(item.evidence)),
        )
        evidence_by_key = {
            evidence_key(evidence): evidence
            for candidate in candidates
            for evidence in candidate.evidence
        }
        sources = sorted({candidate.source for candidate in candidates})
        merged.append(
            strongest.model_copy(
                update={
                    "source": ",".join(sources),
                    "confidence": max(candidate.confidence for candidate in candidates),
                    "evidence": list(evidence_by_key.values()),
                    "blocking": any(candidate.blocking for candidate in candidates),
                    "needs_human": any(candidate.needs_human for candidate in candidates),
                }
            )
        )
    return sorted(merged, key=lambda item: (item.file, item.line_start, item.finding_id))


class Verdict(str):
    APPROVE = "approve"
    COMMENT = "comment"
    REQUEST_CHANGES = "request_changes"
    ESCALATE = "escalate"


def arbitrate(findings: list[Finding], *, high_risk: bool) -> str:
    """Apply policy after findings have been validated and deduplicated."""
    if high_risk or any(finding.needs_human for finding in findings):
        return Verdict.ESCALATE
    if any(finding.blocking for finding in findings):
        return Verdict.REQUEST_CHANGES
    if findings:
        return Verdict.COMMENT
    return Verdict.APPROVE
