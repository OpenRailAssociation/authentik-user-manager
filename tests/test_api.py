"""Tests for _api.py"""

from auth_user_mgr._api import AuthentikAPI
from auth_user_mgr._user import User


def test_list_users(sample_api: AuthentikAPI, mock_api_call):
    """Test the list_users method of AuthentikAPI"""
    mock_api_call("GET", "core-users-GET.json")
    users = sample_api.list_users()

    assert isinstance(users, list)
    assert users[0]["email"] == "tester@example.com"
    assert users[0]["groups"] == [
        "6e981209-8621-4484-993d-dc9882a8747c",
        "ba911f0c-236f-420c-82d0-76503500061a",
    ]


def test_get_users_with_filter(sample_api: AuthentikAPI, mock_api_call):
    """Test get_users with attribute filtering (e.g. email=...)"""
    mock_get = mock_api_call("GET", "core-users-GET-filter.json")
    users = sample_api.get_users(email="tester@example.com")

    assert users[0]["email"] == "tester@example.com"

    mock_get.assert_called_once()
    assert mock_get.call_args[1]["params"]["email"] == "tester@example.com"


def test_get_user_by_id(sample_api: AuthentikAPI, mock_api_call):
    """Test get_user_by_id returns correct user dict"""
    mock_get = mock_api_call("GET", "core-users-GET-id-3.json")
    user = sample_api.get_user_by_id(3)

    assert isinstance(user, dict)
    assert user["email"] == "john@example.net"

    mock_get.assert_called_once()
    assert "/core/users/3/" in mock_get.call_args[0][0]


def test_get_invitation_link(sample_api: AuthentikAPI):
    """Test get_invitation_link returns correct invitation link"""
    # Example UUID
    invitation_id = "abc123"

    # Expect base URL without /api/v3
    sample_api.url = "https://auth.example.com/api/v3"

    link = sample_api.get_invitation_link(invitation_id)

    assert link == "https://auth.example.com/if/flow/invitation-flow/?itoken=abc123"


def test_create_invitation(sample_api: AuthentikAPI, mock_api_call):
    """Test create_invitation creates an invitation and returns the link"""
    # Mock the POST invitation creation
    sample_api.get_users = lambda **kwargs: [] # type: ignore[method-assign]
    mock_post = mock_api_call("POST", "stages-invitatation-invitations-POST.json")

    # Prepare the user
    user = User(name="Alice Test", email="alice@example.com", configured_groups=["Group A"])

    # Call the method
    invite_link = sample_api.create_invitation(user)

    # Check the output
    assert invite_link == "https://auth.example.com/if/flow/invitation-flow/?itoken=inv123"

    # Check request was made once
    mock_post.assert_called_once()
    data = mock_post.call_args[1]["json"]
    assert data["fixed_data"]["email"] == "alice@example.com"
    assert data["flow"] == "fake-flow-uuid"
