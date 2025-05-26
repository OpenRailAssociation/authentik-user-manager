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
    # Load the app and user config files
    app_config = read_yaml_config_file(app_config_path)
    user_config = read_yaml_config_file(user_config_path)

    # Check if the configs contain all required keys
    cfg_sanity_required_keys(
        cfg=app_config,
        required_keys=[
            "authentik_url",
            "authentik_token",
            "authentik_title",
            "invitation_flow_slug",
        ],
    )

    return app_config, user_config


def cfg_sanity_required_keys(cfg: dict, required_keys: list[str]) -> None:
    """Check if the config contains all required keys"""
    missing_keys = [key for key in required_keys if key not in cfg]
    if missing_keys:
        raise KeyError(f"Config is missing required keys: {', '.join(missing_keys)}")
    logging.debug("Config contains all required keys: %s", required_keys)
