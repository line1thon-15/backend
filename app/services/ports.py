from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domain.guardian_report import EndedSession
from app.domain.weak_cues import CueOutcome


class DatabaseProbe(Protocol):
    def ping(self) -> bool: ...


@dataclass(frozen=True)
class GuardianCredentials:
    guardian_id: UUID
    password_hash: str


@dataclass(frozen=True)
class ChildLoginCredentials:
    child_id: UUID
    pin_hash: str
    first_login: bool


@dataclass(frozen=True)
class ChildRegistrationRecord:
    child_id: UUID
    nickname: str
    grade: str
    link_code: str


@dataclass(frozen=True)
class ChildSummary:
    child_id: UUID
    nickname: str
    grade: str


class AuthRepository(Protocol):
    def find_guardian_by_email(self, email: str) -> GuardianCredentials | None: ...

    def create_guardian_with_session(
        self,
        email: str,
        password_hash: str,
        token_hash: str,
        expires_at: datetime,
    ) -> UUID | None: ...

    def create_guardian_session(
        self,
        guardian_id: UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> None: ...

    def find_guardian_id_for_active_session(
        self,
        token_hash: str,
        now: datetime,
    ) -> UUID | None: ...

    def find_child_id_for_active_session(
        self,
        token_hash: str,
        now: datetime,
    ) -> UUID | None: ...

    def find_child_by_link_code(
        self,
        link_code: str,
    ) -> ChildLoginCredentials | None: ...

    def create_child_session(
        self,
        child_id: UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> None: ...

    def has_children(self, guardian_id: UUID) -> bool: ...


class ChildrenRepository(Protocol):
    def create_child(
        self,
        guardian_id: UUID,
        nickname: str,
        grade: str,
        pin_hash: str,
        consent_version: str,
        link_code: str,
    ) -> ChildRegistrationRecord | None: ...

    def list_children_for_guardian(
        self,
        guardian_id: UUID,
    ) -> list[ChildSummary]: ...

    def reset_child_pin(
        self,
        guardian_id: UUID,
        child_id: UUID,
        pin_hash: str,
        revoked_at: datetime,
    ) -> bool: ...

    def replace_child_link_code(
        self,
        guardian_id: UUID,
        child_id: UUID,
        link_code: str,
        revoked_at: datetime,
    ) -> bool | None: ...

class OnboardingRepository(Protocol):
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
    ) -> bool: ...


# ---- 연습 (T-15) ----------------------------------------------------------------


class PracticeStateConflict(Exception):
    """저장 시점에 세션이 이미 진행 중이 아니거나 그 턴에 이미 답이 기록됨 — 같은 세션 동시 요청."""


@dataclass(frozen=True)
class PracticeChildProfile:
    grade: str
    favorite_apps: tuple[str, ...]


@dataclass(frozen=True)
class PracticeTurnRecord:
    turn_index: int
    ai_line: str
    choices: tuple[dict, ...]  # [{id, text, kind}] — kind는 공개 응답에 싣지 않는다
    chosen_choice_id: str | None
    substituted: bool
    target_clue_id: str | None
    revealed_clue_ids: tuple[str, ...]
    ai_status: str


@dataclass(frozen=True)
class PracticeSessionRecord:
    session_id: UUID
    child_id: UUID
    mode: str
    area: str
    scenario_id: str
    is_normal: bool
    target_cue_ids: tuple[str, ...]
    variant: dict
    ai_role_name: str
    retry_of: UUID | None
    status: str
    turns: tuple[PracticeTurnRecord, ...]
    normal_outcome: str | None = None  # 정상 상황 종료 세션만 (T-16 결과 level K4·K5)


@dataclass(frozen=True)
class NewPracticeSession:
    child_id: UUID
    mode: str
    area: str
    subtype: str | None
    scenario_id: str
    is_normal: bool
    target_cue_ids: tuple[str, ...]
    variant: dict
    scenario_title: str
    child_setup: str
    ai_role_name: str
    draw_index: int | None
    started_at: datetime
    retry_of: UUID | None = None  # 다시 도전이면 직전 세션 (T-16, F-13 ③)


@dataclass(frozen=True)
class NewPracticeTurn:
    turn_index: int
    ai_line: str
    choices: tuple[dict, ...]
    substituted: bool
    target_clue_id: str | None
    revealed_clue_ids: tuple[str, ...]
    ai_status: str


@dataclass(frozen=True)
class NewCueResult:
    cue_id: str
    outcome: str  # found | missed


class PracticeRepository(Protocol):
    def get_child_profile(self, child_id: UUID) -> PracticeChildProfile | None: ...

    def latest_variant_axes(
        self,
        child_id: UUID,
        scenario_ids: list[str],
    ) -> dict[str, tuple[str, str]]: ...

    def count_new_draws(self, child_id: UUID) -> int: ...

    def create_session(
        self,
        session: NewPracticeSession,
        first_turn: NewPracticeTurn,
    ) -> UUID: ...

    def get_session(
        self,
        session_id: UUID,
        child_id: UUID,
    ) -> PracticeSessionRecord | None: ...

    def get_cue_results(self, session_id: UUID) -> dict[str, str]: ...

    def record_answer_and_continue(
        self,
        *,
        session_id: UUID,
        answered_turn_index: int,
        chosen_choice_id: str,
        next_turn: NewPracticeTurn,
    ) -> None: ...

    def record_answer_and_end(
        self,
        *,
        session_id: UUID,
        child_id: UUID,
        answered_turn_index: int,
        chosen_choice_id: str,
        cue_results: list[NewCueResult],
        ended_at: datetime,
    ) -> None: ...

    def record_answer_and_stop(
        self,
        *,
        session_id: UUID,
        answered_turn_index: int,
        chosen_choice_id: str,
        stop_turn: NewPracticeTurn,
        stopped_at: datetime,
    ) -> None: ...


# ---- 보호자 리포트 (T-25) ---------------------------------------------------------
# 보호자 경로 — practice_turns를 읽는 메서드를 두지 않는다 (Architecture 엔티티 practice_turns, F-30 ③).


@dataclass(frozen=True)
class ReportChild:
    child_id: UUID
    nickname: str


@dataclass(frozen=True)
class GuardianNoticeRecord:
    """guardian_notices 한 행 — NoticeView 6개 값만(origin은 싣지 않는다)."""

    notice_id: UUID
    kind: str
    occurred_at: datetime  # UTC aware
    level: str | None
    area: str | None
    channel: str | None


class GuardianReportRepository(Protocol):
    def get_owned_child(self, guardian_id: UUID, child_id: UUID) -> ReportChild | None:
        """보호자와 아이 두 조건을 한 쿼리로 — 없거나 남의 아이면 None (Architecture 인가 — 보호자)."""
        ...

    def ended_sessions(self, child_id: UUID) -> list[EndedSession]: ...

    def ended_cue_outcomes(self, child_id: UUID) -> list[CueOutcome]:
        """`status = ended` 세션의 단서 판정 목록 — 판정 시각은 그 세션의 종료 시각, session_id 포함(#122 동률)."""
        ...

    def notices(self, child_id: UUID) -> list[GuardianNoticeRecord]:
        """그 아이의 알림 — 최신 순(occurred_at 내림차순, 같으면 id 내림차순)."""
        ...
