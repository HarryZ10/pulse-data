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
// =============================================================================
import * as React from "react";
import { CaseUpdateActionType } from "../../stores/CaseUpdatesStore";
import { Client } from "../../stores/ClientsStore";
import BaseFeedbackForm from "./BaseForm";
import { useRootStore } from "../../stores";

interface IncorrectDataFormProps {
  client: Client;
  actionType: CaseUpdateActionType;

  title: string;
  onCancel: (event?: React.MouseEvent<Element, MouseEvent>) => void;
}

const IncorrectDataForm = ({
  client,
  actionType,
  title,
  onCancel,
}: IncorrectDataFormProps): JSX.Element => {
  const { caseUpdatesStore, policyStore } = useRootStore();
  const omsName = policyStore.policies?.omsName || "OMS";

  return (
    <BaseFeedbackForm
      caseUpdatesStore={caseUpdatesStore}
      client={client}
      actionType={actionType}
      commentPlaceholder={`This person's status does not match ${omsName} because...`}
      description="Tell us more (optional)."
      title={title}
      onCancel={onCancel}
    />
  );
};

export default IncorrectDataForm;
