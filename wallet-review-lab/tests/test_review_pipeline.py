from pathlib import Path

import pytest

from review_system.agents import RecordedAgent, ReviewContext
from review_system.pipeline import ReviewMode, ReviewPipeline
from review_system.router import RiskRouter

ROOT = Path(__file__).parents[1]
CASE = ROOT / "book-assets" / "pr-04-concurrent-double-spend"
FIXTURE = CASE / "runs" / "recorded-agents.json"
PATCH = CASE / "0001-case-move-balance-update-outside-atomic-boundary.patch"


@pytest.fixture
def pipeline() -> ReviewPipeline:
    names = ["general-review", "correctness", "test", "security", "impact"]
    agents = {name: RecordedAgent(name, FIXTURE) for name in names}
    return ReviewPipeline(RiskRouter(ROOT / "policies" / "risk-rules.yaml"), agents)


@pytest.fixture
def context() -> ReviewContext:
    return ReviewContext(
        case_id="PR-04",
        patch_path=PATCH,
        changed_paths=["app/repository.py", "app/service.py"],
        semantic_labels={"money", "database-transaction"},
    )


def test_single_agent_misses_double_spend_root_cause(
    pipeline: ReviewPipeline, context: ReviewContext
) -> None:
    report = pipeline.run(context, ReviewMode.SINGLE)
    assert report.verdict == "escalate"
    assert {finding.finding_id for finding in report.findings} == {"PERF-001"}


def test_multi_agent_finds_duplicate_root_cause_reports(
    pipeline: ReviewPipeline, context: ReviewContext
) -> None:
    report = pipeline.run(context, ReviewMode.MULTI)
    assert report.verdict == "escalate"
    assert [finding.finding_id for finding in report.findings].count("CONCURRENCY-001") == 2


def test_arbitration_merges_evidence_and_escalates_high_risk(
    pipeline: ReviewPipeline, context: ReviewContext
) -> None:
    report = pipeline.run(context, ReviewMode.MULTI_ARBITRATED)
    assert report.verdict == "escalate"
    assert len(report.findings) == 1
    assert len(report.findings[0].evidence) == 2
    assert report.risk.human_review_required


def test_documentation_only_case_uses_quiet_approval_path() -> None:
    case = ROOT / "book-assets" / "pr-01-documentation-only"
    fixture = case / "runs" / "recorded-agents.json"
    agents = {"general-review": RecordedAgent("general-review", fixture)}
    pipeline = ReviewPipeline(RiskRouter(ROOT / "policies" / "risk-rules.yaml"), agents)
    report = pipeline.run(
        ReviewContext(
            case_id="PR-01",
            patch_path=case / "0001-docs-clarify-transfer-response-identifier.patch",
            changed_paths=["README.md"],
        ),
        ReviewMode.SINGLE,
    )
    assert report.risk.level.value == "low"
    assert report.agents_run == ["general-review"]
    assert report.findings == []
    assert report.verdict == "approve"
