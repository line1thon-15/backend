from collections.abc import Mapping, Sequence

from app.ai_client.fake import FakePracticeAI
from app.ai_client.http_client import HttpPracticeAI
from app.ai_client.ports import PracticeAI
from app.core.config import AIServiceSettings, Settings


def build_practice_ai(
    settings: Settings,
    scenario_clue_ids: Mapping[str, Sequence[str]] | None = None,
    ai_service_settings: AIServiceSettings | None = None,
) -> PracticeAI:
    if settings.ai_client == "fake":
        # scenario_id → 콘텐츠 단서 ID — dev 서버·E2E에서 Fake 변형이 VA2 검증을 통과하게 (T-15)
        return FakePracticeAI(scenario_clue_ids=scenario_clue_ids)
    # AI_CLIENT=http (T-94) — AI_SERVICE_* 는 http일 때만 읽는다. 토큰이 없으면 여기서 바로 실패한다.
    return HttpPracticeAI.from_settings(ai_service_settings or AIServiceSettings())
