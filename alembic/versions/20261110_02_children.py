from alembic import op
import sqlalchemy as sa

revision = "20261110_02"
down_revision = "20261110_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "children",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("guardian_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("nickname", sa.String(length=20), nullable=False),
        sa.Column("grade", sa.String(length=2), nullable=False),
        sa.Column("link_code", sa.String(length=6), nullable=False),
        sa.Column("pin_hash", sa.Text(), nullable=False),
        sa.Column(
            "consent_agreed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("consent_version", sa.String(length=20), nullable=False),
        sa.Column(
            "onboarding_completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column("start_difficulty", sa.SmallInteger(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "grade IN ('E6', 'M1', 'M2', 'M3', 'H1', 'H2', 'H3')",
            name="ck_children_grade",
        ),
        sa.ForeignKeyConstraint(
            ["guardian_id"],
            ["guardians.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("link_code", name="uq_children_link_code"),
    )
    op.create_index(
        "ix_children_guardian_id",
        "children",
        ["guardian_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_children_guardian_id", table_name="children")
    op.drop_table("children")