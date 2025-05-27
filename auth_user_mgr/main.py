# SPDX-FileCopyrightText: 2025 DB Systel GmbH
#
# SPDX-License-Identifier: Apache-2.0

"""Module for managing Authentik users and group memberships via YAML configuration files.

This module provides functionality to synchronize user accounts and group memberships in
Authentik based on YAML configuration files. It supports user invitation management,
group membership synchronization, and provides a command-line interface for operations.
"""

import argparse
import logging

from . import __version__
from ._api import AuthentikAPI
from ._config import read_app_and_users_config
from ._email import Mail
from ._helpers import compare_two_lists
from ._user import User

# Main parser with root-level flags
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--version", action="version", version="%(prog)s " + __version__)

# Initiate first-level subcommands
subparsers = parser.add_subparsers(dest="command", help="Available commands", required=True)

# Common flags, usable for all effective subcommands
common_flags = argparse.ArgumentParser(add_help=False)  # No automatic help to avoid duplication
common_flags.add_argument("-v", "--verbose", action="store_true", help="Print INFO logging")
common_flags.add_argument("-vv", "--debug", action="store_true", help="Print DEBUG logging")

# SYNC commands
parser_sync = subparsers.add_parser(
    "sync", parents=[common_flags], help="Synchronise users to the Authentik instance"
)
parser_sync.add_argument("-c", "--config", help="Path to app config file", required=True)
parser_sync.add_argument(
    "-u", "--users", help="Path to user inventory file or directory", required=True
)
parser_sync.add_argument(
    "--dry",
    action="store_true",
    help="Run a dry sync which does not make any productive changes and does not send emails",
)
parser_sync.add_argument("--no-email", action="store_true", help="Do not send any emails")


