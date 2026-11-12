from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID


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


@dataclass(frozen=True)
class EndedSessionStats:
    """성장 지표용 종료 세션 집계 (T-46) — practice_sessions·cue_results만, 문장·선택지 없음."""

    session_id: UUID
    scenario_id: str
    mode: str
    is_normal: bool
    ended_at: datetime  # UTC
    found: int
    missed: int


@dataclass(frozen=True)
class FirstAnswerKind:
    """첫 답(turn_index 0)에서 고른 선택지의 kind — 보호자 경로 practice_turns 예외의 유일한 반환형
    (ADR-0016 R1, DECISIONS #93). 문자열 내용 필드를 더하지 않는다."""

    session_id: UUID
    kind: str


@dataclass(frozen=True)
class EndedCueOutcome:
    """종료 세션의 단서 판정 1건 (T-46 더 연습이 필요한 단서) — cue_results만."""

    cue_id: str
    outcome: str  # found | missed
    ended_at: datetime  # UTC — 세션 종료 시각
    session_id: UUID


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

    # ---- 성장 지표 (T-46) — 아이(A19)·보호자(A11) 경로 공통 ----

    def ended_session_stats(
        self,
        child_id: UUID,
        ended_from: datetime,
        ended_to: datetime,
    ) -> list[EndedSessionStats]: ...

    def first_session_ids(
        self,
        child_id: UUID,
        scenario_ids: list[str],
    ) -> dict[str, UUID]: ...

    def first_answer_kinds(
        self,
        child_id: UUID,
        ended_from: datetime,
        ended_to: datetime,
    ) -> list[FirstAnswerKind]: ...

    def ended_cue_outcomes(self, child_id: UUID) -> list[EndedCueOutcome]: ...
