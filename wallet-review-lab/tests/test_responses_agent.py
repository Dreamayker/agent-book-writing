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
                    "file": "app/service.py",
                    "line_start": 31,
                    "claim": "Money is converted through float",
                    "evidence": [{"type": "source", "ref": "app/service.py:31"}],
                    "suggested_fix": "Keep Decimal",
                    "blocking": True,
                    "needs_human": True,
                }
            ]
        }
        response = {
            "output": [
                {
                    "content": [
                        {"type": "output_text", "text": json.dumps(finding_batch)}
                    ]
                }
            ]
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
        ReviewContext(case_id="PR-02", patch_path=patch, changed_paths=["app/service.py"])
    )

    assert findings[0].finding_id == "MONEY-001"
    assert captured["url"] == "https://example.invalid/v1/responses"
    assert captured["authorization"] == "Bearer test-secret"
    payload = captured["payload"]
    assert isinstance(payload, dict)
    assert payload["text"]["format"]["type"] == "json_schema"  # type: ignore[index]
    assert "untrusted_patch" in payload["input"]  # type: ignore[operator]


def test_live_agent_rejects_empty_api_key() -> None:
    with pytest.raises(ValueError, match="api_key is required"):
        ResponsesReviewAgent(name="security", specialty="security", model="test", api_key="")
