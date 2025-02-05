// Recidiviz - a data platform for criminal justice reform
// Copyright (C) 2021 Recidiviz, Inc.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

import { palette } from "@recidiviz/design-system";
import assertNever from "assert-never";
import { makeAutoObservable } from "mobx";
import moment from "moment";
import { PillKind } from "../../components/Pill";
import { inflectDay, LONG_DATE_FORMAT } from "../../utils";

// =============================================================================
export enum OpportunityDeferralType {
  REMINDER = "REMINDER",
  ACTION_TAKEN = "ACTION_TAKEN",
  INCORRECT_DATA = "INCORRECT_DATA",
}

export enum OpportunityType {
  OVERDUE_DOWNGRADE = "OVERDUE_DOWNGRADE",
  EMPLOYMENT = "EMPLOYMENT",
  ASSESSMENT = "ASSESSMENT",
  CONTACT = "CONTACT",
  HOME_VISIT = "HOME_VISIT",
  NEW_TO_CASELOAD = "NEW_TO_CASELOAD",
}

const OPPORTUNITY_TITLES: Record<OpportunityType, string> = {
  [OpportunityType.OVERDUE_DOWNGRADE]: "Supervision level mismatch",
  [OpportunityType.EMPLOYMENT]: "Unemployed",
  [OpportunityType.ASSESSMENT]: "Risk assessment",
  [OpportunityType.CONTACT]: "Contact",
  [OpportunityType.HOME_VISIT]: "Home visit",
  [OpportunityType.NEW_TO_CASELOAD]: "New to caseload",
};

export const opportunityPriorityComparator = (
  self: Opportunity,
  other: Opportunity
): number => {
  const first = self.priority;
  const second = other.priority;
  if (first < second) return -1;
  if (first > second) return 1;

  // If the sorting priority is the same, sort by external id so the sort is stable.
  if (self.personExternalId < other.personExternalId) {
    return -1;
  }
  if (self.personExternalId > other.personExternalId) {
    return 1;
  }

  return 0;
};

/**
 * Formats distance from now in terms of days, e.g., "in 5 days", "14 days ago".
 * Will return "today" rather than "in 0 days".
 */
const differenceInDays = (date: moment.Moment): string => {
  // `date` is generally expected to be a day boundary.
  const beginningOfDay = moment().startOf("day");

  if (date.isSame(beginningOfDay, "day")) {
    return "today";
  }

  const dayDiff = date.diff(beginningOfDay, "days");

  const unitInflected = inflectDay(dayDiff);

  if (dayDiff < 0) {
    return `${Math.abs(dayDiff)} ${unitInflected} ago`;
  }
  return `in ${dayDiff} ${unitInflected}`;
};

export type OpportunityData = {
  personExternalId: string;
  stateCode: string;
  supervisingOfficerExternalId: string;
  opportunityType: OpportunityType;
  opportunityMetadata: { [index: string]: unknown };
  deferredUntil?: string;
  deferralType?: OpportunityDeferralType;
  deferralId?: string;
};

export class Opportunity {
  personExternalId: string;

  stateCode: string;

  supervisingOfficerExternalId: string;

  opportunityType: OpportunityType;

  opportunityMetadata: { [index: string]: unknown };

  deferredUntil?: string;

  deferralType?: OpportunityDeferralType;

  deferralId?: string;

  constructor(apiData: OpportunityData) {
    this.personExternalId = apiData.personExternalId;
    this.stateCode = apiData.stateCode;
    this.supervisingOfficerExternalId = apiData.supervisingOfficerExternalId;
    this.opportunityType = apiData.opportunityType;
    this.opportunityMetadata = apiData.opportunityMetadata;
    this.deferredUntil = apiData.deferredUntil;
    this.deferralType = apiData.deferralType;
    this.deferralId = apiData.deferralId;

    makeAutoObservable(this);
  }

  get isDeferred(): boolean {
    return this.deferredUntil !== undefined;
  }

  get previewText(): string {
    switch (this.opportunityType) {
      case OpportunityType.OVERDUE_DOWNGRADE:
      case OpportunityType.EMPLOYMENT:
        return OPPORTUNITY_TITLES[this.opportunityType];
      case OpportunityType.NEW_TO_CASELOAD:
        return "New";
      case OpportunityType.ASSESSMENT:
      case OpportunityType.CONTACT:
      case OpportunityType.HOME_VISIT:
        return `${OPPORTUNITY_TITLES[this.opportunityType]} ${
          this.dueDaysFormatted
        }`;
      default:
        assertNever(this.opportunityType);
    }
  }

