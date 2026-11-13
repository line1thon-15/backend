"""T-15가 ports.py를 고치며 생기는 회귀 확인.

- 옛 모델 이름 3개가 되살아나지 않음(T-86 리뷰 권고 #3 — 이름을 파일에 그대로 적지 않고 조각으로 만든다).
- F-11 ⑥: AI `turn` 응답에 `is_terminal`이 실려 와도 파싱은 성공하고 값은 남지 않는다
  (`HttpPracticeAI`는 아직 없어 — 범위 밖 — 같은 응답 모델 `TurnResponse`로 확인).
- `AIUnavailableError`는 포트 모듈에 있어 services가 포트만 import하고 잡을 수 있다.
"""

import json
from pathlib import Path

import pytest

from app.ai_client import ports
from app.ai_client.ports import AIUnavailableError, TurnResponse

CONTRACTS = Path(__file__).resolve().parents[1] / "contracts" / "ai"

_OLD_NAME_PARTS = [("Scenario", "Spec"), ("Turn", "Result"), ("Opening", "Result")]


@pytest.mark.parametrize("parts", _OLD_NAME_PARTS, ids=lambda p: "".join(p)[:3])
def test_old_model_names_do_not_come_back(parts):
    assert not hasattr(ports, "".join(parts))


@pytest.mark.parametrize("is_terminal", [True, False])
def test_turn_response_drops_is_terminal(is_terminal):
    sample = json.loads((CONTRACTS / "practice.turn.response.json").read_text(encoding="utf-8"))
    sample["is_terminal"] = is_terminal

    parsed = TurnResponse.model_validate(sample)

    assert "is_terminal" not in parsed.model_dump()
    assert not hasattr(parsed, "is_terminal")


def test_ai_unavailable_error_is_an_exception():
    assert issubclass(AIUnavailableError, Exception)
    assert str(AIUnavailableError("turn failed")) == "turn failed"
