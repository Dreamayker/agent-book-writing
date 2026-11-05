from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class Severity(StrEnum):
    MUST_FIX = "must_fix"
    CONCERN = "concern"
    NITPICK = "nitpick"


class EvidenceType(StrEnum):
    SOURCE = "source"
    TEST = "test"
    STATIC_ANALYSIS = "static_analysis"
    DEPENDENCY_SCAN = "dependency_scan"
    POLICY = "policy"


class Evidence(BaseModel):
    type: EvidenceType
    ref: str = Field(min_length=1)


class Finding(BaseModel):
    schema_version: int = Field(default=2, ge=2, le=2)
    root_cause_id: str | None = None
    invariant: str | None = None
    symbol: str | None = None
    finding_id: str = Field(pattern=r"^[A-Z][A-Z0-9_-]+-\d{3}$")
    source: str = Field(min_length=1)
    category: str = Field(min_length=1)
    severity: Severity
    confidence: float = Field(ge=0, le=1)
    file: str = Field(min_length=1)
    line_start: int = Field(ge=1)
    line_end: int | None = Field(default=None, ge=1)
    claim: str = Field(min_length=1)
    evidence: list[Evidence] = Field(default_factory=list)
    suggested_fix: str | None = None
    blocking: bool = False
    needs_human: bool = False

    @model_validator(mode="after")
    def blocking_findings_require_evidence(self) -> "Finding":
        if self.line_end is not None and self.line_end < self.line_start:
            raise ValueError("line_end must be at or after line_start")
        if self.blocking and not self.evidence:
            raise ValueError("blocking findings require at least one evidence item")
        if self.blocking and self.severity is not Severity.MUST_FIX:
            raise ValueError("only must_fix findings may block a pull request")
        return self


class FindingBatch(BaseModel):
    findings: list[Finding]


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RiskDecision(BaseModel):
    score: int
    level: RiskLevel
    matched_rules: list[str]
    required_agents: list[str]
    human_review_required: bool
