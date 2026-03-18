"""add_soc2_audit_fields

Revision ID: ea394e8a966d
Revises: 68239facb43f
Create Date: 2026-03-18 12:57:27.054219

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ea394e8a966d'
down_revision: Union[str, Sequence[str], None] = '68239facb43f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add SOC 2 compliance fields to audit_logs and new enum values."""
    # 1. Add 4 nullable columns to audit_logs for SOC 2 compliance
    op.add_column(
        'audit_logs',
        sa.Column(
            'content_hash', sa.String(64), nullable=True,
            comment='SHA-256 tamper-detection hash',
        ),
    )
    op.add_column(
        'audit_logs',
        sa.Column(
            'compliance_framework', sa.String(32), nullable=True,
            comment='SOC2, HIPAA, GDPR, PCI_DSS',
        ),
    )
    op.add_column(
        'audit_logs',
        sa.Column(
            'evidence_type', sa.String(64), nullable=True,
            comment='TSC category e.g. CC6, CC7, CC8, CC9',
        ),
    )
    op.add_column(
        'audit_logs',
        sa.Column(
            'retention_until', sa.DateTime(timezone=True), nullable=True,
            comment='Retention expiry per compliance policy',
        ),
    )

    # 2. Add 5 new values to the eventtype PostgreSQL enum
    op.execute("ALTER TYPE eventtype ADD VALUE IF NOT EXISTS 'SECURITY_SCAN_STARTED'")
    op.execute("ALTER TYPE eventtype ADD VALUE IF NOT EXISTS 'SECURITY_SCAN_COMPLETED'")
    op.execute("ALTER TYPE eventtype ADD VALUE IF NOT EXISTS 'SECURITY_GATE_PASSED'")
    op.execute("ALTER TYPE eventtype ADD VALUE IF NOT EXISTS 'SECURITY_GATE_FAILED'")
    op.execute("ALTER TYPE eventtype ADD VALUE IF NOT EXISTS 'COMPLIANCE_CHECK_COMPLETED'")

    # 3. Add COMPLIANCE_VIOLATION to the findingtype PostgreSQL enum
    op.execute("ALTER TYPE findingtype ADD VALUE IF NOT EXISTS 'COMPLIANCE_VIOLATION'")

    # 4. Create PostgreSQL rules to enforce audit log immutability
    op.execute(
        "CREATE RULE prevent_audit_log_update AS ON UPDATE TO audit_logs DO INSTEAD NOTHING"
    )
    op.execute(
        "CREATE RULE prevent_audit_log_delete AS ON DELETE TO audit_logs DO INSTEAD NOTHING"
    )


def downgrade() -> None:
    """Remove SOC 2 compliance fields and immutability rules."""
    # Drop immutability rules
    op.execute("DROP RULE IF EXISTS prevent_audit_log_delete ON audit_logs")
    op.execute("DROP RULE IF EXISTS prevent_audit_log_update ON audit_logs")

    # Note: PostgreSQL does not support removing enum values.
    # The eventtype and findingtype enum additions are not reversible.

    # Drop columns
    op.drop_column('audit_logs', 'retention_until')
    op.drop_column('audit_logs', 'evidence_type')
    op.drop_column('audit_logs', 'compliance_framework')
    op.drop_column('audit_logs', 'content_hash')
