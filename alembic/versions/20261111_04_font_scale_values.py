from alembic import op


revision = "20261111_04"
down_revision = "20261111_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("child_settings") as batch_op:
        batch_op.drop_constraint("ck_child_settings_font_scale", type_="check")
        batch_op.create_check_constraint(
            "ck_child_settings_font_scale",
            "font_scale IN (\'small\', \'normal\', \'large\')",
        )


def downgrade() -> None:
    with op.batch_alter_table("child_settings") as batch_op:
        batch_op.drop_constraint("ck_child_settings_font_scale", type_="check")
        batch_op.create_check_constraint(
            "ck_child_settings_font_scale",
            "font_scale IN (\'normal\', \'large\', \'xlarge\')",
        )
