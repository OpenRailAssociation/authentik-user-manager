"""Classes and functions for users and groups"""


class User:
    """Class for configured user.

    Attributes:
        id (int): The user's unique identifier.
        name (str): The user's name.
        email (str): The user's email address.
        current_groups (list[str]): The list of groups the user is currently a member of.
        configured_groups (list[str]): The list of groups the user is configured to be a member of.
        username (str): The username generated from the user's name.
        invite_name (str): The invitation name generated from the user's name.
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
        self.invite_name = self.user_name_to_invite_name()

    def user_name_to_username(self) -> str:
        """Convert user name to a username.

        Returns:
            str: The username created by converting the user's name.
        """
        return self.name.replace(" ", ".").lower()

    def user_name_to_invite_name(self) -> str:
        """Convert user name to an invitation name.

        Returns:
            str: The invitation name created by converting the user's name.
        """
        invite_name = self.name.replace(" ", "-").replace(".", "-")
        return "invite-" + invite_name.lower()
