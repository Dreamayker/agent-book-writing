from dataclasses import dataclass
from pathlib import Path

import yaml

from evaluation.scoring import FindingMetrics, score_finding_ids
from review_system.agents import RecordedAgent, ReviewContext
from review_system.pipeline import ReviewMode, ReviewPipeline
from review_system.router import RiskRouter

ROOT = Path(__file__).parents[1]
AGENT_NAMES = ["general-review", "correctness", "test", "security", "impact"]


@dataclass(frozen=True)
class CaseDefinition:
    directory: str
    patch: str
    changed_paths: list[str]
    labels: set[str]


CASES = [
    CaseDefinition(
        "pr-02-money-precision",
        "0001-case-introduce-float-money-normalization.patch",
        ["app/service.py"],
        {"money"},
    ),
    CaseDefinition(
        "pr-03-object-authorization",
        "0001-case-omit-source-wallet-ownership-check.patch",
        ["app/service.py"],
        {"authorization"},
    ),
    CaseDefinition(
        "pr-04-concurrent-double-spend",
        "0001-case-move-balance-update-outside-atomic-boundary.patch",
        ["app/repository.py", "app/service.py"],
        {"money", "database-transaction"},
    ),
    CaseDefinition(
        "pr-05-idempotency-retry",
        "0001-case-remove-idempotent-retry-lookup.patch",
        ["app/service.py"],
        {"money", "database-transaction"},
    ),
    CaseDefinition(
        "pr-07-vulnerable-dependency",
        "0001-case-downgrade-requests-to-vulnerable-release.patch",
        ["dependency-audit/requirements.txt"],
        set(),
    ),
    CaseDefinition(
        "pr-08-prompt-injection",
        "0001-case-embed-review-instructions-in-source-comment.patch",
        ["app/service.py"],
        {"authorization"},
    ),
]


def evaluate_recorded_suite(mode: ReviewMode) -> FindingMetrics:
    all_findings = []
    expected_ids: set[str] = set()
    router = RiskRouter(ROOT / "policies" / "risk-rules.yaml")
    for case in CASES:
        case_path = ROOT / "book-assets" / case.directory
        fixture = case_path / "runs" / "recorded-agents.json"
        agents = {name: RecordedAgent(name, fixture) for name in AGENT_NAMES}
        oracle = yaml.safe_load((case_path / "oracle.yaml").read_text(encoding="utf-8"))
        expected_ids.update(item["id"] for item in oracle["findings"])
        context = ReviewContext(
            case_id=str(oracle["case_id"]),
            patch_path=case_path / case.patch,
            changed_paths=case.changed_paths,
            semantic_labels=case.labels,
        )
        all_findings.extend(ReviewPipeline(router, agents).run(context, mode).findings)
    return score_finding_ids(all_findings, expected_ids)
