// Recidiviz - a data platform for criminal justice reform
// Copyright (C) 2022 Recidiviz, Inc.
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
import { User } from "@auth0/auth0-spa-js";
import { makeAutoObservable, runInAction, when } from "mobx";

import { AuthStore } from "../components/Auth";
import API from "./API";

type UserAgencies = {
  name: string;
  id: number;
};
class UserStore {
  authStore: AuthStore;

  api: API;

  email: string | undefined;

  auth0UserID: string | undefined;

  userAgencies: UserAgencies[] | undefined;

  hasSeenOnboarding: boolean;

  constructor(authStore: AuthStore, api: API) {
    makeAutoObservable(this);

    this.authStore = authStore;
    this.api = api;
    this.email = undefined;
    this.auth0UserID = undefined;
    this.userAgencies = undefined;
    this.hasSeenOnboarding = true;

    when(
      () => api.isSessionInitialized,
      () => this.updateAndRetrieveUserInfo()
    );
  }

  async updateAndRetrieveUserInfo() {
    try {
      if (!this.authStore.user) {
        Promise.reject(new Error("No user information exists."));
      }

      const { email, sub: auth0ID } = this.authStore.user as User;

      const response = (await this.api.request({
        path: "/api/users",
        method: "POST",
        body: {
          email_address: email,
          auth0_user_id: auth0ID,
        },
      })) as Response;

      const {
        email_address: emailAddress,
        auth0_user_id: auth0UserID,
        has_seen_onboarding: hasSeenOnboarding, // will be undefined for now
        agency_id: userAgencies, // will be undefined for now
      } = await response.json();

      runInAction(() => {
        this.email = emailAddress;
        this.auth0UserID = auth0UserID;
        this.hasSeenOnboarding = hasSeenOnboarding; // will be set to undefined for now
        this.userAgencies = userAgencies; // will be set to undefined for now
      });
    } catch (error) {
      if (error instanceof Error) return error.message;
      return String(error);
    }
  }
}

export default UserStore;