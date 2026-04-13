# SPDX-FileCopyrightText: 2025 DB Systel GmbH
#
# SPDX-License-Identifier: Apache-2.0

"""Test _config.py."""

import pytest

from auth_user_mgr._config import read_app_and_users_config
from tests.conftest import CONFIG_APP_SAMPLE

CONFIG_USERS_DIR_SAMPLE = "tests/data/sample/users.sample"
CONFIG_USERS_DIR_UNEQUAL = "tests/data/users.unequal"


def test_read_app_and_users_config(sample_configs_userfile: tuple[dict, list[dict]]) -> None:
    """Test reading application and user configurations from a file."""
    app_config, users_config = sample_configs_userfile
    assert isinstance(app_config, dict)
    assert isinstance(users_config, list)
    assert len(users_config) > 0


def test_non_existent_app_config() -> None:
    """Test reading non-existent application configuration."""
    with pytest.raises(ValueError):
        read_app_and_users_config("non_existent_app.yaml", CONFIG_USERS_DIR_SAMPLE)


def test_non_existent_users_dir() -> None:
    """Test reading non-existent users directory configuration."""
    with pytest.raises(ValueError):
        read_app_and_users_config(CONFIG_APP_SAMPLE, "non_existent_users_dir")


def test_app_config_missing_required_keys() -> None:
    """Test reading application configuration with missing required keys."""
    with pytest.raises(ValueError):
        read_app_and_users_config("tests/data/app.missing_required.yaml", CONFIG_USERS_DIR_SAMPLE)


def test_app_config_wrong_types() -> None:
    """Test reading application configuration with wrong types."""
    with pytest.raises(ValueError):
        read_app_and_users_config("tests/data/app.wrong_types.yaml", CONFIG_USERS_DIR_SAMPLE)


def test_app_config_unexpected_key() -> None:
    """Test reading application configuration with unexpected properties."""
    with pytest.raises(ValueError):
        read_app_and_users_config("tests/data/app.unexpected_keys.yaml", CONFIG_USERS_DIR_SAMPLE)


def test_user_config_missing_required_keys() -> None:
    """Test reading user configuration with missing required keys."""
    with pytest.raises(ValueError):
        read_app_and_users_config(CONFIG_APP_SAMPLE, "tests/data/users.missing_required.yaml")


def test_user_config_unexpected_keys() -> None:
    """Test reading user configuration with unexpected properties."""
    with pytest.raises(ValueError):
        read_app_and_users_config(CONFIG_APP_SAMPLE, "tests/data/users.unexpected_keys.yaml")


def test_user_config_wrong_indentation() -> None:
    """Test reading user configuration with wrong indentation."""
    with pytest.raises(ValueError):
        read_app_and_users_config(CONFIG_APP_SAMPLE, "tests/data/users.wrong_indent.yaml")


def test_user_config_wrong_indentation_2() -> None:
    """Test reading user configuration with wrong indentation, causing yaml.safe_load() to fail."""
    with pytest.raises(RuntimeError):
        read_app_and_users_config(CONFIG_APP_SAMPLE, "tests/data/users.wrong_indent2.yaml")


def test_users_config_content(sample_configs_userfile) -> None:
    """Test the content of the user configurations loaded from a file."""
    _, users_config = sample_configs_userfile
    assert isinstance(users_config, list)
    assert len(users_config) == 3
    for user in users_config:
        assert isinstance(user, dict)
        assert "name" in user
        assert "email" in user
    # Check specific user details. As they are sorted by email, we know which is which
    assert users_config[0]["name"] == "Jane Doe"
    assert users_config[0]["email"] == "jane@example.com"
    assert users_config[2]["groups"] == ["Group 1", "Group 2"]


def test_users_file_and_dir_equal(sample_configs_userfile) -> None:
    """Compare the user configurations loaded from a file and a directory. They should be equal."""
    _, users_file = sample_configs_userfile
    _, users_dir = read_app_and_users_config(CONFIG_APP_SAMPLE, CONFIG_USERS_DIR_SAMPLE)
    assert users_file == users_dir


def test_users_file_and_dir_unequal(sample_configs_userfile) -> None:
    """
    Compare the user configurations loaded from a file and a directory.

    These should NOT be equal.
    """
    _, users_file = sample_configs_userfile
    _, users_dir = read_app_and_users_config(CONFIG_APP_SAMPLE, CONFIG_USERS_DIR_UNEQUAL)
    assert users_file != users_dir


def test_users_config_duplicates() -> None:
    """
    Test reading user configurations with duplicate emails.
    This should raise a ValueError due to the unique email constraint.
    """
    with pytest.raises(ValueError):
        read_app_and_users_config(CONFIG_APP_SAMPLE, "tests/data/users.duplicates.yaml")
