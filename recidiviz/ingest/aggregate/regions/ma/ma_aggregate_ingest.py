# Recidiviz - a data platform for criminal justice reform
# Copyright (C) 2019 Recidiviz, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# =============================================================================
"""Download and parse (turn the data into wide format consistent with other
state aggregate datasets) pdfs from the Massachusetts Department of Correction
Weekly collections.

Author: Albert Sun"""

from datetime import datetime
from typing import Dict

import numpy as np
import pandas as pd
import tabula
import us
from sqlalchemy.ext.declarative import DeclarativeMeta

from recidiviz.common import fips
from recidiviz.common.constants.aggregate import enum_canonical_strings as enum_strings
from recidiviz.persistence.database.schema.aggregate.schema import MaFacilityAggregate


def parse(filename: str) -> Dict[DeclarativeMeta, pd.DataFrame]:
    table = _parse_table(filename)
    report_date = _parse_date(filename)

    county_names = table.county

    table = fips.add_column_to_df(table, county_names, us.states.MA)  # type: ignore

    table["report_date"] = report_date
    table["aggregation_window"] = enum_strings.daily_granularity
    table["report_frequency"] = enum_strings.weekly_granularity

    return {MaFacilityAggregate: table}


def _parse_date(filename: str):
    """Parse dates from the filename of filenames, i.e. """
    all_num = "".join(x for x in filename if x.isdigit())  # return all digits
    last_eight = all_num[-8:]  # look at last 8 digits, which are used for dates
    date = datetime.strptime(last_eight, "%m%d%Y")
    return date


def _parse_table(filename: str) -> pd.DataFrame:
    """
    Parse a Massachusetts DOC weekly report pdf to be consistent with other
    aggregate data integration efforts.

    :return: parsed Massachusetts df
    """

    def label_subset_of_counties(column):
        for i, v in enumerate(column):
            if i == len(column) - 1:
                break
            if pd.isna(v):
                continue
            if v.endswith("TYPE") and not pd.isna(column[i + 1]):
                column[i] = column[i][:-5] + " " + column[i + 1] + " TYPE"

    def create_level_col(df):
        """Create LEVEL column with HOC or Jail"""
        levels = {
            "HOUSE OF STATE": "HOC",
            "CORRECTION FEDERAL": "HOC",
            "SENTENCED": "HOC",
            "SENTENCED STATE": "HOC",
            "JAIL IN": "JAIL",
            "JAIL INS": "JAIL",
            "JAIL OTHER COUNTY": "JAIL",
            "UNSENTENCED": "JAIL",
            "UNSENTENCED INS": "JAIL",
        }

        df["LEVEL"] = df["COUNTY_SECURITY_LEVEL"].map(levels)

        # shift level column up one row because level appears
        df["LEVEL"] = df["LEVEL"].shift(-1)

        # interpolate LEVEL to fill the entire LEVEL column
        df.LEVEL = df["LEVEL"].ffill()

        return df

    [df] = tabula.read_pdf(
        filename, pages=[3, 4, 5, 6], stream=True, multiple_tables=False
    )
    df = df[["COUNTY SECURITY LEVEL", "Unnamed: 6", "TOTAL", "Unnamed: 8"]]
    df = df.rename(
        columns={
            "COUNTY SECURITY LEVEL": "COUNTY_SECURITY_LEVEL",
            "Unnamed: 6": "MALE",
            "TOTAL": "FEMALE",
            "Unnamed: 8": "TOTAL",
        }
    )

    # fix subset labelling (i.e. specifying Norfolk to be Norfolk Braintree
    # and NORFOLK Dedham / RT 128)
    label_subset_of_counties(df.COUNTY_SECURITY_LEVEL)

    # label counties (hacky solution for Worcester, which is the last COUNTY
    # in the DF. It's the only COUNTY that is parsed without ' TYPE' at the
    # end of it:)
    df["COUNTY"] = np.where(
        df["COUNTY_SECURITY_LEVEL"].str.contains("TYPE|WORCESTER", regex=True),
        df["COUNTY_SECURITY_LEVEL"],
        np.nan,
    )

    df.COUNTY = df.COUNTY.interpolate(method="pad", limit_direction="forward")

    df = create_level_col(df)

    # remove NA rows and non-numeric rows:
    df = df.dropna(subset=["COUNTY_SECURITY_LEVEL", "MALE"])
    df = df[df.MALE.str.isnumeric()]

    # fix names
    df = df.replace(
        {
            "HOUSE OF STATE": "STATE",
            "CORRECTION FEDERAL": "FEDERAL",
            "JAIL OTHER COUNTY": "JAIL_OTHER",
            "SENTENCED STATE": "STATE",
            "UNSENTENCED INS": "JAIL_OTHER",
            "FACILITY TOTAL": "TOTAL",
        }
    )

    df.COUNTY = df.COUNTY.replace("TYPE", "", regex=True)
    df.COUNTY = df.COUNTY.str.upper()
    # remove unecessary space at the end of county:
    df.COUNTY = df.COUNTY.str.replace(r"\b $", "", regex=True).str.strip()

    # select county security levels that we care about. This excludes 52A's,
    # Non 52A's, etc.
    df = df[
        (
            df.COUNTY_SECURITY_LEVEL.isin(
                ["COUNTY", "STATE", "FEDERAL", "TOTAL", "JAIL_OTHER"]
            )
        )
    ]

    df = df.set_index(["COUNTY", "LEVEL", "COUNTY_SECURITY_LEVEL"])

    # fix conversion error for fields ending with ' .'
    df = df.applymap(lambda value: value.rstrip(". "))

    # turn counts to type int

    df = df.astype("float").astype("int32")

    pivoted = df.pivot_table(
        index=["COUNTY"], columns=["COUNTY_SECURITY_LEVEL", "LEVEL"], aggfunc=np.sum
    )

    # flatten index and lowercase column names
    pivoted.columns = [
        "_".join(reversed(a)).lower() for a in pivoted.columns.to_flat_index()
    ]

    pivoted = pivoted.reset_index()
    pivoted["facility_name"] = pivoted["COUNTY"]  # distinguish county and facility
    pivoted["COUNTY"] = pivoted.COUNTY.str.split().str.get(0)  # create county column
    pivoted.columns = map(str.lower, pivoted.columns)  # lowercase col names

    return pivoted