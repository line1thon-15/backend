from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Guardian(Base):
    __tablename__ = "guardians"
    __table_args__ = (
        UniqueConstraint("email", name="uq_guardians_email"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class Child(Base):
    __tablename__ = "children"
    __table_args__ = (
        UniqueConstraint("link_code", name="uq_children_link_code"),
        CheckConstraint(
            "grade IN ('E6', 'M1', 'M2', 'M3', 'H1', 'H2', 'H3')",
            name="ck_children_grade",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    guardian_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("guardians.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    nickname: Mapped[str] = mapped_column(String(20), nullable=False)
    grade: Mapped[str] = mapped_column(String(2), nullable=False)
    link_code: Mapped[str] = mapped_column(String(6), nullable=False)
    pin_hash: Mapped[str] = mapped_column(Text, nullable=False)
    consent_agreed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    consent_version: Mapped[str] = mapped_column(String(20), nullable=False)
    onboarding_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    start_difficulty: Mapped[int | None] = mapped_column(
        SmallInteger,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class ChildSettings(Base):
    __tablename__ = "child_settings"
    __table_args__ = (
        CheckConstraint(
            "font_scale IN ('normal', 'large', 'xlarge')",
            name="ck_child_settings_font_scale",
        ),
    )

    child_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("children.id", ondelete="CASCADE"),
        primary_key=True,
    )
    font_scale: Mapped[str] = mapped_column(
        String(16),
        default="normal",
        nullable=False,
    )
    high_contrast: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    tts_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    trusted_contact_name: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    trusted_contact_phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    favorite_apps: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        server_default=text("'[]'"),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_auth_sessions_token_hash"),
        CheckConstraint(
            "subject_type IN ('guardian', 'child')",
            name="ck_auth_sessions_subject_type",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    subject_type: Mapped[str] = mapped_column(String(16), nullable=False)
    subject_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class PracticeSession(Base):
    """연습 세션 (Architecture 엔티티 practice_sessions — 2026-11-11 AI 계약 채택 변경 포함, DECISIONS #98·#99)."""

    __tablename__ = "practice_sessions"
    __table_args__ = (
        CheckConstraint("mode IN ('area', 'mission', 'retry')", name="ck_practice_sessions_mode"),
        CheckConstraint(
            "area IN ('scam', 'identity_lending', 'friend_pressure')",
            name="ck_practice_sessions_area",
        ),
        CheckConstraint(
            "subtype IS NULL OR subtype IN ('game_item', 'allowance', 'high_paying_job')",
            name="ck_practice_sessions_subtype",
        ),
        CheckConstraint(
            "status IN ('in_progress', 'ended', 'stopped')",
            name="ck_practice_sessions_status",
        ),
        CheckConstraint(
            "normal_outcome IS NULL OR normal_outcome IN ('trusted_correctly', 'over_warned')",
            name="ck_practice_sessions_normal_outcome",
        ),
        CheckConstraint("origin IN ('live', 'demo_seed')", name="ck_practice_sessions_origin"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    child_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("children.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    mode: Mapped[str] = mapped_column(String(16), nullable=False)
    area: Mapped[str] = mapped_column(String(32), nullable=False)
    subtype: Mapped[str | None] = mapped_column(String(32), nullable=True)
    scenario_id: Mapped[str] = mapped_column(String(64), nullable=False)
    is_normal: Mapped[bool] = mapped_column(Boolean, nullable=False)
    target_cue_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    variant: Mapped[dict] = mapped_column(JSON, nullable=False)
    scenario_title: Mapped[str] = mapped_column(String(80), nullable=False)
    child_setup: Mapped[str] = mapped_column(String(300), nullable=False)
    ai_role_name: Mapped[str] = mapped_column(String(40), nullable=False)
    retry_of: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("practice_sessions.id", ondelete="SET NULL"),
        nullable=True,
    )
    draw_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # 1차 힌트 없음(#104 ④) — HINT_MAX는 PRD OQ 14 미정이라 값을 채우지 않는다(null)
    hint_level: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    normal_outcome: Mapped[str | None] = mapped_column(String(32), nullable=True)
    origin: Mapped[str] = mapped_column(String(16), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PracticeTurn(Base):
    """연습 턴 (Architecture 엔티티 practice_turns — 첫 대사 turn_index 0, DECISIONS #80·#98)."""

    __tablename__ = "practice_turns"
    __table_args__ = (
        UniqueConstraint("session_id", "turn_index", name="uq_practice_turns_session_turn"),
        CheckConstraint(
            "ai_status IN ('ok', 'blocked', 'safe_reply')",
            name="ck_practice_turns_ai_status",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("practice_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    turn_index: Mapped[int] = mapped_column(Integer, nullable=False)
    ai_line: Mapped[str] = mapped_column(Text, nullable=False)
    choices: Mapped[list[dict]] = mapped_column(JSON, nullable=False)
    chosen_choice_id: Mapped[str | None] = mapped_column(String(8), nullable=True)
    substituted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    target_clue_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    revealed_clue_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    ai_status: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class CueResult(Base):
    """드러난 단서의 판정 결과 — found·missed만 저장, not_shown은 저장하지 않음 (DECISIONS #109)."""

    __tablename__ = "cue_results"
    __table_args__ = (
        CheckConstraint("outcome IN ('found', 'missed')", name="ck_cue_results_outcome"),
        # 같은 세션의 같은 단서는 한 번만 — 동시 종료 요청의 중복 저장 방지 (T-15 리뷰 치명 #1)
        UniqueConstraint("session_id", "cue_id", name="uq_cue_results_session_cue"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("practice_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    child_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("children.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cue_id: Mapped[str] = mapped_column(String(64), nullable=False)
    outcome: Mapped[str] = mapped_column(String(16), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class GuardianNotice(Base):
    """보호자 최소 알림 (Architecture 엔티티 guardian_notices — DECISIONS #23·#92·#95, T-25).

    본문·원문·이미지·감정 열이 없다(F-41 ③). 항목은 발생 시각·위험도·영역만(F-41 ④) — 열 추가 금지(F-41 ⑤).
    """

    __tablename__ = "guardian_notices"
    __table_args__ = (
        CheckConstraint("kind IN ('safety', 'trusted_contact')", name="ck_guardian_notices_kind"),
        CheckConstraint("level IS NULL OR level IN ('red', 'yellow')", name="ck_guardian_notices_level"),
        CheckConstraint(
            "area IS NULL OR area IN ('scam', 'identity_lending', 'friend_pressure')",
            name="ck_guardian_notices_area",
        ),
        CheckConstraint("channel IS NULL OR channel IN ('call', 'sms')", name="ck_guardian_notices_channel"),
        CheckConstraint("origin IN ('demo_seed', 'live')", name="ck_guardian_notices_origin"),
        CheckConstraint(
            "(kind = 'safety' AND level IS NOT NULL AND area IS NOT NULL AND channel IS NULL)"
            " OR (kind = 'trusted_contact' AND level IS NULL AND area IS NULL AND channel IS NOT NULL)",
            name="ck_guardian_notices_kind_fields",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    child_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("children.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    level: Mapped[str | None] = mapped_column(String(8), nullable=True)
    area: Mapped[str | None] = mapped_column(String(32), nullable=True)
    channel: Mapped[str | None] = mapped_column(String(8), nullable=True)
    origin: Mapped[str] = mapped_column(String(16), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
