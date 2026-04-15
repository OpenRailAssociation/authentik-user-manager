# SPDX-FileCopyrightText: 2025 DB Systel GmbH
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for main.py."""

from unittest.mock import MagicMock

import pytest

from auth_user_mgr._api import AuthentikAPI
from auth_user_mgr._user import User
from auth_user_mgr.main import UserSync, get_groups_of_users


def test_check_existence_user_exists(sample_sync: UserSync) -> None:
    """Test check_existence returns True for an existing user and sets user.id."""
    sample_sync.api.get_pending_invitation_uuid_for_email = MagicMock(return_value="")
    user = User(name="Tester Testerson", email="tester@example.com", configured_groups=[])

    result = sample_sync.check_user_existence(user=user)

    assert result is True
    assert user.id == 1
    assert sample_sync.detail_messages == []


def test_check_existence_user_exists_stale_invitation(sample_sync: UserSync) -> None:
    """Test check_existence deletes stale invitations for existing users."""
    sample_sync.api.get_pending_invitation_uuid_for_email = MagicMock(return_value="inv-abc")
    sample_sync.api.delete_invitation = MagicMock()
    user = User(name="Tester Testerson", email="tester@example.com", configured_groups=[])

    result = sample_sync.check_user_existence(user=user)

    assert result is True
    sample_sync.api.delete_invitation.assert_called_once_with(invitation_uuid="inv-abc")
    assert len(sample_sync.detail_messages) == 1
    assert "tester@example.com (tester.testerson)" in sample_sync.detail_messages[0]
    assert "deleting stale invitation" in sample_sync.detail_messages[0]


def test_check_existence_user_not_found_pending_invitation(sample_sync: UserSync) -> None:
    """Test check_existence for a non-existing user with a pending invitation."""
    sample_sync.api.get_pending_invitation_url_for_email = MagicMock(
        return_value="https://auth.example.com/invite"
    )
    user = User(name="New User", email="new@example.com", configured_groups=[])

    result = sample_sync.check_user_existence(user=user)

    assert result is False
    assert len(sample_sync.detail_messages) == 1
    assert "new@example.com (new.user)" in sample_sync.detail_messages[0]
    assert "pending invitation" in sample_sync.detail_messages[0]


def test_check_existence_user_not_found_creates_invitation(sample_sync: UserSync) -> None:
    """Test check_existence creates an invitation for a new user without one."""
    sample_sync.api.get_pending_invitation_url_for_email = MagicMock(return_value="")
    sample_sync.api.create_invitation = MagicMock(return_value="https://auth.example.com/inv/new")
    user = User(name="New User", email="new@example.com", configured_groups=["Group 1"])

    result = sample_sync.check_user_existence(user=user)

    assert result is False
    sample_sync.api.create_invitation.assert_called_once_with(user=user)
    sample_sync.mail.send_email.assert_called_once()
    assert len(sample_sync.detail_messages) == 1
    assert "new@example.com (new.user)" in sample_sync.detail_messages[0]
    assert "invitation created and sent" in sample_sync.detail_messages[0]


def test_check_group_memberships_no_changes(sample_sync: UserSync) -> None:
    """Test check_group_memberships when groups are already in sync."""
    user = User(
        name="Tester Testerson",
        email="tester@example.com",
        configured_groups=["Group 1", "Group 2"],
    )
    user.id = 1

    result = sample_sync.check_group_memberships(user=user)

    assert result is False
    assert sample_sync.detail_messages == []


def test_check_group_memberships_add_group(sample_sync: UserSync) -> None:
    """Test check_group_memberships when a user needs to be added to a group."""
    sample_sync.api.add_user_to_group = MagicMock()
    user = User(
        name="Tester Testerson",
        email="tester@example.com",
        configured_groups=["Group 1", "Group 2", "Group 3"],
    )
    user.id = 1

    result = sample_sync.check_group_memberships(user=user)

    assert result is True
    sample_sync.api.add_user_to_group.assert_called_once_with(user_id=1, group_uuid="uuid-group-3")
    assert len(sample_sync.detail_messages) == 1
    assert "tester@example.com (tester.testerson)" in sample_sync.detail_messages[0]
    assert "added to group 'Group 3'" in sample_sync.detail_messages[0]


def test_check_group_memberships_remove_group(sample_sync: UserSync) -> None:
    """Test check_group_memberships when a user needs to be removed from a group."""
    sample_sync.api.delete_user_from_group = MagicMock()
    user = User(name="Tester Testerson", email="tester@example.com", configured_groups=["Group 1"])
    user.id = 1

    result = sample_sync.check_group_memberships(user=user)

    assert result is True
    sample_sync.api.delete_user_from_group.assert_called_once_with(
        user_id=1, group_uuid="uuid-group-2"
    )
    assert len(sample_sync.detail_messages) == 1
    assert "tester@example.com (tester.testerson)" in sample_sync.detail_messages[0]
    assert "removed from group 'Group 2'" in sample_sync.detail_messages[0]


def test_check_group_memberships_add_and_remove(sample_sync: UserSync) -> None:
    """Test check_group_memberships with both additions and removals."""
    sample_sync.api.add_user_to_group = MagicMock()
    sample_sync.api.delete_user_from_group = MagicMock()
    user = User(
        name="Tester Testerson",
        email="tester@example.com",
        configured_groups=["Group 1", "Group 3"],
    )
    user.id = 1

    result = sample_sync.check_group_memberships(user=user)

    assert result is True
    sample_sync.api.delete_user_from_group.assert_called_once_with(
        user_id=1, group_uuid="uuid-group-2"
    )
    sample_sync.api.add_user_to_group.assert_called_once_with(user_id=1, group_uuid="uuid-group-3")
    assert len(sample_sync.detail_messages) == 2


def test_sync_user_existing_unchanged(sample_sync: UserSync) -> None:
    """Test sync_user increments unchanged counter for existing user with no group changes."""
    sample_sync.api.get_pending_invitation_uuid_for_email = MagicMock(return_value="")
    user = User(
        name="Tester Testerson",
        email="tester@example.com",
        configured_groups=["Group 1", "Group 2"],
    )

    sample_sync.sync_user(user=user)

    assert sample_sync.users_unchanged == 1
    assert sample_sync.users_changed == 0
    assert sample_sync.users_pending == 0


def test_sync_user_existing_changed(sample_sync: UserSync) -> None:
    """Test sync_user increments changed counter for existing user with group changes."""
    sample_sync.api.get_pending_invitation_uuid_for_email = MagicMock(return_value="")
    sample_sync.api.add_user_to_group = MagicMock()
    user = User(
        name="Tester Testerson",
        email="tester@example.com",
        configured_groups=["Group 1", "Group 2", "Group 3"],
    )

    sample_sync.sync_user(user=user)

    assert sample_sync.users_unchanged == 0
    assert sample_sync.users_changed == 1
    assert sample_sync.users_pending == 0


def test_sync_user_pending(sample_sync: UserSync) -> None:
    """Test sync_user increments pending counter for non-existing user."""
    sample_sync.api.get_pending_invitation_url_for_email = MagicMock(
        return_value="https://auth.example.com/invite"
    )
    user = User(name="New User", email="new@example.com", configured_groups=[])

    sample_sync.sync_user(user=user)

    assert sample_sync.users_unchanged == 0
    assert sample_sync.users_changed == 0
    assert sample_sync.users_pending == 1


def test_print_summary_no_details(sample_sync: UserSync, capsys: pytest.CaptureFixture) -> None:
    """Test print_summary with no detail messages."""
    sample_sync.users_unchanged = 5
    sample_sync.users_changed = 0
    sample_sync.users_pending = 0

    sample_sync.print_summary(total_users=5)

    captured = capsys.readouterr()
    assert "Sync summary: 5 users processed" in captured.out
    assert "Unchanged: 5" in captured.out
    assert "Changed:   0" in captured.out
    assert "Pending:   0" in captured.out
    assert "Details:" not in captured.out


def test_print_summary_with_details(sample_sync: UserSync, capsys: pytest.CaptureFixture) -> None:
    """Test print_summary with detail messages."""
    sample_sync.users_unchanged = 3
    sample_sync.users_changed = 1
    sample_sync.users_pending = 1
    sample_sync.detail_messages = [
        "bob@example.com: added to group 'Admin'",
        "new@example.com: invitation created and sent: https://example.com/inv",
    ]

    sample_sync.print_summary(total_users=5)

    captured = capsys.readouterr()
    assert "Sync summary: 5 users processed" in captured.out
    assert "Unchanged: 3" in captured.out
    assert "Changed:   1" in captured.out
    assert "Pending:   1" in captured.out
    assert "Details:" in captured.out
    assert "bob@example.com: added to group 'Admin'" in captured.out
    assert "new@example.com: invitation created and sent" in captured.out


def test_get_groups_of_users(sample_api: AuthentikAPI, mock_api_call: callable) -> None:
    """Test get_groups_of_users returns both user-group mapping and group UUID cache."""
    mock_api_call("GET", "core-users-GET.json")

    # Mock list_groups to return groups with users and UUIDs
    sample_api.list_groups = MagicMock(
        return_value=[
            {"pk": "uuid-g1", "name": "Group 1", "users": [1, 3]},
            {"pk": "uuid-g2", "name": "Group 2", "users": [1]},
        ]
    )

    user_mapping, group_cache = get_groups_of_users(api=sample_api)

    assert user_mapping[1] == ["Group 1", "Group 2"]
    assert user_mapping[3] == ["Group 1"]
    assert group_cache == {"Group 1": "uuid-g1", "Group 2": "uuid-g2"}


def test_handle_unconfigured_users_disabled(sample_sync: UserSync) -> None:
    """Test handle_unconfigured_users does nothing when disabled."""
    sample_sync.delete_unconfigured_users = False
    sample_sync.api.delete_user = MagicMock()

    sample_sync.handle_unconfigured_users(configured_emails=set())

    sample_sync.api.delete_user.assert_not_called()
    assert sample_sync.users_deleted == 0


def test_handle_unconfigured_users_deletes_internal(sample_sync: UserSync) -> None:
    """Test handle_unconfigured_users deletes internal users not in config."""
    sample_sync.delete_unconfigured_users = True
    sample_sync.all_users_by_email = {
        "configured@example.com": {"pk": 1, "email": "configured@example.com", "type": "internal"},
        "extra@example.com": {
            "pk": 2,
            "email": "extra@example.com",
            "type": "internal",
            "username": "extra.user",
        },
    }
    sample_sync.api.delete_user = MagicMock()

    sample_sync.handle_unconfigured_users(configured_emails={"configured@example.com"})

    sample_sync.api.delete_user.assert_called_once_with(user_id=2)
    assert sample_sync.users_deleted == 1
    assert len(sample_sync.detail_messages) == 1
    assert "extra@example.com (extra.user)" in sample_sync.detail_messages[0]
    assert "deleted" in sample_sync.detail_messages[0]


def test_handle_unconfigured_users_skips_service_accounts(sample_sync: UserSync) -> None:
    """Test handle_unconfigured_users skips non-internal user types."""
    sample_sync.delete_unconfigured_users = True
    sample_sync.all_users_by_email = {
        "service@example.com": {
            "pk": 10,
            "email": "service@example.com",
            "type": "service_account",
        },
        "admin@example.com": {
            "pk": 11,
            "email": "admin@example.com",
            "type": "internal_service_account",
        },
        "external@example.com": {
            "pk": 12,
            "email": "external@example.com",
            "type": "external",
        },
    }
    sample_sync.api.delete_user = MagicMock()

    sample_sync.handle_unconfigured_users(configured_emails=set())

    sample_sync.api.delete_user.assert_not_called()
    assert sample_sync.users_deleted == 0


def test_handle_unconfigured_users_mixed(sample_sync: UserSync) -> None:
    """Test handle_unconfigured_users with a mix of types and configured users."""
    sample_sync.delete_unconfigured_users = True
    sample_sync.all_users_by_email = {
        "keep@example.com": {"pk": 1, "email": "keep@example.com", "type": "internal"},
        "delete@example.com": {"pk": 2, "email": "delete@example.com", "type": "internal"},
        "svc@example.com": {"pk": 3, "email": "svc@example.com", "type": "service_account"},
    }
    sample_sync.api.delete_user = MagicMock()

    sample_sync.handle_unconfigured_users(configured_emails={"keep@example.com"})

    sample_sync.api.delete_user.assert_called_once_with(user_id=2)
    assert sample_sync.users_deleted == 1


def test_print_summary_includes_deleted(
    sample_sync: UserSync, capsys: pytest.CaptureFixture
) -> None:
    """Test print_summary includes deleted count."""
    sample_sync.users_unchanged = 3
    sample_sync.users_changed = 0
    sample_sync.users_pending = 0
    sample_sync.users_deleted = 2
    sample_sync.detail_messages = [
        "a@example.com: deleted (not in user inventory)",
        "b@example.com: deleted (not in user inventory)",
    ]

    sample_sync.print_summary(total_users=3)

    captured = capsys.readouterr()
    assert "Deleted:   2" in captured.out
    assert "a@example.com: deleted" in captured.out
