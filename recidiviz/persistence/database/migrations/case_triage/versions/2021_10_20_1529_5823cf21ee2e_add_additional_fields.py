# pylint: skip-file
"""add_additional_fields

Revision ID: 5823cf21ee2e
Revises: 271f00b3ca42
Create Date: 2021-10-20 15:29:59.707190

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "5823cf21ee2e"
down_revision = "271f00b3ca42"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "etl_clients",
        sa.Column("next_recommended_home_visit_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "etl_clients",
        sa.Column(
            "most_recent_treatment_collateral_contact_date", sa.Date(), nullable=True
        ),
    )
    op.add_column(
        "etl_clients",
        sa.Column(
            "next_recommended_treatment_collateral_contact_date",
            sa.Date(),
            nullable=True,
        ),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("etl_clients", "next_recommended_treatment_collateral_contact_date")
    op.drop_column("etl_clients", "most_recent_treatment_collateral_contact_date")
    op.drop_column("etl_clients", "next_recommended_home_visit_date")
    # ### end Alembic commands ###