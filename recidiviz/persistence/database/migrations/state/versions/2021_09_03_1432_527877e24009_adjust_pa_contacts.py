# pylint: skip-file
"""adjust_pa_contacts

Revision ID: 527877e24009
Revises: cc9bd09e8e85
Create Date: 2021-09-03 14:32:09.203252

"""
from typing import Dict, List, Tuple

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "527877e24009"
down_revision = "cc9bd09e8e85"
branch_labels = None
depends_on = None


UPDATE_CONTACT_METHOD_QUERY = """
    UPDATE {table} 
    SET contact_method = '{new_type_value}' 
    WHERE state_code = 'US_PA' AND SPLIT_PART(contact_type_raw_text, '-', 2) IN ('{old_values}')
"""

UPDATE_CONTACT_METHOD_MAPPING: Dict[str, List[str]] = {
    "TELEPHONE": ["PHONEVOICEMAIL", "PHONEVOICE"],
    "WRITTEN_MESSAGE": ["EMAIL", "FACSIMILE", "MAIL", "PHONETEXT"],
    "IN_PERSON": ["HOME", "OFFICE", "WORK", "FIELD"],
}


UPDATE_CONTACT_TYPE_QUERY = """
    UPDATE {table} 
    SET contact_type = '{new_type_value}'
    WHERE state_code = 'US_PA' AND SPLIT_PART(contact_type_raw_text, '-', 1) IN ('{old_values}')
"""

UPDATE_CONTACT_TYPE_MAPPING: Dict[str, List[str]] = {
    "COLLATERAL": ["COLLATERAL"],
    "BOTH_COLLATERAL_AND_DIRECT": ["BOTH_COLLATERAL_AND_DIRECT"],
    "DIRECT": ["OFFENDER"],
}

UPDATE_CONTACT_LOCATION_QUERY = """
    UPDATE {table}
    SET location = '{new_type_value}'
    WHERE state_code = 'US_PA' AND SPLIT_PART(location_raw_text, '-', 1) IN ('{old_values}') 
"""

UPDATE_CONTACT_LOCATION_MAPPING: Dict[str, List[str]] = {
    "COURT": ["COURTPROBATIONSTAF"],
    "LAW_ENFORCEMENT_AGENCY": ["LAWENFORCEMENT"],
}

DOWNGRADE_CONTACT_METHOD_QUERY = """
    UPDATE {table}
    SET contact_method = NULL
    WHERE state_code = 'US_PA'
"""

DOWNGRADE_CONTACT_TYPE_COLLATERAL_QUERY = """
    UPDATE {table}
    SET contact_type = 'INTERNAL_UNKNOWN' 
    WHERE state_code = 'US_PA' AND SPLIT_PART(contact_type_raw_text, '-', 1) = 'COLLATERAL'
"""

DOWNGRADE_CONTACT_TYPE_QUERY = """
    UPDATE {table}
    SET contact_type = '{old_type_value}'
    WHERE state_code = 'US_PA' 
    AND SPLIT_PART(contact_type_raw_text, '-', 1) IN ('BOTH', 'OFFENDER')
    AND SPLIT_PART(contact_type_raw_text, '-', 2) IN ('{old_method_values}')
"""

DOWNGRADE_CONTACT_TYPE_MAPPING: Dict[str, List[str]] = {
    "WRITTEN_MESSAGE": ["EMAIL", "FACSIMILE", "MAIL", "PHONETEXT"],
    "TELEPHONE": ["PHONEVOICE", "PHONEVOICEMAIL"],
    "FACE_TO_FACE": ["HOME", "OFFICE", "WORK", "FIELD"],
}

DOWNGRADE_CONTACT_LOCATION_QUERY = """
    UPDATE {table}
    SET location = 'INTERNAL_UNKNOWN'
    WHERE state_code = 'US_PA' AND SPLIT_PART(location_raw_text, '-', 1) IN ('COURTPROBATIONSTAF', 'LAWENFORCEMENT')
"""

TABLES_TO_UPDATE = ["state_supervision_contact", "state_supervision_contact_history"]

UPGRADE_QUERIES_WITH_MAPPINGS: List[Tuple[str, Dict[str, List[str]]]] = [
    (UPDATE_CONTACT_METHOD_QUERY, UPDATE_CONTACT_METHOD_MAPPING),
    (UPDATE_CONTACT_TYPE_QUERY, UPDATE_CONTACT_TYPE_MAPPING),
    (UPDATE_CONTACT_LOCATION_QUERY, UPDATE_CONTACT_LOCATION_MAPPING),
]

DOWNGRADE_QUERIES = [
    DOWNGRADE_CONTACT_METHOD_QUERY,
    DOWNGRADE_CONTACT_TYPE_COLLATERAL_QUERY,
    DOWNGRADE_CONTACT_LOCATION_QUERY,
]


def upgrade() -> None:
    ### commands auto generated by Alembic - please adjust! ###
    connection = op.get_bind()
    for table in TABLES_TO_UPDATE:
        for upgrade_query, upgrade_mapping in UPGRADE_QUERIES_WITH_MAPPINGS:
            for new_type_value, old_values in upgrade_mapping.items():
                connection.execute(
                    upgrade_query.format(
                        table=table,
                        new_type_value=new_type_value,
                        old_values="', '".join(old_values),
                    )
                )
    ### end Alembic commands ###


def downgrade() -> None:
    ### commands auto generated by Alembic - please adjust! ###
    pass
    connection = op.get_bind()
    for table in TABLES_TO_UPDATE:
        for downgrade_query in DOWNGRADE_QUERIES:
            connection.execute(downgrade_query.format(table=table))
        for old_type_value, old_method_values in DOWNGRADE_CONTACT_TYPE_MAPPING.items():
            connection.execute(
                DOWNGRADE_CONTACT_TYPE_QUERY.format(
                    table=table,
                    old_type_value=old_type_value,
                    old_method_values="', '".join(old_method_values),
                )
            )
    ### end Alembic commands ###