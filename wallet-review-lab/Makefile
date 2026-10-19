.PHONY: check test lint typecheck replay-pr04 evaluate-recorded

check: lint typecheck test

test:
	uv run pytest

lint:
	uv run ruff check .

typecheck:
	uv run mypy app review_system evaluation

replay-pr04:
	uv run python -m evaluation.replay_pr04 --mode single
	uv run python -m evaluation.replay_pr04 --mode multi
	uv run python -m evaluation.replay_pr04 --mode multi_arbitrated

evaluate-recorded:
	uv run pytest tests/test_evaluation_suite.py -q
