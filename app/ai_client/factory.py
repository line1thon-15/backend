from collections.abc import Mapping, Sequence

from app.ai_client.fake import FakePracticeAI
from app.ai_client.ports import PracticeAI
from app.core.config import Settings


def build_practice_ai(
    settings: Settings,
    scenario_clue_ids: Mapping[str, Sequence[str]] | None = None,
) -> PracticeAI:
    if settings.ai_client == "fake":
        # scenario_id → 콘텐츠 단서 ID — dev 서버·E2E에서 Fake 변형이 VA2 검증을 통과하게 (T-15)
        return FakePracticeAI(scenario_clue_ids=scenario_clue_ids)
    raise NotImplementedError("AI_CLIENT=http requires HttpPracticeAI, which is not implemented yet")
