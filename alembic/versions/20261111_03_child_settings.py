from alembic import op
import sqlalchemy as sa


revision = "20261111_03"
down_revision = "20261110_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "child_settings",
        sa.Column("child_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column(
            "font_scale",
            sa.String(length=16),
            server_default="normal",
            nullable=False,
        ),
        sa.Column(
            "high_contrast",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
        sa.Column(
            "tts_enabled",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
        sa.Column("trusted_contact_name", sa.String(length=20), nullable=True),
        sa.Column("trusted_contact_phone", sa.String(length=20), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "font_scale IN ('normal', 'large', 'xlarge')",
            name="ck_child_settings_font_scale",
        ),
        sa.ForeignKeyConstraint(
            ["child_id"],
            ["children.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("child_id"),
    )


def downgrade() -> None:
    op.drop_table("child_settings")
