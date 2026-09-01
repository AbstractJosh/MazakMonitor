"""olcum tablolari

Revision ID: 75141e398cbd
Revises: 0e4a34448ddb
Create Date: 2026-08-11 10:14:07.744500

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '75141e398cbd'
down_revision: Union[str, Sequence[str], None] = '0e4a34448ddb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Olcum tablolari (CSV tekrar-oynatma simulatorunun hedefi)."""
    op.create_table(
        "measurement",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        sa.Column("source_time", sa.DateTime(), nullable=False),
        sa.Column("unit_no", sa.Integer(), nullable=False),
        sa.Column("channel_nr", sa.Integer(), nullable=False),
        sa.Column("tool_nr", sa.Integer(), nullable=False),
        sa.Column("program_nr", sa.Integer(), nullable=False),
        sa.Column("cut_nr", sa.Integer(), nullable=False),
        sa.Column("workpiece", sa.String(length=64), nullable=True),
        sa.Column("alarm", sa.Integer(), nullable=True),
        sa.Column("alarm_limit", sa.Integer(), nullable=True),
        sa.Column("source_file", sa.String(length=128), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_measurement_recorded_at", "measurement", ["recorded_at"])
    op.create_index("ix_measurement_unit_no", "measurement", ["unit_no"])
    op.create_index("ix_measurement_unit_time", "measurement", ["unit_no", "recorded_at"])

    op.create_table(
        "measurement_feature",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("measurement_id", sa.Integer(), nullable=False),
        sa.Column("slot", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column("work_value", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["measurement_id"], ["measurement.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_measurement_feature_measurement_id", "measurement_feature", ["measurement_id"]
    )

    op.create_table(
        "measurement_limit",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("measurement_id", sa.Integer(), nullable=False),
        sa.Column("limit_nr", sa.Integer(), nullable=False),
        sa.Column("level", sa.Float(), nullable=False),
        sa.Column("lim_type", sa.Integer(), nullable=True),
        sa.Column("feature_nr", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["measurement_id"], ["measurement.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_measurement_limit_measurement_id", "measurement_limit", ["measurement_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_measurement_limit_measurement_id", table_name="measurement_limit")
    op.drop_table("measurement_limit")
    op.drop_index("ix_measurement_feature_measurement_id", table_name="measurement_feature")
    op.drop_table("measurement_feature")
    op.drop_index("ix_measurement_unit_time", table_name="measurement")
    op.drop_index("ix_measurement_unit_no", table_name="measurement")
    op.drop_index("ix_measurement_recorded_at", table_name="measurement")
    op.drop_table("measurement")
