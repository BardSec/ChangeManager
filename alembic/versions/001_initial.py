"""Initial schema

Revision ID: 001_initial
Revises: 
Create Date: 2025-02-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create changes table
    op.create_table(
        'changes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('category', sa.Enum('Network', 'Identity', 'Endpoint', 'Application', 'Vendor', 'Other', name='categoryenum'), nullable=False),
        sa.Column('systems_affected', sa.Text(), nullable=False),
        sa.Column('planned_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('planned_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('implementer', sa.String(length=255), nullable=False),
        sa.Column('impact_level', sa.Enum('Low', 'Medium', 'High', name='impactlevelenum'), nullable=False),
        sa.Column('user_impact', sa.Enum('None', 'Some', 'Many', name='userimpactenum'), nullable=False),
        sa.Column('maintenance_window', sa.Boolean(), nullable=False),
        sa.Column('backout_plan', sa.Text(), nullable=True),
        sa.Column('what_changed', sa.Text(), nullable=False),
        sa.Column('ticket_id', sa.String(length=100), nullable=True),
        sa.Column('links', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('Planned', 'In Progress', 'Completed', 'Rolled Back', 'Failed', name='statusenum'), nullable=False),
        sa.Column('outcome_notes', sa.Text(), nullable=True),
        sa.Column('post_change_issues', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for changes table
    op.create_index(op.f('ix_changes_title'), 'changes', ['title'], unique=False)
    op.create_index(op.f('ix_changes_category'), 'changes', ['category'], unique=False)
    op.create_index(op.f('ix_changes_implementer'), 'changes', ['implementer'], unique=False)
    op.create_index(op.f('ix_changes_impact_level'), 'changes', ['impact_level'], unique=False)
    op.create_index(op.f('ix_changes_ticket_id'), 'changes', ['ticket_id'], unique=False)
    op.create_index(op.f('ix_changes_status'), 'changes', ['status'], unique=False)
    op.create_index(op.f('ix_changes_created_by'), 'changes', ['created_by'], unique=False)
    op.create_index(op.f('ix_changes_created_at'), 'changes', ['created_at'], unique=False)
    
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('user_email', sa.String(length=255), nullable=False),
        sa.Column('user_name', sa.String(length=255), nullable=True),
        sa.Column('change_id', sa.Integer(), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for audit_logs table
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_user_email'), 'audit_logs', ['user_email'], unique=False)
    op.create_index(op.f('ix_audit_logs_change_id'), 'audit_logs', ['change_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_timestamp'), 'audit_logs', ['timestamp'], unique=False)


def downgrade() -> None:
    # Drop audit_logs table
    op.drop_index(op.f('ix_audit_logs_timestamp'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_change_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_user_email'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_action'), table_name='audit_logs')
    op.drop_table('audit_logs')
    
    # Drop changes table
    op.drop_index(op.f('ix_changes_created_at'), table_name='changes')
    op.drop_index(op.f('ix_changes_created_by'), table_name='changes')
    op.drop_index(op.f('ix_changes_status'), table_name='changes')
    op.drop_index(op.f('ix_changes_ticket_id'), table_name='changes')
    op.drop_index(op.f('ix_changes_impact_level'), table_name='changes')
    op.drop_index(op.f('ix_changes_implementer'), table_name='changes')
    op.drop_index(op.f('ix_changes_category'), table_name='changes')
    op.drop_index(op.f('ix_changes_title'), table_name='changes')
    op.drop_table('changes')
