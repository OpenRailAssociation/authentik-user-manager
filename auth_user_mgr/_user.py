# SPDX-FileCopyrightText: 2025 DB Systel GmbH
#
# SPDX-License-Identifier: Apache-2.0

"""Classes and functions for users and groups"""

from slugify import slugify


class User:
    """Class for configured user.

    Attributes:
        id (int): The user's unique identifier.
        name (str): The user's name.
        email (str): The user's email address.
        current_groups (list[str]): The list of groups the user is currently a member of.
        configured_groups (list[str]): The list of groups the user is configured to be a member of.
        username (str): The username generated from the user's name.
        invite_slug (str): The invitation slug generated from the user's name.
    """

    def __init__(self, name: str, email: str, configured_groups: list[str]):
        """
        Args:
            name (str): The name of the user.
            email (str): The email address of the user.
            configured_groups (list[str]): The list of groups the user is configured to be
                a member of.
        """
        self.id: int
        self.name: str = name
        self.email: str = email
        self.current_groups: list[str]
        self.configured_groups: list[str] = sorted(configured_groups)
        self.username = self.user_name_to_username()
        self.invite_slug = self.user_name_to_invite_slug()

    def user_name_to_username(self) -> str:
        """Convert user name to a username.

        Returns:
            str: The username created by converting the user's name.
        """
        return slugify(self.name, separator=".")

    def user_name_to_invite_slug(self) -> str:
        """Convert user name to an invitation slug.

        Returns:
            str: The invitation slug created by converting the user's name.
        """
        return slugify("invite-" + self.name, separator="-", max_length=50)
