from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
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