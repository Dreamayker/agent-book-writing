from collections.abc import Mapping
from enum import StrEnum

from pydantic import BaseModel

from review_system.adjudication import arbitrate, deduplicate_findings
from review_system.agents import ReviewAgent, ReviewContext
from review_system.router import RiskRouter
from review_system.schemas import Finding, RiskDecision, RiskLevel


class ReviewMode(StrEnum):
    SINGLE = "single"
    MULTI = "multi"
    MULTI_ARBITRATED = "multi_arbitrated"


class ReviewReport(BaseModel):
    case_id: str
    mode: ReviewMode
    risk: RiskDecision
    agents_run: list[str]
    findings: list[Finding]
    verdict: str


class ReviewPipeline:
    def __init__(self, router: RiskRouter, agents: Mapping[str, ReviewAgent]) -> None:
        self._router = router
        self._agents = agents

    def run(self, context: ReviewContext, mode: ReviewMode) -> ReviewReport:
        risk = self._router.assess(context.changed_paths, context.semantic_labels)
        agent_names = self._select_agents(risk, mode)
        findings = [
            finding
            for agent_name in agent_names
            for finding in self._agents[agent_name].review(context)
        ]

        if mode is ReviewMode.MULTI_ARBITRATED:
            findings = deduplicate_findings(findings)

        # Review depth may change by mode, but policy gates may not.
        verdict = arbitrate(findings, high_risk=risk.level is RiskLevel.HIGH)

        return ReviewReport(
            case_id=context.case_id,
            mode=mode,
            risk=risk,
            agents_run=agent_names,
            findings=findings,
            verdict=verdict,
        )

    def _select_agents(self, risk: RiskDecision, mode: ReviewMode) -> list[str]:
        if mode is ReviewMode.SINGLE:
            return ["general-review"]
        return [name for name in risk.required_agents if name != "arbitrator"]
