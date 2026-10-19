import argparse
from pathlib import Path

from review_system.agents import RecordedAgent, ReviewContext
from review_system.pipeline import ReviewMode, ReviewPipeline
from review_system.router import RiskRouter

ROOT = Path(__file__).parents[1]
CASE = ROOT / "book-assets" / "pr-04-concurrent-double-spend"


def build_pipeline() -> ReviewPipeline:
    fixture = CASE / "runs" / "recorded-agents.json"
    names = ["general-review", "correctness", "test", "security", "impact"]
    agents = {name: RecordedAgent(name, fixture) for name in names}
    return ReviewPipeline(RiskRouter(ROOT / "policies" / "risk-rules.yaml"), agents)


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay the PR-04 review experiment")
    parser.add_argument("--mode", choices=[mode.value for mode in ReviewMode], required=True)
    arguments = parser.parse_args()
    context = ReviewContext(
        case_id="PR-04",
        patch_path=CASE / "0001-case-move-balance-update-outside-atomic-boundary.patch",
        changed_paths=["app/repository.py", "app/service.py"],
        semantic_labels={"money", "database-transaction"},
    )
    report = build_pipeline().run(context, ReviewMode(arguments.mode))
    print(report.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
