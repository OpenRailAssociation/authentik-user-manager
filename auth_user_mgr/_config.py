# SPDX-FileCopyrightText: 2025 DB Systel GmbH
#
# SPDX-License-Identifier: Apache-2.0

"""Handle config files"""

import logging
from pathlib import Path

import yaml


def get_yaml_file_paths(file_or_dir: str) -> list[Path]:
    """Get paths of YAML files from a directory or a single file"""
    path = Path(file_or_dir)
    if path.is_dir():
        return list(path.glob("*.yml")) + list(path.glob("*.yaml"))
    if path.is_file() and path.suffix in {".yaml", ".yml"}:
        return [path]
    raise ValueError(f"Invalid path: {file_or_dir}. Must be a directory or a YAML file.")


def load_yaml_file(file_path: Path):
    """Load a YAML file and return its content"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Config file not found: {file_path}") from e
    except Exception as e:
        raise RuntimeError(f"Error reading YAML file {file_path}: {e}") from e


def check_unique_key(
    items: list[dict], seen_values: set[str], unique_key: str, source: Path
) -> None:
    """Check if the unique key/value exists in the items and raise an error if duplicates are
    found"""
    for item in items:
        assert isinstance(item, dict)
        value = item.get(unique_key, "")
        if value in seen_values:
            raise ValueError(
                f"The key/value '{unique_key}: {value}' in file '{source}' has already been seen."
            )
        seen_values.add(value)


def read_yaml_config_files(file_or_dir: str, unique_key: str = "") -> list[dict]:
    """Read YAML config files from a directory or a single file and return their content as a list
    of dictionaries. If a unique key is provided, ensure that all items have unique values for that
    key"""
    logging.debug("Reading config file/directory: %s", file_or_dir)
    yaml_file_paths = get_yaml_file_paths(file_or_dir)
    logging.debug("Found YAML files: %s", yaml_file_paths)

    seen_keys: set[str] = set()
    cfg_output: list[dict] = []

    for path in yaml_file_paths:
        logging.debug("Reading YAML file: %s", path)
        content = load_yaml_file(path)

        # If we handle multiple files, check for conflicting unique keys
        if unique_key and isinstance(content, list):
            check_unique_key(content, seen_keys, unique_key, path)

        # If the content is from a single file and not a list, wrap it in a list
        if len(yaml_file_paths) == 1:
            return content if isinstance(content, list) else [content]

        # Otherwise, assume it's a list of dictionaries, and extend the output list
        cfg_output.extend(content)

    return cfg_output


def cfg_sanity_required_keys(cfg: dict, required_keys: list[str]) -> None:
    """Check if the config contains all required keys"""
    missing_keys = [key for key in required_keys if key not in cfg]
    if missing_keys:
        raise KeyError(f"Config {cfg} is missing required keys: {', '.join(missing_keys)}")
    logging.debug("Config contains all required keys: %s", required_keys)


def read_app_and_users_config(
    app_config_path: str, user_config_path: str
) -> tuple[dict, list[dict]]:
    """Read app and user config files and return a tuple of dicts"""
    # Load the app and user config files
    app_config: dict = read_yaml_config_files(app_config_path)[0]  # is always a single file
    users_config: list[dict] = read_yaml_config_files(user_config_path, unique_key="email")

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
    for user in users_config:
        cfg_sanity_required_keys(cfg=user, required_keys=["name", "email"])

    return app_config, users_config
