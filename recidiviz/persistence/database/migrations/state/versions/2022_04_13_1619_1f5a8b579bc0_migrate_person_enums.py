# pylint: skip-file
"""migrate_person_enums

Revision ID: 1f5a8b579bc0
Revises: a9d6c8613472
Create Date: 2022-04-13 16:19:10.395649

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "1f5a8b579bc0"
down_revision = "a9d6c8613472"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute("ALTER TYPE gender RENAME TO state_gender;")
    op.execute("ALTER TYPE race RENAME TO state_race;")
    op.execute("ALTER TYPE ethnicity RENAME TO state_ethnicity;")
    op.execute("ALTER TYPE residency_status RENAME TO state_residency_status;")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute("ALTER TYPE state_gender RENAME TO gender;")
    op.execute("ALTER TYPE state_race RENAME TO race;")
    op.execute("ALTER TYPE state_ethnicity RENAME TO ethnicity;")
    op.execute("ALTER TYPE state_residency_status RENAME TO residency_status;")
    # ### end Alembic commands ###
