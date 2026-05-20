# SPDX-FileCopyrightText: 2025 DB Systel GmbH
#
# SPDX-License-Identifier: Apache-2.0

"""Handle config files for application and users."""

import csv
import logging
from pathlib import Path

from jsonschema import FormatChecker, validate
from jsonschema.exceptions import ValidationError
from ruamel.yaml import YAML

APP_CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "authentik_url": {"type": "string", "format": "uri"},
        "authentik_token": {"type": "string"},
        "authentik_title": {"type": "string"},
        "invitation_flow_slug": {"type": "string"},
        "smtp_server": {"type": "string"},
        "smtp_port": {"type": "integer"},
        "smtp_user": {"type": "string"},
        "smtp_password": {"type": "string"},
        "smtp_starttls": {"type": "boolean"},
        "smtp_from": {"type": "string", "format": "email"},
        "create_missing_groups": {"type": "boolean"},
        "delete_unconfigured_users": {"type": "boolean"},
        "invitation_expiry_days": {"type": "integer"},
    },
    "required": [
        "authentik_url",
        "authentik_token",
        "authentik_title",
        "invitation_flow_slug",
    ],
    "additionalProperties": False,
}

USER_CONFIG_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "email": {"type": "string", "format": "email"},
            "username": {"type": "string"},
            "groups": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "required": ["name", "email"],
        "additionalProperties": False,
    },
}


def get_yaml_file_paths(file_or_dir: str) -> list[Path]:
    """Get paths of YAML files from a directory or a single file."""
    path = Path(file_or_dir)
    if path.is_dir():
        return list(path.glob("*.yml")) + list(path.glob("*.yaml"))
    if path.is_file() and path.suffix in {".yaml", ".yml"}:
        return [path]
    msg = f"Invalid path: {file_or_dir}. Must be a directory or a YAML file."
    raise ValueError(msg)


def _get_yaml() -> YAML:
    """Return a configured ruamel.yaml YAML instance."""
    yml = YAML()
    yml.preserve_quotes = True
    yml.indent(mapping=2, sequence=4, offset=2)
    return yml


def _prettify_yaml_formatting(text: str) -> str:
    """Pretty-print YAML formatting for better readability (opinionated).

    Fix root-level YAML sequence formatting. ruamel.yaml's indent(offset=2) applies to all sequence
    levels including root, producing '  - item' at the top level. This transform strips that extra
    indent so root items start at column 0 while nested sequences remain properly indented.

    Additionally, ensures a blank line separates each root-level list item for readability.
    """
    lines = text.split("\n")
    dedented = [line.removeprefix("  ") for line in lines]

    # Insert blank lines between root-level list items (lines starting with '- ')
    # but not after comments (comments belong with the item that follows them)
    result: list[str] = []
    for i, line in enumerate(dedented):
        if (
            i > 0
            and line.startswith("- ")
            and dedented[i - 1] != ""
            and not dedented[i - 1].startswith("#")
        ):
            result.append("")
        result.append(line)

    return "\n".join(result)


def load_yaml_file(file_path: Path) -> dict | list[dict]:
    """Load a YAML file and return its content."""
    try:
        yml = _get_yaml()
        with open(file_path, encoding="utf-8") as f:
            data = yml.load(f)
        return data if data is not None else []  # noqa: TRY300
    except FileNotFoundError as e:
        msg = f"Config file not found: {file_path}"
        raise FileNotFoundError(msg) from e
    except Exception as e:
        msg = f"Error reading YAML file {file_path}: {e}"
        raise RuntimeError(msg) from e


def save_yaml_file(file_path: Path, data: dict | list[dict]) -> None:
    """Write data to a YAML file, preserving comments if originally loaded with ruamel.yaml."""
    yml = _get_yaml()
    with open(file_path, "w", encoding="utf-8") as f:
        yml.dump(data, f, transform=_prettify_yaml_formatting)


def check_unique_key(
    items: list[dict], seen_values: set[str], unique_key: str, source: Path
) -> None:
    """Check if the unique key/value exists in the items and raise an error if duplicates are
    found.
    """
    for item in items:
        if not isinstance(item, dict):
            msg = (
                f"Invalid item in file '{source}': "
                f"expected a dictionary, got {type(item).__name__}."
            )
            raise TypeError(msg)
        value = item.get(unique_key, "")
        if value in seen_values:
            msg = f"The key/value '{unique_key}: {value}' in file '{source}' has already been seen."
            raise ValueError(msg)
        seen_values.add(value)


def read_yaml_config_files(file_or_dir: str, unique_key: str = "") -> list[dict]:
    """Read YAML config files from a directory or a single file and return their content as a list
    of dictionaries. If a unique key is provided, ensure that all items have unique values for that
    key.
    """
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
            # Sort the content by the unique key
            content.sort(key=lambda x: x.get(unique_key, ""))

        # If the content is from a single file and not a list, wrap it in a list
        if len(yaml_file_paths) == 1:
            return content if isinstance(content, list) else [content]

        # Otherwise, assume it's a list of dictionaries, and extend the output list
        cfg_output.extend(content)

    # Sort the output list by the unique key if provided, again
    if unique_key:
        cfg_output.sort(key=lambda x: x.get(unique_key, ""))

    return cfg_output


def validate_config_schema(cfg: dict | list[dict], schema: dict) -> None:
    """Validate the config against a JSON schema."""
    try:
        validate(instance=cfg, schema=schema, format_checker=FormatChecker())
    except ValidationError as e:
        logging.critical("Config validation failed: %s", e.message)
        raise ValueError(e) from None
    logging.debug("Config validated successfully against schema.")


def read_app_and_users_config(
    app_config_path: str, user_config_path: str
) -> tuple[dict, list[dict]]:
    """Read app and user config files and return a tuple of dicts."""
    # Load the app and user config files
    app_config: dict = read_yaml_config_files(app_config_path)[0]  # is always a single file
    users_config: list[dict] = read_yaml_config_files(user_config_path, unique_key="email")

    # Validate the configs against their schemas and required keys
    validate_config_schema(cfg=app_config, schema=APP_CONFIG_SCHEMA)
    validate_config_schema(cfg=users_config, schema=USER_CONFIG_SCHEMA)

    return app_config, users_config


def parse_csv_users(csv_path: str) -> list[dict]:
    """Parse a CSV file containing user data for import.

    Expected columns: name, email (required); username (optional).
    Rows with empty name or email are skipped.

    Args:
        csv_path (str): Path to the CSV file.

    Returns:
        list[dict]: List of user dictionaries with keys: name, email, and optionally username.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
        ValueError: If required columns (name, email) are missing from the CSV header.
    """
    path = Path(csv_path)
    if not path.is_file():
        msg = f"CSV file not found: {csv_path}"
        raise FileNotFoundError(msg)

    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, skipinitialspace=True)

        # Validate required columns
        fieldnames = [name.strip() for name in (reader.fieldnames or [])]
        for required in ("name", "email"):
            if required not in fieldnames:
                msg = f"CSV file is missing required column: '{required}'"
                raise ValueError(msg)

        users: list[dict] = []
        for row in reader:
            # Strip whitespace from keys and values
            clean_row = {k.strip(): v.strip() for k, v in row.items() if k is not None}

            name = clean_row.get("name", "")
            email = clean_row.get("email", "")

            # Skip rows with missing required fields
            if not name or not email:
                logging.debug("Skipping CSV row with empty name or email: %s", clean_row)
                continue

            user: dict = {"name": name, "email": email}
            username = clean_row.get("username", "")
            if username:
                user["username"] = username

            users.append(user)

    # Validate parsed users against the user config schema
    validate_config_schema(cfg=users, schema=USER_CONFIG_SCHEMA)

    logging.info("Parsed %d users from CSV file: %s", len(users), csv_path)
    return users


