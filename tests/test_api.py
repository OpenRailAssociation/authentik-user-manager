"""Tests for _api.py"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from auth_user_mgr._api import AuthentikAPI

API_FIXTURE_DIR = Path("tests/data/api")


def load_api_fixture(name):
    """Load a JSON API fixture from the API fixtures directory"""
    path = API_FIXTURE_DIR / name
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@patch("auth_user_mgr._api.requests.get")
def test_list_users(mock_get, sample_api: AuthentikAPI):
    """Test the list_users method of AuthentikAPI"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = json.dumps(load_api_fixture("core-users-GET.json"))
    mock_get.return_value = mock_response

    users = sample_api.list_users()
    assert isinstance(users, list)
    assert users[0]["email"] == "tester@example.com"
    assert users[0]["groups"] == [
        "6e981209-8621-4484-993d-dc9882a8747c",
        "ba911f0c-236f-420c-82d0-76503500061a",
    ]


@patch("auth_user_mgr._api.requests.get")
def test_get_users_with_filter(mock_get, sample_api: AuthentikAPI):
    """Test get_users with attribute filtering (e.g. email=...)"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = json.dumps(load_api_fixture("core-users-GET-filter.json"))
    mock_get.return_value = mock_response

    users = sample_api.get_users(email="tester@example.com")
    assert isinstance(users, list)
    assert users[0]["email"] == "tester@example.com"
    mock_get.assert_called_once()
    called_url = mock_get.call_args[1]["params"]
    assert called_url["email"] == "tester@example.com"


@patch("auth_user_mgr._api.requests.get")
def test_get_user_by_id(mock_get, sample_api: AuthentikAPI):
    """Test get_user_by_id returns correct user dict"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = json.dumps(load_api_fixture("core-users-GET-id-3.json"))
    mock_get.return_value = mock_response

    user = sample_api.get_user_by_id(3)
    assert isinstance(user, dict)
    assert user["email"] == "john@example.net"
    mock_get.assert_called_once()
    assert "/core/users/3/" in mock_get.call_args[0][0]
