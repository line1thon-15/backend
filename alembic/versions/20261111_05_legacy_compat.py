"""Compatibility marker for databases at the pre-squash child-settings revision.

The current 20261111_03 migration creates the final child_settings schema. Existing
Neon databases may already record 20261111_05 from the former split migration chain.
"""

revision = "20261111_05"
down_revision = "20261111_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass