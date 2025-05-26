# SPDX-FileCopyrightText: 2025 DB Systel GmbH
#
# SPDX-License-Identifier: Apache-2.0

"""Handle config files"""

import logging
from pathlib import Path

import yaml


def read_yaml_config_files(file_or_dir: str, unique_key: str = "") -> list[dict]:
    """Read a single YAML config file or a whole directory containing YAML files and return a
    (combined) dict"""
    logging.debug("Reading config file/directory: %s", file_or_dir)
    yaml_file_paths: list[Path] = []
    unique_key_values: list[str] = []
    cfg_output: list[dict] = []

    # Compose list of YAML file(s) from the given path
    path: Path = Path(file_or_dir)
    if path.is_dir():
        yaml_file_paths = list(path.glob("*.yml"))
        yaml_file_paths.extend(path.glob("*.yaml"))
    elif path.is_file() and path.suffix in {".yaml", ".yml"}:
        yaml_file_paths = [path]
    else:
        raise ValueError(f"Invalid path: {file_or_dir}. Must be a directory or a YAML file.")

    logging.debug("Found YAML files: %s", yaml_file_paths)

    for yaml_file_path in yaml_file_paths:
        logging.debug("Reading YAML file: %s", yaml_file_path)
        try:
            with open(yaml_file_path, "r", encoding="utf-8") as yaml_file:
                yaml_content = yaml.safe_load(yaml_file)

                # Check whether value of unique keys have been caught before
                if unique_key:
                    if isinstance(yaml_content, list):
                        for element in yaml_content:
                            assert isinstance(element, dict)
                            if (value := element.get(unique_key, "")) in unique_key_values:
                                raise ValueError(
                                    f"The key/value '{unique_key}: {value}' in file '{yaml_file_path}' "
                                    "has already been seen in the same or another file"
                                )
                            unique_key_values.append(value)
                if len(yaml_file_paths) == 1:
                    cfg_output.append(yaml_content)
                else:
                    cfg_output.extend(yaml_content)

        except FileNotFoundError as exc:
            raise FileNotFoundError(f"Config file not found: {path}") from exc
        except Exception as exc:
            raise RuntimeError(f"Error reading YAML file {yaml_file_path}: {exc}") from exc

    return cfg_output


def read_app_and_users_config(app_config_path: str, user_config_path: str) -> tuple[dict, dict]:
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

    return app_config, {"users": users_config}


def cfg_sanity_required_keys(cfg: dict, required_keys: list[str]) -> None:
    """Check if the config contains all required keys"""
    missing_keys = [key for key in required_keys if key not in cfg]
    if missing_keys:
        raise KeyError(f"Config {cfg} is missing required keys: {', '.join(missing_keys)}")
    logging.debug("Config contains all required keys: %s", required_keys)
