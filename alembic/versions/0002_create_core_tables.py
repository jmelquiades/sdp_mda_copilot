"""Create core copilot tables."""

import os

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0002_create_core_tables"
down_revision = "0001_create_schema"
branch_labels = None
depends_on = None

SCHEMA = os.getenv("DB_SCHEMA", "copilot")


def upgrade() -> None:
    op.execute(sa.text(f'CREATE SCHEMA IF NOT EXISTS "{SCHEMA}"'))

    op.create_table(
        "technician_mapping",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_upn", sa.String(), nullable=False, unique=True),
        sa.Column("technician_id_sdp", sa.String(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            onupdate=sa.text("now()"),
        ),
        schema=SCHEMA,
    )

    op.create_table(
        "services_catalog",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("service_code", sa.String(), nullable=False, unique=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("short_description", sa.Text()),
        sa.Column("requirements", sa.Text()),
        sa.Column("first_response_notes", sa.Text()),
        sa.Column("update_notes", sa.Text()),
        sa.Column("closure_notes", sa.Text()),
        sa.Column("comm_sla_p1_hours", sa.Numeric()),
        sa.Column("comm_sla_p2_hours", sa.Numeric()),
        sa.Column("comm_sla_p3_hours", sa.Numeric()),
        sa.Column("comm_sla_p4_hours", sa.Numeric()),
        sa.Column("sdp_mapping_info", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            onupdate=sa.text("now()"),
        ),
        schema=SCHEMA,
    )

    op.create_table(
        "org_profile",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("industry", sa.String()),
        sa.Column("context", sa.Text()),
        sa.Column("critical_services", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("tone_notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            onupdate=sa.text("now()"),
        ),
        schema=SCHEMA,
    )

    op.create_table(
        "persona_config",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("role_description", sa.Text()),
        sa.Column("tone_attributes", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("rules", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("max_reply_length", sa.Integer()),
        sa.Column("system_prompt_template", sa.Text()),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            onupdate=sa.text("now()"),
        ),
        schema=SCHEMA,
    )

    op.create_table(
        "settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(), nullable=False, unique=True),
        sa.Column("value", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            onupdate=sa.text("now()"),
        ),
        schema=SCHEMA,
    )

    op.create_table(
        "ticket_flags",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticket_id", sa.String(), nullable=False, unique=True),
        sa.Column("display_id", sa.String()),
        sa.Column("service_code", sa.String()),
        sa.Column("priority", sa.String()),
        sa.Column("status", sa.String()),
        sa.Column("last_user_contact_at", sa.DateTime(timezone=True)),
        sa.Column("hours_since_last_user_contact", sa.Numeric()),
        sa.Column("communication_sla_hours", sa.Numeric()),
        sa.Column("is_silent", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("experience_review_requested", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("last_review_request_at", sa.DateTime(timezone=True)),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            onupdate=sa.text("now()"),
        ),
        schema=SCHEMA,
    )
    op.create_table(
        "ia_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("user_upn", sa.String(), index=True),
        sa.Column("ticket_id", sa.String(), index=True),
        sa.Column("operation", sa.String()),
        sa.Column("message_type", sa.String()),
        sa.Column("model", sa.String()),
        sa.Column("success", sa.Boolean()),
        sa.Column("latency_ms", sa.Integer()),
        sa.Column("prompt_chars", sa.Integer()),
        sa.Column("response_chars", sa.Integer()),
        sa.Column("error_message", sa.Text()),
        schema=SCHEMA,
    )
    op.create_index("ix_ia_logs_ticket_id", "ia_logs", ["ticket_id"], schema=SCHEMA)
    op.create_index("ix_ia_logs_user_upn", "ia_logs", ["user_upn"], schema=SCHEMA)


def downgrade() -> None:
    op.drop_index("ix_ia_logs_user_upn", table_name="ia_logs", schema=SCHEMA)
    op.drop_index("ix_ia_logs_ticket_id", table_name="ia_logs", schema=SCHEMA)
    op.drop_table("ia_logs", schema=SCHEMA)

    op.drop_table("ticket_flags", schema=SCHEMA)
    op.drop_table("settings", schema=SCHEMA)
    op.drop_table("persona_config", schema=SCHEMA)
    op.drop_table("org_profile", schema=SCHEMA)
    op.drop_table("services_catalog", schema=SCHEMA)
    op.drop_table("technician_mapping", schema=SCHEMA)
