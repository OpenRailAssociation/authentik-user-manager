"""
Fixtures for testing the auth_user_mgr package. This module provides fixtures to load sample
configurations and create User objects for testing purposes
"""

import pytest

from auth_user_mgr._config import read_app_and_users_config
from auth_user_mgr._user import User

CONFIG_APP_SAMPLE = "tests/data/sample/app.sample.yaml"
CONFIG_USERS_FILE_SAMPLE = "tests/data/sample/users.sample.yaml"
CONFIG_USERS_DIR_SAMPLE = "tests/data/sample/users.sample"


@pytest.fixture(name="sample_configs_userfile")
def fixture_sample_configs_userfile():
    """
    Fixture to load sample application and user configurations (single file).
    Returns:
        tuple: A tuple containing the application configuration and user configuration.
    """
    app_config, users_config = read_app_and_users_config(
        CONFIG_APP_SAMPLE, CONFIG_USERS_FILE_SAMPLE
    )
    return app_config, users_config


@pytest.fixture(name="sample_configs_userdir")
def fixture_sample_configs_userdir():
    """
    Fixture to load sample application and user configurations (directory).
    Returns:
        tuple: A tuple containing the application configuration and user configuration.
    """
    app_config, users_config = read_app_and_users_config(CONFIG_APP_SAMPLE, CONFIG_USERS_DIR_SAMPLE)
    return app_config, users_config


@pytest.fixture(name="sample_users")
def fixture_sample_users(sample_configs):
    """
    Fixture to create a list of User objects from sample user configurations.

    Args:
        sample_configs (tuple): A tuple containing the application configuration and
            user configuration.

    Returns:
        list: A list of User objects created from the sample user configurations.
    """
    _, users_config = sample_configs
    return [
        User(name=u["name"], email=u["email"], configured_groups=u.get("groups", []))
        for u in users_config
    ]
