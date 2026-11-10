from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session, sessionmaker

from app.db.models import Child, ChildSettings
from app.services.ports import OnboardingRepository


class SqlAlchemyOnboardingRepository(OnboardingRepository):
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def save_onboarding(
        self,
        *,
        child_id: UUID,
        font_scale: str,
        high_contrast: bool,
        tts_enabled: bool,
        trusted_contact_name: str | None,
        trusted_contact_phone: str | None,
        favorite_apps: list[str],
        start_difficulty: int,
        completed_at: datetime,
    ) -> bool:
        with self._session_factory.begin() as session:
            child = session.get(Child, child_id)
            if child is None:
                return False

            settings = session.get(ChildSettings, child_id)
            if settings is None:
                settings = ChildSettings(child_id=child_id)
                session.add(settings)

            settings.font_scale = font_scale
            settings.high_contrast = high_contrast
            settings.tts_enabled = tts_enabled
            settings.trusted_contact_name = trusted_contact_name
            settings.trusted_contact_phone = trusted_contact_phone
            settings.favorite_apps = favorite_apps

            child.start_difficulty = start_difficulty
            child.onboarding_completed_at = completed_at

        return True
