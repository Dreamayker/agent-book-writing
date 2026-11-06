import json
from pathlib import Path
from urllib.request import Request

import pytest

from review_system.agents import ReviewContext
from review_system.responses_agent import ResponsesReviewAgent


def test_responses_agent_sends_untrusted_patch_and_parses_finding(tmp_path: Path) -> None:
    patch = tmp_path / "change.patch"
    patch.write_text("+ float(amount)\n", encoding="utf-8")
    captured: dict[str, object] = {}

    def transport(request: Request, timeout: float) -> bytes:
        captured["url"] = request.full_url
        captured["authorization"] = request.headers["Authorization"]
        captured["payload"] = json.loads(request.data or b"{}")
        captured["timeout"] = timeout
        finding_batch = {
            "findings": [
                {
                    "finding_id": "MONEY-001",
                    "source": "correctness",
                    "category": "correctness",
                    "severity": "must_fix",
                    "confidence": 0.9,
                    "file": "order-infra/src/main/java/com/example/OrderApplicationService.java",
                    "line_start": 31,
                    "claim": "Money is converted through float",
                    "evidence": [
                        {
                            "type": "source",
                            "ref": (
                                "order-infra/src/main/java/com/example/"
                                "OrderApplicationService.java:31"
                            ),
                        }
                    ],
                    "suggested_fix": "Keep Decimal",
                    "blocking": True,
                    "needs_human": True,
                }
            ]
        }
        response = {
            "id": "response-test",
            "usage": {"input_tokens": 100, "output_tokens": 20},
            "output": [{"content": [{"type": "output_text", "text": json.dumps(finding_batch)}]}],
        }
        return json.dumps(response).encode()

    agent = ResponsesReviewAgent(
        name="correctness",
        specialty="money correctness",
        model="test-model",
        api_key="test-secret",
        base_url="https://example.invalid/v1",
        transport=transport,
    )
    findings = agent.review(
        ReviewContext(
            case_id="ORD-02",
            patch_path=patch,
            changed_paths=["order-infra/src/main/java/com/example/OrderApplicationService.java"],
        )
    )

    assert findings[0].finding_id == "MONEY-001"
    assert agent.last_usage["status"] == "validated"
    assert agent.last_usage["response_id"] == "response-test"
    assert agent.last_usage["usage"] == {"input_tokens": 100, "output_tokens": 20}
    assert captured["url"] == "https://example.invalid/v1/responses"
    assert captured["authorization"] == "Bearer test-secret"
    payload = captured["payload"]
    assert isinstance(payload, dict)
    assert payload["text"]["format"]["type"] == "json_schema"  # type: ignore[index]
    assert "untrusted_patch" in payload["input"]  # type: ignore[operator]


def test_live_agent_rejects_empty_api_key() -> None:
    with pytest.raises(ValueError, match="api_key is required"):
        ResponsesReviewAgent(name="security", specialty="security", model="test", api_key="")


def test_live_failure_preserves_status_and_elapsed_time(tmp_path: Path) -> None:
    patch = tmp_path / "change.patch"
    patch.write_text("+ change\n")

    def transport(request: Request, timeout: float) -> bytes:
        raise TimeoutError("simulated timeout")

    agent = ResponsesReviewAgent(
        name="test",
        specialty="test",
        model="test-model",
        api_key="test-secret",
        transport=transport,
    )
    with pytest.raises(TimeoutError):
        agent.review(ReviewContext(case_id="ORD-09", patch_path=patch, changed_paths=[]))
    assert agent.last_usage["status"] == "failed"
    assert agent.last_usage["elapsed_seconds"] >= 0
