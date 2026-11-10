from app.ai_client.fake import FakePracticeAI
from app.ai_client.ports import PracticeAI
from app.core.config import Settings


def build_practice_ai(settings: Settings) -> PracticeAI:
    if settings.ai_client == "fake":
        return FakePracticeAI()
    raise NotImplementedError("AI_CLIENT=http requires HttpPracticeAI, which is not implemented yet")
