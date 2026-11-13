"""T-15 연습 세션 테이블: practice_sessions·practice_turns·cue_results.

Architecture "엔티티" practice_sessions·practice_turns·cue_results (2026-11-11 AI 계약 채택 변경 포함 —
DECISIONS #98·#99·#109·#115).
"""

from alembic import op
import sqlalchemy as sa


revision = "20261112_04"
down_revision = "20261111_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "practice_sessions",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("child_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("mode", sa.String(length=16), nullable=False),
        sa.Column("area", sa.String(length=32), nullable=False),
        sa.Column("subtype", sa.String(length=32), nullable=True),
        sa.Column("scenario_id", sa.String(length=64), nullable=False),
        sa.Column("is_normal", sa.Boolean(), nullable=False),
        sa.Column("target_cue_ids", sa.JSON(), nullable=False),
        sa.Column("variant", sa.JSON(), nullable=False),
        sa.Column("scenario_title", sa.String(length=80), nullable=False),
        sa.Column("child_setup", sa.String(length=300), nullable=False),
        sa.Column("ai_role_name", sa.String(length=40), nullable=False),
        sa.Column("retry_of", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("draw_index", sa.Integer(), nullable=True),
        sa.Column("hint_level", sa.SmallInteger(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("normal_outcome", sa.String(length=32), nullable=True),
        sa.Column("origin", sa.String(length=16), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("mode IN ('area', 'mission', 'retry')", name="ck_practice_sessions_mode"),
        sa.CheckConstraint(
            "area IN ('scam', 'identity_lending', 'friend_pressure')",
            name="ck_practice_sessions_area",
        ),
        sa.CheckConstraint(
            "subtype IS NULL OR subtype IN ('game_item', 'allowance', 'high_paying_job')",
            name="ck_practice_sessions_subtype",
        ),
        sa.CheckConstraint(
            "status IN ('in_progress', 'ended', 'stopped')",
            name="ck_practice_sessions_status",
        ),
        sa.CheckConstraint(
            "normal_outcome IS NULL OR normal_outcome IN ('trusted_correctly', 'over_warned')",
            name="ck_practice_sessions_normal_outcome",
        ),
        sa.CheckConstraint("origin IN ('live', 'demo_seed')", name="ck_practice_sessions_origin"),
        sa.ForeignKeyConstraint(["child_id"], ["children.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["retry_of"], ["practice_sessions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_practice_sessions_child_id",
        "practice_sessions",
        ["child_id"],
        unique=False,
    )

    op.create_table(
        "practice_turns",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("session_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("turn_index", sa.Integer(), nullable=False),
        sa.Column("ai_line", sa.Text(), nullable=False),
        sa.Column("choices", sa.JSON(), nullable=False),
        sa.Column("chosen_choice_id", sa.String(length=8), nullable=True),
        sa.Column("substituted", sa.Boolean(), nullable=False),
        sa.Column("target_clue_id", sa.String(length=64), nullable=True),
        sa.Column("revealed_clue_ids", sa.JSON(), nullable=False),
        sa.Column("ai_status", sa.String(length=16), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "ai_status IN ('ok', 'blocked', 'safe_reply')",
            name="ck_practice_turns_ai_status",
        ),
        sa.ForeignKeyConstraint(["session_id"], ["practice_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", "turn_index", name="uq_practice_turns_session_turn"),
    )

    op.create_table(
        "cue_results",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("session_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("child_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("cue_id", sa.String(length=64), nullable=False),
        sa.Column("outcome", sa.String(length=16), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("outcome IN ('found', 'missed')", name="ck_cue_results_outcome"),
        sa.UniqueConstraint("session_id", "cue_id", name="uq_cue_results_session_cue"),
        sa.ForeignKeyConstraint(["session_id"], ["practice_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["child_id"], ["children.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_cue_results_child_id",
        "cue_results",
        ["child_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_cue_results_child_id", table_name="cue_results")
    op.drop_table("cue_results")
    op.drop_table("practice_turns")
    op.drop_index("ix_practice_sessions_child_id", table_name="practice_sessions")
    op.drop_table("practice_sessions")
