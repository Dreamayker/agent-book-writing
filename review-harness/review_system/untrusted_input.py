import re
from pathlib import Path

from review_system.schemas import Evidence, EvidenceType, Finding, Severity

REVIEW_INSTRUCTION = re.compile(
    r"(?i)\b(ignore|bypass|skip|reveal|approve)\b.{0,80}"
    r"\b(review|security|instruction|policy|system|change)\b"
)


def scan_untrusted_text(text: str, source_path: str) -> list[Finding]:
    """Flag repository text that appears to instruct the reviewer.

    This is deliberately a narrow deterministic guard, not a complete prompt
    injection detector. A match forces human review but never executes or
    follows the matched text.
    """
    findings: list[Finding] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if REVIEW_INSTRUCTION.search(line):
            findings.append(
                Finding(
                    finding_id="AGENTSEC-001",
                    source="untrusted-input-guard",
                    category="agent-security",
                    severity=Severity.MUST_FIX,
                    confidence=1.0,
                    file=source_path,
                    line_start=line_number,
                    claim="Repository text appears to instruct the review system",
                    evidence=[
                        Evidence(
                            type=EvidenceType.POLICY,
                            ref="policies/review-policy.yaml:untrusted_inputs",
                        )
                    ],
                    suggested_fix="Treat the text as quoted data and require human review",
                    blocking=True,
                    needs_human=True,
                )
            )
    return findings


def scan_file(path: Path) -> list[Finding]:
    return scan_untrusted_text(path.read_text(encoding="utf-8"), str(path))
