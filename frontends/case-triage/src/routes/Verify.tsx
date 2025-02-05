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
import { navigate, RouteComponentProps } from "@reach/router";
import React, { ReactElement } from "react";
import styled from "styled-components/macro";
import { rem } from "polished";
import { Button, ErrorPage, Link, spacing } from "@recidiviz/design-system";

const HomeButton = styled(Button)`
  margin: ${rem(spacing.xl)} 0;
`;

const Verify = (props: RouteComponentProps): ReactElement => {
  return (
    <ErrorPage headerText="Please verify your email.">
      <p>
        If you have just signed up for an account, please check your inbox for
        an email asking you to verify your email address. After you click the
        verification button or link in that email, you can reach the home page
        below.
      </p>
      <p>
        If you have reached this page by mistake, please try to log in again. If
        you are still having trouble, please reach out to{" "}
        <Link href="mailto:feedback@recidiviz.org?subject=Trouble logging into Case Triage">
          Recidiviz Support
        </Link>
        .
      </p>
      <HomeButton kind="secondary" onClick={() => navigate("/")}>
        Back to Home
      </HomeButton>
    </ErrorPage>
  );
};

export default Verify;