def _append_groups_in_place(user_entry: dict, new_groups: list[str]) -> None:
    """Append new groups to a user entry's groups list, preserving ruamel.yaml metadata.

    Handles moving end-of-sequence comments (blank lines, section headers) so they remain
    at the end after appending new items.
    """
    if user_entry.get("groups") is None:
        user_entry["groups"] = sorted(new_groups)
        return

    groups_seq = user_entry["groups"]
    # Move end-of-sequence comment from the current last item so it stays at the end
    last_idx = len(groups_seq) - 1
    saved_comment = None
    if hasattr(groups_seq, "ca") and last_idx in groups_seq.ca.items:
        saved_comment = groups_seq.ca.items[last_idx]
        del groups_seq.ca.items[last_idx]

    for group in sorted(new_groups):
        groups_seq.append(group)

    # Re-attach end comment to the new last item
    if saved_comment is not None:
        groups_seq.ca.items[len(groups_seq) - 1] = saved_comment


def update_user_groups_in_yaml_files(
    file_paths: list[Path], email: str, groups_to_add: list[str], dry: bool = False
) -> bool:
    """Search existing YAML user files for a user by email and merge groups.

    If the user is found, ensures all groups in `groups_to_add` are present in the user's
    `groups` list. The file is rewritten with comments preserved.

    Args:
        file_paths (list[Path]): List of YAML file paths to search.
        email (str): The email address to search for.
        groups_to_add (list[str]): Groups that should be present for this user.
        dry (bool): If True, do not write changes to disk.

    Returns:
        bool: True if the user was found in any file, False otherwise.
    """
    for file_path in file_paths:
        # Use same YAML instance for load and dump to preserve original formatting
        yml = _get_yaml()
        with open(file_path, encoding="utf-8") as f:
            data = yml.load(f)

        if not isinstance(data, list):
            continue

        for user_entry in data:
            if not isinstance(user_entry, dict):
                continue
            if user_entry.get("email") != email:
                continue

            # User found — merge groups (append new groups at end to keep existing order)
            existing_groups = list(user_entry.get("groups") or [])
            new_groups = [g for g in groups_to_add if g not in existing_groups]

            if new_groups:
                _append_groups_in_place(user_entry, new_groups)
                if dry:
                    logging.info(
                        "[DRY RUN] Would update groups for %s in %s: %s",
                        email,
                        file_path,
                        list(user_entry["groups"]),
                    )
                else:
                    with open(file_path, "w", encoding="utf-8") as f:
                        yml.dump(data, f, transform=_prettify_yaml_formatting)
                    logging.info(
                        "Updated groups for %s in %s: %s",
                        email,
                        file_path,
                        list(user_entry["groups"]),
                    )
            else:
                logging.info("User %s already has all required groups in %s", email, file_path)

            return True

    return False


def append_user_to_yaml_file(file_path: Path, user_dict: dict, dry: bool = False) -> None:
    """Append a new user entry to a YAML file, creating the file if necessary.

    If the file exists, its content (including comments) is preserved and the new user is
    appended to the list.

    Args:
        file_path (Path): Path to the target YAML file.
        user_dict (dict): User dictionary with keys like name, email, groups, and optionally
            username.
        dry (bool): If True, do not write changes to disk.
    """
    # Use same YAML instance for load and dump to preserve original formatting
    yml = _get_yaml()

    if file_path.is_file():
        with open(file_path, encoding="utf-8") as f:
            data = yml.load(f)
        if not isinstance(data, list):
            data = []
    else:
        data = []

    data.append(user_dict)

    if dry:
        logging.info("[DRY RUN] Would append user %s to %s", user_dict.get("email"), file_path)
    else:
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            yml.dump(data, f, transform=_prettify_yaml_formatting)
        logging.info("Appended user %s to %s", user_dict.get("email"), file_path)
