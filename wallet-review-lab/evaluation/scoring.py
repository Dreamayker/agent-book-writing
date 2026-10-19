from pydantic import BaseModel

from review_system.schemas import Finding


class FindingMetrics(BaseModel):
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float


def score_finding_ids(findings: list[Finding], expected_ids: set[str]) -> FindingMetrics:
    predicted_ids = {finding.finding_id for finding in findings}
    true_positives = len(predicted_ids & expected_ids)
    false_positives = len(predicted_ids - expected_ids)
    false_negatives = len(expected_ids - predicted_ids)
    precision = true_positives / len(predicted_ids) if predicted_ids else 0.0
    recall = true_positives / len(expected_ids) if expected_ids else 1.0
    return FindingMetrics(
        true_positives=true_positives,
        false_positives=false_positives,
        false_negatives=false_negatives,
        precision=precision,
        recall=recall,
    )
