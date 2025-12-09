"""Create Copilot schema."""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_create_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE SCHEMA IF NOT EXISTS "Copilot"')


def downgrade() -> None:
    # No automatic downgrade to avoid dropping potential data.
    pass
