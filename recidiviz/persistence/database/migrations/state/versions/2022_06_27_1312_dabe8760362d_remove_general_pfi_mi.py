# pylint: skip-file
"""remove_general_pfi_mi

Revision ID: dabe8760362d
Revises: bcaae162219f
Create Date: 2022-06-27 13:12:46.341585

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "dabe8760362d"
down_revision = "bcaae162219f"
branch_labels = None
depends_on = None

UPDATE_QUERY = (
    "UPDATE state_incarceration_period SET specialized_purpose_for_incarceration = NULL "
    "WHERE state_code = 'US_MI' AND admission_reason_raw_text NOT IN ('17', '18', '106');"
)

DOWNGRADE_QUERY = (
    "UPDATE state_incarceration_period SET specialized_purpose_for_incarceration = 'GENERAL' "
    "WHERE state_code = 'US_MI' AND admission_reason_raw_text NOT IN ('17', '18', '106');"
)


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute(UPDATE_QUERY)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute(DOWNGRADE_QUERY)
    # ### end Alembic commands ###