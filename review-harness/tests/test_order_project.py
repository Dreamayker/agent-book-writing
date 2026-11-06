from pathlib import Path

import pytest

from evaluation.projects import replay_project
from review_system.pipeline import ReviewMode

MANIFEST = Path(__file__).resolve().parents[2] / "order-review-lab/evaluation/cases.yaml"


@pytest.mark.parametrize("mode", list(ReviewMode))
def test_order_fixture_replay_preserves_case_identity_and_policy(mode: ReviewMode) -> None:
    report = replay_project(MANIFEST, mode)
    assert report["kind"] == "recorded-control-fixture"
    assert len(report["cases"]) == 12
    assert report["cases"][0]["verdict"] == "approve"
    refund = next(case for case in report["cases"] if case["case_id"] == "ORD-09")
    assert refund["verdict"] == "escalate"
    if mode is ReviewMode.SINGLE:
        assert report["totals"] == {"tp": 0, "fp": 0, "fn": 11}
    else:
        assert report["totals"] == {"tp": 11, "fp": 0, "fn": 0}
        assert refund["findings"] == (1 if mode is ReviewMode.MULTI_ARBITRATED else 2)
