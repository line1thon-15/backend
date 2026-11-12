"""T-25 보호자 최소 알림 테이블: guardian_notices.

Architecture 엔티티 guardian_notices 행(열·CHECK — DECISIONS #23·#92·#95). 2026-11-12 사용자 답 "T-25에 포함 (추천)".
본문·원문·이미지·감정 열 없음(F-41 ③⑤). `origin`의 2차 값(`real_check`)은 선추가하지 않는다.
"""

from alembic import op
import sqlalchemy as sa


revision = "20261112_05"
down_revision = "20261112_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "guardian_notices",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("child_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("level", sa.String(length=8), nullable=True),
        sa.Column("area", sa.String(length=32), nullable=True),
        sa.Column("channel", sa.String(length=8), nullable=True),
        sa.Column("origin", sa.String(length=16), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("kind IN ('safety', 'trusted_contact')", name="ck_guardian_notices_kind"),
        sa.CheckConstraint("level IS NULL OR level IN ('red', 'yellow')", name="ck_guardian_notices_level"),
        sa.CheckConstraint(
            "area IS NULL OR area IN ('scam', 'identity_lending', 'friend_pressure')",
            name="ck_guardian_notices_area",
        ),
        sa.CheckConstraint("channel IS NULL OR channel IN ('call', 'sms')", name="ck_guardian_notices_channel"),
        sa.CheckConstraint("origin IN ('demo_seed', 'live')", name="ck_guardian_notices_origin"),
        sa.CheckConstraint(
            "(kind = 'safety' AND level IS NOT NULL AND area IS NOT NULL AND channel IS NULL)"
            " OR (kind = 'trusted_contact' AND level IS NULL AND area IS NULL AND channel IS NOT NULL)",
            name="ck_guardian_notices_kind_fields",
        ),
        sa.ForeignKeyConstraint(["child_id"], ["children.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_guardian_notices_child_id",
        "guardian_notices",
        ["child_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_guardian_notices_child_id", table_name="guardian_notices")
    op.drop_table("guardian_notices")
