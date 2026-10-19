from evaluation.suite import evaluate_recorded_suite
from review_system.pipeline import ReviewMode


def test_recorded_single_agent_baseline_misses_standard_findings() -> None:
    metrics = evaluate_recorded_suite(ReviewMode.SINGLE)
    assert metrics.true_positives == 0
    assert metrics.false_negatives == 6


def test_recorded_multi_agent_control_plane_recovers_standard_findings() -> None:
    metrics = evaluate_recorded_suite(ReviewMode.MULTI_ARBITRATED)
    assert metrics.true_positives == 6
    assert metrics.false_positives == 0
    assert metrics.false_negatives == 0
    assert metrics.precision == 1
    assert metrics.recall == 1
