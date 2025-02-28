# SPDX-FileCopyrightText: 2025 DB Systel GmbH
#
# SPDX-License-Identifier: Apache-2.0

"""Handle config files"""

import logging

import yaml


def read_yaml_config_file(path: str) -> dict:
    """Read a YAML config file and return a dict"""
    logging.debug("Reading config file: %s", path)
    try:
        with open(path, "r", encoding="utf-8") as file:
            return yaml.safe_load(file)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Config file not found: {path}") from exc


def read_app_and_users_config(app_config_path: str, user_config_path: str) -> tuple[dict, dict]:
    """Read app and user config files and return a tuple of dicts"""
    app_config = read_yaml_config_file(app_config_path)
    user_config = read_yaml_config_file(user_config_path)
    return app_config, user_config
