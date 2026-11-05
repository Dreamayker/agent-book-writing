"""Verify controller-produced evidence before giving it to a model or policy gate."""

import hashlib
import json
from pathlib import Path
from typing import Any

from review_system.agents import ReviewContext
from review_system.schemas import EvidenceType, Finding


def checked_path(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    if not candidate.is_relative_to(root.resolve()):
        raise ValueError("path escapes project root")
    return candidate


def verified_evidence(context: ReviewContext) -> dict[str, Any]:
    if context.evidence_manifest is None:
        return {}
    if context.project_root is None or not context.code_revision:
        raise ValueError("evidence requires project root and code revision")
    manifest: dict[str, Any] = json.loads(context.evidence_manifest.read_text())
    if manifest["case_id"] != context.case_id or manifest["code_revision"] != context.code_revision:
        raise ValueError("evidence belongs to a different case or code revision")
    if not manifest.get("run_id"):
        raise ValueError("evidence requires run ID")
    for entry in manifest["files"]:
        path = checked_path(context.project_root, entry["path"])
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError("evidence hash mismatch")
        entry["content"] = path.read_text(encoding="utf-8")
    return manifest


def validate_references(context: ReviewContext, findings: list[Finding]) -> None:
    manifest = verified_evidence(context)
    if not manifest:
        return  # Historical wallet fixtures use their original evidence contract.
    allowed = {entry["path"] for entry in manifest["files"]}
    for finding in findings:
        for evidence in finding.evidence:
            if (
                evidence.type is not EvidenceType.SOURCE
                and evidence.ref.split("#", 1)[0] not in allowed
            ):
                raise ValueError("finding references evidence outside this run")