def configure_logger(verbose: bool = False, debug: bool = False) -> logging.Logger:
    """
    Configure and return a logger with appropriate settings. If verbose or debug is False (default),
    logging level is WARNING

    Args:
        verbose (bool, optional): If True, sets log level to INFO. Defaults to False.
        debug (bool, optional): If True, sets log level to DEBUG. Defaults to False.

    Returns:
        logging.Logger: Configured logger instance.
    """
    log = logging.getLogger()
    logging.basicConfig(
        encoding="utf-8",
        format="[%(asctime)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    if debug:
        log.setLevel(logging.DEBUG)
    elif verbose:
        log.setLevel(logging.INFO)
    else:
        log.setLevel(logging.WARNING)

    return log


def get_groups_of_users(api: AuthentikAPI) -> dict[int, list[str]]:
    """Build a mapping of user IDs to their current group memberships.

    Args:
        api (AuthentikAPI): Authentik API client instance.

    Returns:
        dict[int, list[str]]: A dictionary mapping user IDs to sorted lists of group names that the
            user belongs to.
    """
    users_groups_mapping: dict[int, list[str]] = {}
    for group_dict in api.list_groups():
        group_name = group_dict.get("name", "")
        logging.debug("Processing screen of members of group %s", group_name)
        # Iterate all members of this group
        for user_id in group_dict.get("users", []):
            # Initialise list of group names if not present, otherwise add to it
            if user_id not in users_groups_mapping:
                users_groups_mapping[user_id] = [group_name]
            else:
                users_groups_mapping[user_id].append(group_name)

    # Alphabetically sort the list of groups
    for user_id, groups in users_groups_mapping.items():
        users_groups_mapping[user_id] = sorted(groups)

    return users_groups_mapping


def user_check_existence(
    api: AuthentikAPI, user: User, mail: Mail, invitation_template: str = ""
) -> bool:
    """Check if a user exists in Authentik and handle invitations accordingly.

    This function checks if a user exists, and if not, manages the invitation process.
    It also cleans up any pending invitations for existing users.

    Args:
        api (AuthentikAPI): Authentik API client instance.
        user (User): User object containing email and other user details.
        mail (Mail): Mail object for sending invitations.
        invitation_template (str, optional): Path to a custom invitation template file.
            Defaults to an empty string in which case the inbuilt template is used.

    Returns:
        bool: True if user exists, False if user needs to be invited.
    """
    logging.info("Processing user %s", user.email)
    user_exists = api.get_users(email=user.email)
    # CHeck if user already exists
    if user_exists:
        # Add user ID
        user.id = user_exists[0].get("pk", 0)

        print(f"User {user.email} already exists (ID: {user.id})")

        # Check if user still has an still an invitation pending
        if invite_uuid := api.get_pending_invitation_uuid_for_email(user.email):
            print(f"User {user.email} is still pending invitation: {invite_uuid}")
            # Delete invitation
            api.delete_invitation(invitation_uuid=invite_uuid)
            print(f"User {user.email} invitation deleted: {invite_uuid}")

        return True

    # Check if user is pending invitation. If not, create invitation
    if invite_url := api.get_pending_invitation_url_for_email(user.email):
        print(f"User {user.email} is pending invitation: {invite_url}")
    else:
        invitation_url = api.create_invitation(user=user)
        mail.send_email(
            recipient=user.email,
            message="invitation",
            template_file=invitation_template,
            link=invitation_url,
            invitation_expiry_days=api.invitation_expiry_days,
        )
        print(f"Invitation created for and sent to {user.email}: {invitation_url}")

    return False


def user_check_group_memberships(
    api: AuthentikAPI,
    user: User,
    user_group_mapping: dict[int, list[str]],
    group_name_uuid_cache: dict[str, str],
) -> None:
    """Compare and synchronize a user's configured and current group memberships.

    This function compares the user's configured group memberships with their current status
    and makes the necessary adjustments by adding or removing the user from groups.

    Args:
        api (AuthentikAPI): Authentik API client instance.
        user (User): User object containing current and configured group memberships.
        user_group_mapping (dict[int, list[str]]): Mapping of user IDs to their current
            group memberships.
        group_name_uuid_cache (dict[str, str]): Cache of group names to their UUIDs for
            efficient lookups.

    Returns:
        None
    """
    # Compare configured group memberships with current status
    user.current_groups = user_group_mapping.get(user.id, [])

    # Compare configured and current group memberships
    delete_from_groups, in_sync, add_to_groups = compare_two_lists(
        user.configured_groups, user.current_groups
    )
    logging.info(
        "User %s: %s",
        user.email,
        {
            "delete_from_groups": delete_from_groups,
            "in_sync": in_sync,
            "add_to_groups": add_to_groups,
        },
    )

    # Delete user from groups
    for group in delete_from_groups:
        if group not in group_name_uuid_cache:
            group_name_uuid_cache[group] = api.get_group_uuid_by_name(group)
        api.delete_user_from_group(user_id=user.id, group_uuid=group_name_uuid_cache[group])
        print(f"User {user.email} removed from group {group}")

    # Add user to groups
    for group in add_to_groups:
        if group not in group_name_uuid_cache:
            group_name_uuid_cache[group] = api.get_group_uuid_by_name(group)
        api.add_user_to_group(user_id=user.id, group_uuid=group_name_uuid_cache[group])
        print(f"User {user.email} added to group {group}")


def cli() -> None:
    """Command-line interface entry point for the Authentik user management tool.

    This function serves as the main entry point for the CLI tool. It handles command-line
    arguments, initializes logging, and orchestrates the synchronization of users and their group
    memberships with Authentik when the 'sync' command is used.

    Returns:
        None
    """
    args = parser.parse_args()
    configure_logger(verbose=args.verbose, debug=args.debug)

    if args.command == "sync":
        cfg_app, cfg_users = read_app_and_users_config(args.config, args.users)

        # Initiate classes
        api = AuthentikAPI(
            url=cfg_app.get("authentik_url", ""),
            token=cfg_app.get("authentik_token", ""),
            invitation_flow_slug=cfg_app.get("invitation_flow_slug", ""),
            create_missing_groups=cfg_app.get("create_missing_groups", False),
            invitation_expiry_days=cfg_app.get("invitation_expiry_days", 30),
            dry=args.dry,
        )
        mail = Mail(
            smtp_server=cfg_app.get("smtp_server", ""),
            smtp_port=cfg_app.get("smtp_port", ""),
            smtp_user=cfg_app.get("smtp_user", ""),
            smtp_password=cfg_app.get("smtp_password", ""),
            smtp_starttls=cfg_app.get("smtp_starttls", False),
            smtp_from=cfg_app.get("smtp_from", ""),
            dry=any([args.dry, args.no_email]),
        )
        mail.create_copy_with_details(
            subject_suffix="Invitation to create account",
            instance_url=cfg_app.get("authentik_url", ""),
            instance_title=cfg_app.get("authentik_title", ""),
        )

        # Get all current groups and their users
        users_and_groups = get_groups_of_users(api=api)

        # Create a cache for group name-to-uuid mappings
        group_name_uuid_cache: dict[str, str] = {}

        # Iterate all configured users
        for user_dict in cfg_users:
            user = User(
                name=user_dict.get("name", ""),
                email=user_dict.get("email", ""),
                configured_groups=user_dict.get("groups", []),
            )
            # Check if user exists. If not invite them.
            if user_check_existence(api=api, user=user, mail=mail):
                user_check_group_memberships(
                    api=api,
                    user=user,
                    user_group_mapping=users_and_groups,
                    group_name_uuid_cache=group_name_uuid_cache,
                )


if __name__ == "__main__":
    cli()
