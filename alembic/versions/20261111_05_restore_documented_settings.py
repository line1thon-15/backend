from alembic import op
import sqlalchemy as sa


revision = "20261111_05"
down_revision = "20261111_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("child_settings") as batch_op:
        batch_op.drop_constraint("ck_child_settings_font_scale", type_="check")
        batch_op.create_check_constraint(
            "ck_child_settings_font_scale",
            "font_scale IN (\'normal\', \'large\', \'xlarge\')",
        )
        batch_op.add_column(
            sa.Column(
                "favorite_apps",
                sa.JSON(),
                server_default=sa.text("'[]'"),
                nullable=False,
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("child_settings") as batch_op:
        batch_op.drop_column("favorite_apps")
        batch_op.drop_constraint("ck_child_settings_font_scale", type_="check")
        batch_op.create_check_constraint(
            "ck_child_settings_font_scale",
            "font_scale IN (\'small\', \'normal\', \'large\')",
        )
