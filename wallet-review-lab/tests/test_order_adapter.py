import hashlib
import json
from pathlib import Path

import pytest

from evaluation.projects import match_roots
from review_system.adjudication import deduplicate_findings
from review_system.agents import ReviewContext
from review_system.evidence import checked_path, validate_references, verified_evidence
from review_system.router import RiskRouter
from review_system.schemas import Finding, RiskLevel


def finding(**changes: object) -> Finding:
    values: dict[str, object] = dict(
        finding_id="REFUND-001",
        root_cause_id="snapshot-reprice",
        invariant="frozen-price",
        source="test",
        category="correctness",
        severity="must_fix",
        confidence=0.95,
        file="Refund.java",
        line_start=10,
        claim="Reprices instead of using snapshot",
        evidence=[{"type": "test", "ref": "failure.txt"}],
        blocking=True,
    )
    values.update(changes)
    return Finding.model_validate(values)


def context(tmp_path: Path) -> ReviewContext:
    (tmp_path / "failure.txt").write_text("expected 6600 actual 6400")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "run_id": "run-1",
                "case_id": "ORD-09",
                "code_revision": "abc",
                "files": [
                    {
                        "path": "failure.txt",
                        "sha256": hashlib.sha256(
                            (tmp_path / "failure.txt").read_bytes()
                        ).hexdigest(),
                    }
                ],
            }
        )
    )
    return ReviewContext(
        case_id="ORD-09",
        patch_path=tmp_path / "buggy.patch",
        changed_paths=["Refund.java"],
        project_root=tmp_path,
        code_revision="abc",
        evidence_manifest=manifest,
    )


def test_evidence_is_bound_to_case_revision_and_hash(tmp_path: Path) -> None:
    ctx = context(tmp_path)
    assert verified_evidence(ctx)["files"][0]["content"] == "expected 6600 actual 6400"
    validate_references(ctx, [finding()])
    with pytest.raises(ValueError, match="outside this run"):
        validate_references(ctx, [finding(evidence=[{"type": "test", "ref": "other.txt"}])])
    with pytest.raises(ValueError, match="different case"):
        verified_evidence(ctx.model_copy(update={"code_revision": "def"}))
    (tmp_path / "failure.txt").write_text("forged")
    with pytest.raises(ValueError, match="hash mismatch"):
        verified_evidence(ctx)
    with pytest.raises(ValueError, match="escapes"):
        checked_path(tmp_path, "../secret")


def test_explicit_root_merges_cross_file_but_keeps_independent_roots() -> None:
    assert len(deduplicate_findings([finding(), finding(file="Other.java")])) == 1
    assert len(deduplicate_findings([finding(), finding(root_cause_id="other-root")])) == 2
    assert (
        len(
            deduplicate_findings(
                [finding(root_cause_id=None), finding(root_cause_id=None, line_start=20)]
            )
        )
        == 2
    )


def test_scoring_requires_case_root_location_evidence_and_severity() -> None:
    oracle = [
        {
            "root_cause_id": "snapshot-reprice",
            "file": "Refund.java",
            "line_start": 8,
            "line_end": 12,
            "severity": "must_fix",
        }
    ]
    assert match_roots([finding(), finding()], oracle) == {"tp": 1, "fp": 0, "fn": 0}
    assert match_roots([finding(line_start=30)], oracle) == {"tp": 0, "fp": 1, "fn": 1}
    assert match_roots([finding(severity="concern", blocking=False)], oracle)["fn"] == 1
    assert match_roots([], []) == {"tp": 0, "fp": 0, "fn": 0}


def test_java_sensitive_path_cannot_be_lowered_by_docs(tmp_path: Path) -> None:
    policy = tmp_path / "policy.yaml"
    policy.write_text("""thresholds: {low_max: 2, medium_max: 6}
rules:
  - {id: money, patterns: ['**/Refund*.java'], score: 8, force_human: true}
  - {id: docs, patterns: ['**/*.md'], score: -100}
""")
    decision = RiskRouter(policy).assess(["src/RefundService.java", "docs/README.md"], set())
    assert decision.level is RiskLevel.HIGH
    assert decision.human_review_required
