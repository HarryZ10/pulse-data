# pylint: skip-file
"""adjust_pa_contacts_raw_text

Revision ID: a50802bba2df
Revises: 527877e24009
Create Date: 2021-09-03 15:34:13.842823

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a50802bba2df"
down_revision = "527877e24009"
branch_labels = None
depends_on = None

TABLES_TO_UPDATE = ["state_supervision_contact", "state_supervision_contact_history"]

UPDATE_QUERY = """
    UPDATE {table}
    SET contact_type_raw_text = SPLIT_PART(contact_type_raw_text, '-', 1),
    contact_method_raw_text = SPLIT_PART(location_raw_text, '-', 2)
    WHERE state_code = 'US_PA'
"""

DOWNGRADE_QUERY = """
    UPDATE {table}
    SET contact_type_raw_text = CONCAT(contact_type_raw_text, '-', SPLIT_PART(location_raw_text, '-', 2)),
    contact_method_raw_text = NULL
    WHERE state_code = 'US_PA'
"""


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    for table in TABLES_TO_UPDATE:
        op.execute(UPDATE_QUERY.format(table=table))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    for table in TABLES_TO_UPDATE:
        op.execute(DOWNGRADE_QUERY.format(table=table))
    # ### end Alembic commands ###