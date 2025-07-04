"""Test _config.py"""

from pytest import raises

from auth_user_mgr._config import read_app_and_users_config
from tests.conftest import CONFIG_APP_SAMPLE

CONFIG_USERS_DIR_SAMPLE = "tests/data/sample/users.sample"
CONFIG_USERS_DIR_UNEQUAL = "tests/data/users.unequal"


def test_read_app_and_users_config(sample_configs_userfile):
    """
    Test reading application and user configurations from a file.
    """
    app_config, users_config = sample_configs_userfile
    assert isinstance(app_config, dict)
    assert isinstance(users_config, list)
    assert len(users_config) > 0


def test_non_existent_app_config():
    """
    Test reading non-existent application configuration.
    """
    with raises(ValueError):
        read_app_and_users_config("non_existent_app.yaml", CONFIG_USERS_DIR_SAMPLE)


def test_non_existent_users_dir():
    """
    Test reading non-existent users directory configuration.
    """
    with raises(ValueError):
        read_app_and_users_config(CONFIG_APP_SAMPLE, "non_existent_users_dir")


def test_app_config_missing_required_keys():
    """
    Test reading application configuration with missing required keys.
    """
    with raises(KeyError):
        read_app_and_users_config(
            "tests/data/app.missing_required.yaml", CONFIG_USERS_DIR_SAMPLE
        )

def test_users_config_content(sample_configs_userfile):
    """
    Test the content of the user configurations loaded from a file.
    """
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


def test_users_file_and_dir_equal(sample_configs_userfile):
    """
    Compare the user configurations loaded from a file and a directory. They should be equal.
    """
    _, users_file = sample_configs_userfile
    _, users_dir = read_app_and_users_config(CONFIG_APP_SAMPLE, CONFIG_USERS_DIR_SAMPLE)
    assert users_file == users_dir


def test_users_file_and_dir_unequal(sample_configs_userfile):
    """
    Compare the user configurations loaded from a file and a directory. These should NOT be equal.
    """
    _, users_file = sample_configs_userfile
    _, users_dir = read_app_and_users_config(CONFIG_APP_SAMPLE, CONFIG_USERS_DIR_UNEQUAL)
    assert users_file != users_dir

def test_users_config_duplicates():
    """
    Test reading user configurations with duplicate emails.
    This should raise a ValueError due to the unique email constraint.
    """
    with raises(ValueError):
        read_app_and_users_config(
            CONFIG_APP_SAMPLE, "tests/data/users.duplicates.yaml"
        )
