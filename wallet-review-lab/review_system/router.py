from fnmatch import fnmatch
from pathlib import Path
from typing import Any

import yaml

from review_system.schemas import RiskDecision, RiskLevel


class RiskRouter:
    def __init__(self, policy_path: Path) -> None:
        raw = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("risk policy must be a mapping")
        self._policy: dict[str, Any] = raw

    def assess(self, changed_paths: list[str], semantic_labels: set[str]) -> RiskDecision:
        score = 0
        matched: list[str] = []
        for rule in self._policy.get("rules", []):
            patterns = rule.get("patterns", [])
            if any(self._matches(path, pattern) for path in changed_paths for pattern in patterns):
                score += int(rule["score"])
                matched.append(str(rule["id"]))

        mandatory_labels = set(self._policy.get("mandatory_human_review", []))
        human_required = bool(semantic_labels & mandatory_labels)
        if human_required:
            matched.append("mandatory-human-review")

        thresholds = self._policy["thresholds"]
        if score <= int(thresholds["low_max"]):
            level = RiskLevel.LOW
            agents = ["general-review"]
        elif score <= int(thresholds["medium_max"]):
            level = RiskLevel.MEDIUM
            agents = ["correctness", "test"]
        else:
            level = RiskLevel.HIGH
            agents = ["correctness", "test", "security", "impact", "arbitrator"]

        if human_required:
            level = RiskLevel.HIGH
            agents = ["correctness", "test", "security", "impact", "arbitrator"]

        return RiskDecision(
            score=score,
            level=level,
            matched_rules=matched,
            required_agents=agents,
            human_review_required=human_required,
        )

    @staticmethod
    def _matches(path: str, pattern: str) -> bool:
        if pattern.startswith("**/") and fnmatch(path, pattern[3:]):
            return True
        return fnmatch(path, pattern)
