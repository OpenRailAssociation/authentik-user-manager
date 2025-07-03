# SPDX-FileCopyrightText: 2025 DB Systel GmbH
#
# SPDX-License-Identifier: Apache-2.0

"""Functions for handling Authentik and its API"""

import json
import logging
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import requests

from ._helpers import make_url, remove_path_from_url
from ._user import User


class AuthentikAPI:  # pylint: disable=too-many-instance-attributes
    """Class for Authentik API and"""

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        url: str,
        token: str,
        invitation_flow_slug: str,
        invitation_expiry_days: int = 30,
        create_missing_groups: bool = False,
        dry: bool = False,
    ):
        """Initialize the Authentik API client.

        Args:
            url (str): Base URL of the Authentik instance.
            token (str): API token for authentication.
            invitation_flow_slug (str): Slug for the invitation flow.
            invitation_expiry_days (int, optional): Days the invitation is valid. Defaults to 30
            create_missing_groups (bool, optional): If True, missing groups will be created.
                Defaults to False
            dry (bool, optional): If True, non-GET API calls will not be executed. Defaults to False
        """
        self.url: str = url + "/api/v3"
        self.headers: dict[str, str] = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }
        self.flow_slug: str = invitation_flow_slug
        self.flow_uuid: str = self.get_invitation_flow_uuid()
        self.open_invitations: None | list[dict] = None
        self.invitation_expiry_days: int = int(invitation_expiry_days)
        self.create_missing_groups: bool = create_missing_groups
        self.dry: bool = dry

    def api_call(  # pylint: disable=too-many-positional-arguments, too-many-arguments
        self,
        url: str,
        method: str = "GET",
        data: dict | None = None,
        returns_list: bool = False,
    ):
        """Make an API call to Authentik.

        Args:
            url (str): The URL to make the API call to.

            method (str, optional): The HTTP method to use for the API call. Defaults to "GET".
                Valid values are "GET", "POST", "PATCH", and "DELETE".

            data (dict, optional): The data to send with the API call. Defaults to None.

            returns_list (bool, optional): Whether the API response should be returned as a list.
                Defaults to False.

        Returns:
            response (dict | list): The response from the API call, parsed as a dictionary.
                If `returns_list` is True, a list of dictionaries is returned.
                    If `self.dry` is True and method is not GET, an empty dictionary is returned.

        Raises:
            ValueError: If an invalid HTTP method is provided.
        """
        logging.info("API call: %s %s with data %s", method, url, data)

        if method == "GET":
            response = requests.get(url, headers=self.headers, params=data, timeout=10)
        else:
            # In dry run, do not execute non-GET calls but return empty dict
            if self.dry:
                logging.info("Dry run, not executing the above API call")
                if returns_list:
                    return [{}]
                return {}

            if method == "POST":
                response = requests.post(url, headers=self.headers, json=data, timeout=10)
            elif method == "PATCH":
                response = requests.patch(url, headers=self.headers, json=data, timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, headers=self.headers, timeout=10)
            else:
                raise ValueError(f"Invalid method: {method}")

        if response.status_code not in range(200, 300):
            logging.error(
                "API call '%s %s' with data '%s' exited with a non 2xx status code (%s): %s",
                method,
                url,
                data,
                response.status_code,
                response.text,
            )

        # Convert response JSON to dict
        try:
            result: dict = json.loads(response.text)
            if returns_list:
                logging.debug("API response pagination: %s", result.get("pagination", {}))
                list_result: list[dict] = result.get("results", [])
                return list_result
            return result
        except json.JSONDecodeError:
            logging.debug("API response is not valid JSON: %s", response.text)
            return {}

    # --------------------------------------------------------------------------
    # USERS
    # --------------------------------------------------------------------------

    def list_users(self) -> list[dict]:
        """List all users"""
        api_url = self.url + "/core/users/"
        return self.api_call(url=api_url, returns_list=True)

    def get_users(self, **attributes) -> list[dict]:
        """Get one or multiple users by optional attributes, see
        https://docs.goauthentik.io/docs/developer-docs/api/reference/core-users-list"""
        api_url = self.url + "/core/users/"
        return self.api_call(url=api_url, data=attributes, returns_list=True)

    def get_user_by_id(self, user_id: int) -> dict:
        """Get a specific user by their ID ('pk' key in user dict)"""
        api_url = self.url + "/core/users/" + str(user_id) + "/"
        return self.api_call(url=api_url)

    # --------------------------------------------------------------------------
    # INVITATIONS
    # --------------------------------------------------------------------------

    def get_flows(self, **attributes) -> list[dict]:
        """Get one or multiple flows by optional attributes, see
        https://docs.goauthentik.io/docs/developer-docs/api/reference/flows-instances-list"""
        api_url = self.url + "/flows/instances/"
        return self.api_call(url=api_url, data=attributes, returns_list=True)

    def get_all_open_invitations(self) -> list[dict]:
        """Retrieve all open invitations"""
        api_url = self.url + "/stages/invitation/invitations/"
        return self.api_call(url=api_url, returns_list=True)

    def get_invitation_by_id(self, invitation_id: int) -> dict:
        """Get a specific invitation by their ID ('pk' key in dict)"""
        api_url = self.url + "/stages/invitation/invitations/" + str(invitation_id) + "/"
        return self.api_call(url=api_url)

    def get_invitation_flow_uuid(self) -> str:
        """Get the invitation flow uuid by its slug"""
        flow = self.get_flows(slug=self.flow_slug)
        if len(flow) == 0:
            raise ValueError(f"Flow with slug {flow} not found")
        if len(flow) > 1:
            raise ValueError(f"Multiple flows with slug {flow} found")
        try:
            return str(flow[0]["pk"])
        except KeyError as exc:
            raise KeyError(f"Flow with slug {flow} has no 'pk' key") from exc

    def get_invitation_link(self, invitation_id: str):
        """Create the link with which a user can sign up"""
        return make_url(
            remove_path_from_url(self.url),
            "if",
            "flow",
            self.flow_slug,
            "/",
            itoken=invitation_id,
        )

    def create_invitation(self, user: User) -> str:
        """Create a new invitation and return invitation URL"""
        # Usernames should be unique
        if self.get_users(username=user.username):
            raise ValueError(f"User {user.username} already exists")

        api_url = self.url + "/stages/invitation/invitations/"
        # Create an expiry time of now + by default 30 days
        expiry_time = datetime.now(timezone.utc) + timedelta(days=self.invitation_expiry_days)
        data = {
            "name": user.invite_slug,  # name if invitation
            "expires": expiry_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "single_use": False,
            "flow": self.flow_uuid if self.flow_uuid else None,
            "fixed_data": {
                "name": user.name,
                "email": user.email,
                "username": user.username,
                "groups_to_add": user.configured_groups,
            },
        }
        api_result = self.api_call(url=api_url, method="POST", data=data)
        return self.get_invitation_link(invitation_id=api_result.get("pk", ""))

    def get_pending_invitation_url_for_email(self, email: str) -> str:
        """Check if an email is part of a pending invitation, and return invitation URL"""
        # Only fetch open invitations once, if not already done
        if self.open_invitations is None:
            self.open_invitations = self.get_all_open_invitations()
        for open_invitation in self.open_invitations:
            if open_invitation.get("fixed_data", {}).get("email", "") == email:
                return self.get_invitation_link(open_invitation.get("pk", ""))
        return ""

    def get_pending_invitation_uuid_for_email(self, email: str) -> str:
        """Check if an email is part of a pending invitation, and return invitation UUID"""
        invitation_url = self.get_pending_invitation_url_for_email(email)
        if invitation_url:
            parsed_url = urlparse(invitation_url)
            return parsed_url.query.split("=")[1]

        return ""

    def delete_invitation(self, invitation_uuid: str) -> None:
        """Delete an invitation"""
        api_url = self.url + "/stages/invitation/invitations/" + invitation_uuid + "/"
        self.api_call(url=api_url, method="DELETE")

    # --------------------------------------------------------------------------
    # GROUPS
    # --------------------------------------------------------------------------

    def list_groups(self) -> list[dict]:
        """List all groups"""
        api_url = self.url + "/core/groups/"
        return self.api_call(url=api_url, returns_list=True)

    def create_group(self, group_name: str) -> str:
        """Create a new group"""
        api_url = self.url + "/core/groups/"
        data = {"name": group_name}
        group = self.api_call(url=api_url, method="POST", data=data)
        print("Group created:", group_name)
        return str(group.get("pk", ""))

    def get_group_uuid_by_name(self, group_name: str) -> str:
        """Get a specific group's uuid by its name"""
        api_url = self.url + "/core/groups/"
        group = self.api_call(url=api_url, data={"name": group_name}, returns_list=True)

        if len(group) == 0:
            if self.create_missing_groups:
                # Create group if it does not exist
                logging.info("Group %s does not exist, creating it", group_name)
                return self.create_group(group_name=group_name)

            raise ValueError(f"No group with name {group_name} found")
        if len(group) > 1:
            raise ValueError(f"Multiple groups with name {group_name} found")
        try:
            return str(group[0]["pk"])
        except KeyError as exc:
            raise KeyError(f"Group with name {group_name} has no 'pk' key") from exc

    def get_group_by_uuid(self, group_uuid: str) -> dict:
        """Get a specific group by its uuid"""
        api_url = self.url + "/core/groups/" + group_uuid + "/"
        return self.api_call(url=api_url)

    def add_user_to_group(self, user_id: int, group_uuid: str) -> None:
        """Add a user to a group"""
        api_url = self.url + "/core/groups/" + str(group_uuid) + "/add_user/"
        data = {"pk": user_id}
        self.api_call(url=api_url, method="POST", data=data)

    def delete_user_from_group(self, user_id: int, group_uuid: str) -> None:
        """Delete a user from a group"""
        api_url = self.url + "/core/groups/" + str(group_uuid) + "/remove_user/"
        data = {"pk": user_id}
        return self.api_call(url=api_url, method="POST", data=data)
