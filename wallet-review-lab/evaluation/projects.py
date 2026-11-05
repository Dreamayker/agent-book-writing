"""Manifest-driven replay, with per-case root/location scoring and isolated Oracle."""

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from review_system.agents import RecordedAgent, ReviewContext
from review_system.evidence import checked_path
from review_system.pipeline import ReviewMode, ReviewPipeline
from review_system.router import RiskRouter
from review_system.schemas import Finding

AGENTS = ["general-review", "correctness", "test", "security", "impact"]


def match_roots(findings: list[Finding], oracle: list[dict[str, Any]]) -> dict[str, int]:
    remaining = list(oracle)
    false_positives = 0
    matched: set[tuple[str, str, str]] = set()
    for finding in findings:
        key = (finding.root_cause_id or finding.finding_id, finding.file, finding.symbol or "")
        if key in matched:
            continue
        match = next(
            (
                item
                for item in remaining
                if (
                    item["root_cause_id"] == key[0]
                    and item["file"] == finding.file
                    and item["line_start"] <= finding.line_start <= item["line_end"]
                    and finding.severity.value == item["severity"]
                    and bool(finding.evidence)
                )
            ),
            None,
        )
        if match:
            remaining.remove(match)
            matched.add(key)
        else:
            false_positives += 1
    return {"tp": len(oracle) - len(remaining), "fp": false_positives, "fn": len(remaining)}


def replay_project(manifest_path: Path, mode: ReviewMode) -> dict[str, Any]:
    manifest = yaml.safe_load(manifest_path.read_text())
    root = checked_path(manifest_path.parent.parent, manifest.get("project_root", "."))
    router = RiskRouter(checked_path(root, manifest["policy"]))
    results = []
    for case in manifest["cases"]:
        directory = checked_path(root, case["directory"])
        fixture = directory / "runs" / "recorded-agents.json"
        agents = {name: RecordedAgent(name, fixture) for name in AGENTS}
        context = ReviewContext(
            case_id=case["id"],
            patch_path=directory / "buggy.patch",
            changed_paths=case["changed_paths"],
            semantic_labels=set(case["labels"]),
            project_root=root,
            code_revision=case["code_revision"],
            requirements=(directory / "requirement.md").read_text(),
            evidence_manifest=directory / "tool-evidence" / "manifest.json",
        )
        report = ReviewPipeline(router, agents).run(context, mode)
        # Read expected answers only after review. Nothing from Oracle enters ReviewContext.
        oracle = yaml.safe_load((directory / "oracle.yaml").read_text())["findings"]
        results.append(
            {
                "case_id": case["id"],
                "verdict": report.verdict,
                "findings": len(report.findings),
                **match_roots(report.findings, oracle),
            }
        )
    totals = {key: sum(case[key] for case in results) for key in ("tp", "fp", "fn")}
    return {
        "kind": "recorded-control-fixture",
        "mode": mode.value,
        "cases": results,
        "totals": totals,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--mode", type=ReviewMode, default=ReviewMode.MULTI_ARBITRATED)
    args = parser.parse_args()
    print(
        json.dumps(replay_project(args.manifest.resolve(), args.mode), ensure_ascii=False, indent=2)
    )