  get priority(): number {
    switch (this.opportunityType) {
      case OpportunityType.OVERDUE_DOWNGRADE:
        return 1;
      case OpportunityType.NEW_TO_CASELOAD:
        return 2;
      case OpportunityType.EMPLOYMENT:
        return 3;
      case OpportunityType.ASSESSMENT:
        return this.opportunityMetadata.status === "OVERDUE" ? 4 : 5;
      case OpportunityType.HOME_VISIT:
        return this.opportunityMetadata.status === "OVERDUE" ? 6 : 7;
      case OpportunityType.CONTACT:
        return this.opportunityMetadata.status === "OVERDUE" ? 8 : 9;
      default:
        assertNever(this.opportunityType);
    }
  }

  get dueDate(): moment.Moment | null {
    const { daysUntilDue } = this.opportunityMetadata;
    if (typeof daysUntilDue === "number") {
      return moment().startOf("day").add(daysUntilDue, "days");
    }
    return null;
  }

  get dueDaysFormatted(): string {
    const { dueDate } = this;
    if (dueDate) {
      return differenceInDays(dueDate);
    }
    return "";
  }

  /**
   * Assessments are "due" but contacts and home visits are "recommended"
   */
  get dueDateModifier(): string {
    switch (this.opportunityType) {
      case OpportunityType.CONTACT:
      case OpportunityType.HOME_VISIT:
        return "recommended";
      case OpportunityType.ASSESSMENT:
        return "due";
      default:
        return "";
    }
  }

  /**
   * New to Caseload opportunities report how long ago they started
   */
  get daysAgo(): string | null {
    const { daysOnCaseload } = this.opportunityMetadata;

    if (typeof daysOnCaseload === "number") {
      if (daysOnCaseload === 0) return "today";

      return `${daysOnCaseload} ${inflectDay(daysOnCaseload)} ago`;
    }

    return null;
  }

  get title(): string {
    const titleBase = OPPORTUNITY_TITLES[this.opportunityType];

    switch (this.opportunityType) {
      case OpportunityType.OVERDUE_DOWNGRADE:
      case OpportunityType.EMPLOYMENT:
        return titleBase;
      case OpportunityType.NEW_TO_CASELOAD:
        return `${titleBase}${this.daysAgo ? `: ${this.daysAgo}` : ""}`;
      case OpportunityType.CONTACT:
      case OpportunityType.ASSESSMENT:
      case OpportunityType.HOME_VISIT:
        return `${titleBase} ${this.dueDateModifier} ${this.dueDaysFormatted}`;
      default:
        assertNever(this.opportunityType);
    }
  }

  get tooltipText(): string | undefined {
    const titleBase = OPPORTUNITY_TITLES[this.opportunityType];

    switch (this.opportunityType) {
      case OpportunityType.OVERDUE_DOWNGRADE:
      case OpportunityType.EMPLOYMENT:
      case OpportunityType.NEW_TO_CASELOAD:
        return undefined;
      case OpportunityType.CONTACT:
      case OpportunityType.ASSESSMENT:
      case OpportunityType.HOME_VISIT:
        return `${titleBase} ${this.dueDateModifier} ${this.dueDate?.format(
          LONG_DATE_FORMAT
        )}`;
      default:
        assertNever(this.opportunityType);
    }
  }

  get alertOptions(): {
    icon: {
      kind: string;
      color: string;
    };
    pill: {
      kind: PillKind;
    };
  } {
    let iconKind = "Alert";
    let iconColor;
    let pillKind: PillKind;

    switch (this.opportunityType) {
      case OpportunityType.OVERDUE_DOWNGRADE:
      case OpportunityType.NEW_TO_CASELOAD:
        iconKind = "StarCircled";
        iconColor = palette.signal.highlight;
        pillKind = "highlight";
        break;
      case OpportunityType.EMPLOYMENT:
        iconColor = palette.data.gold1;
        pillKind = "warn";
        break;
      case OpportunityType.ASSESSMENT:
      case OpportunityType.CONTACT:
      case OpportunityType.HOME_VISIT:
        if (this.opportunityMetadata.status === "OVERDUE") {
          iconColor = palette.signal.error;
          pillKind = "error";
        } else {
          iconColor = palette.data.gold1;
          pillKind = "warn";
        }
        break;
      default:
        assertNever(this.opportunityType);
    }

    return {
      icon: { kind: iconKind, color: iconColor },
      pill: { kind: pillKind },
    };
  }
}
