"""Tests for _api.py"""

from auth_user_mgr._api import AuthentikAPI


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
