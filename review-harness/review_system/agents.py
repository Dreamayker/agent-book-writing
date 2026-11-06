import json
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, Field

from review_system.schemas import Finding


class ReviewContext(BaseModel):
    case_id: str
    patch_path: Path
    changed_paths: list[str]
    semantic_labels: set[str] = Field(default_factory=set)
    project_root: Path | None = None
    code_revision: str | None = None
    requirements: str = ""
    evidence_manifest: Path | None = None


class ReviewAgent(Protocol):
    @property
    def name(self) -> str: ...

    def review(self, context: ReviewContext) -> list[Finding]: ...


class RecordedAgent:
    """Offline adapter for deterministic book reproduction.

    Recorded output is explicitly test data. It exercises orchestration but is
    never presented as a fresh model judgment.
    """

    def __init__(self, name: str, fixture_path: Path) -> None:
        self._name = name
        raw = json.loads(fixture_path.read_text(encoding="utf-8"))
        self._findings = [Finding.model_validate(item) for item in raw.get(name, [])]

    @property
    def name(self) -> str:
        return self._name

    def review(self, context: ReviewContext) -> list[Finding]:
        if not context.patch_path.exists():
            raise FileNotFoundError(context.patch_path)
        return [finding.model_copy(deep=True) for finding in self._findings]
