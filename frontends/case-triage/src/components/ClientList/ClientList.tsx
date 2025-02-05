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
import { observer } from "mobx-react-lite";
import * as React from "react";
import { useRootStore } from "../../stores";
import { CLIENT_LIST_KIND } from "../../stores/ClientsStore/ClientListBuilder";
import TEST_IDS from "../TestIDs";
import {
  ClientListContainerElement,
  ClientListHeading,
  FirstClientListHeading,
} from "./ClientList.styles";
import ClientListCard from "./ClientListCard";
import { ClientListControls } from "./ClientListControls";
import EmptyStateCard from "./EmptyStateCard";

interface ClientListProps {
  kind: CLIENT_LIST_KIND;
  showEmptyState?: boolean;
}

const ClientList = observer(
  ({ kind, showEmptyState = false }: ClientListProps) => {
    const { clientsStore } = useRootStore();

    React.useEffect(() => {
      // Lets the `<ClientListCard />` know to recalculate its offset when the list updates
      clientsStore.setClientPendingView(
        clientsStore.clientPendingView || clientsStore.activeClient
      );
    });

    const list = clientsStore.lists[kind];

    if (showEmptyState && list.length === 0) {
      return <EmptyStateCard />;
    }

    return (
      <div
        data-testid={
          kind === CLIENT_LIST_KIND.UP_NEXT
            ? TEST_IDS.UP_NEXT_LIST
            : TEST_IDS.PROCESSING_FEEDBACK_LIST
        }
      >
        {list.map((client) => {
          return (
            <ClientListCard client={client} key={client.personExternalId} />
          );
        })}
      </div>
    );
  }
);

const ClientListContainer = observer(() => {
  const { clientsStore, userStore } = useRootStore();
  if (clientsStore.isLoading) {
    return <ClientListContainerElement>Loading...</ClientListContainerElement>;
  }

  return (
    <ClientListContainerElement>
      {userStore.isImpersonating ? (
        <FirstClientListHeading>
          {userStore.getOfficerFullName()}&apos;s Caseload
        </FirstClientListHeading>
      ) : (
        <FirstClientListHeading>Up Next</FirstClientListHeading>
      )}
      <ClientListControls />
      <ClientList kind={CLIENT_LIST_KIND.UP_NEXT} showEmptyState />
      {clientsStore.lists[CLIENT_LIST_KIND.PROCESSING_FEEDBACK].length > 0 ? (
        <ClientListHeading>Processing Feedback</ClientListHeading>
      ) : null}
      <ClientList kind={CLIENT_LIST_KIND.PROCESSING_FEEDBACK} />
    </ClientListContainerElement>
  );
});

export default ClientListContainer;
