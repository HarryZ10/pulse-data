# pylint: skip-file
"""ma_facility_aggregate_migration

Revision ID: c6dfe2c1a618
Revises: c3047a711f7a
Create Date: 2021-07-22 23:20:18.996537

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c6dfe2c1a618"
down_revision = "c3047a711f7a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "ma_facility_aggregate",
        sa.Column("record_id", sa.Integer(), nullable=False),
        sa.Column("fips", sa.String(length=5), nullable=False),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column(
            "aggregation_window",
            sa.dialects.postgresql.ENUM(
                "DAILY",
                "WEEKLY",
                "MONTHLY",
                "QUARTERLY",
                "YEARLY",
                name="time_granularity",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "report_frequency",
            sa.dialects.postgresql.ENUM(
                "DAILY",
                "WEEKLY",
                "MONTHLY",
                "QUARTERLY",
                "YEARLY",
                name="time_granularity",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("facility_name", sa.String(length=255), nullable=False),
        sa.Column("county", sa.String(length=255), nullable=False),
        sa.Column("hoc_county_female", sa.Integer(), nullable=True),
        sa.Column("jail_county_female", sa.Integer(), nullable=True),
        sa.Column("hoc_federal_female", sa.Integer(), nullable=True),
        sa.Column("jail_federal_female", sa.Integer(), nullable=True),
        sa.Column("jail_jail_other_female", sa.Integer(), nullable=True),
        sa.Column("hoc_state_female", sa.Integer(), nullable=True),
        sa.Column("facility_total_female", sa.Integer(), nullable=True),
        sa.Column("hoc_total_female", sa.Integer(), nullable=True),
        sa.Column("jail_total_female", sa.Integer(), nullable=True),
        sa.Column("hoc_county_male", sa.Integer(), nullable=True),
        sa.Column("jail_county_male", sa.Integer(), nullable=True),
        sa.Column("hoc_federal_male", sa.Integer(), nullable=True),
        sa.Column("jail_federal_male", sa.Integer(), nullable=True),
        sa.Column("jail_jail_other_male", sa.Integer(), nullable=True),
        sa.Column("hoc_state_male", sa.Integer(), nullable=True),
        sa.Column("facility_total_male", sa.Integer(), nullable=True),
        sa.Column("hoc_total_male", sa.Integer(), nullable=True),
        sa.Column("jail_total_male", sa.Integer(), nullable=True),
        sa.Column("hoc_county_total", sa.Integer(), nullable=True),
        sa.Column("jail_county_total", sa.Integer(), nullable=True),
        sa.Column("hoc_federal_total", sa.Integer(), nullable=True),
        sa.Column("jail_federal_total", sa.Integer(), nullable=True),
        sa.Column("jail_jail_other_total", sa.Integer(), nullable=True),
        sa.Column("hoc_state_total", sa.Integer(), nullable=True),
        sa.Column("facility_total_total", sa.Integer(), nullable=True),
        sa.Column("hoc_total_total", sa.Integer(), nullable=True),
        sa.Column("jail_total_total", sa.Integer(), nullable=True),
        sa.CheckConstraint(
            "LENGTH(fips) = 5", name="ma_facility_aggregate_fips_length_check"
        ),
        sa.PrimaryKeyConstraint("record_id"),
        sa.UniqueConstraint(
            "fips", "report_date", "aggregation_window", "facility_name"
        ),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("ma_facility_aggregate")
    # ### end Alembic commands ###