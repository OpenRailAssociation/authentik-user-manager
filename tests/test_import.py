# SPDX-FileCopyrightText: 2026 DB Systel GmbH
#
# SPDX-License-Identifier: Apache-2.0

"""Test import functionality: CSV parsing, YAML updating, and CLI integration."""

import textwrap
from pathlib import Path

import pytest

from auth_user_mgr._config import (
    append_user_to_yaml_file,
    parse_csv_users,
    update_user_groups_in_yaml_files,
)

CSV_FIXTURE = "tests/data/users.import.csv"


# --- Tests for parse_csv_users ---


class TestParseCsvUsers:
    """Tests for parse_csv_users function."""

    def test_valid_csv(self) -> None:
        """Test parsing a valid CSV file with expected columns."""
        users = parse_csv_users(CSV_FIXTURE)
        assert len(users) == 3
        assert users[0] == {"name": "Tester Testerson", "email": "tester@example.com"}
        assert users[1] == {"name": "Jane Doe", "email": "jane@example.com"}
        assert users[2] == {
            "name": "Bob Smith",
            "email": "bob@example.org",
            "username": "bob.custom",
        }

    def test_file_not_found(self) -> None:
        """Test that a missing CSV file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            parse_csv_users("non_existent.csv")

    def test_missing_required_column(self, tmp_path: Path) -> None:
        """Test that a CSV missing the 'email' column raises ValueError."""
        csv_file = tmp_path / "bad.csv"
        csv_file.write_text("name, username\nJohn, john\n")
        with pytest.raises(ValueError, match="email"):
            parse_csv_users(str(csv_file))

    def test_missing_name_column(self, tmp_path: Path) -> None:
        """Test that a CSV missing the 'name' column raises ValueError."""
        csv_file = tmp_path / "bad.csv"
        csv_file.write_text("email, username\njohn@x.com, john\n")
        with pytest.raises(ValueError, match="name"):
            parse_csv_users(str(csv_file))

    def test_skips_empty_rows(self, tmp_path: Path) -> None:
        """Test that rows with empty name or email are skipped."""
        csv_file = tmp_path / "partial.csv"
        csv_file.write_text("name, email\nJane, jane@x.com\n, missing@x.com\nNoEmail,\n")
        users = parse_csv_users(str(csv_file))
        assert len(users) == 1
        assert users[0]["email"] == "jane@x.com"

    def test_invalid_email_format(self, tmp_path: Path) -> None:
        """Test that an invalid email format raises ValueError via schema validation."""
        csv_file = tmp_path / "bad_email.csv"
        csv_file.write_text("name, email\nAlice, not-an-email\n")
        with pytest.raises(ValueError):
            parse_csv_users(str(csv_file))

    def test_whitespace_stripping(self, tmp_path: Path) -> None:
        """Test that whitespace is stripped from all fields."""
        csv_file = tmp_path / "spaces.csv"
        csv_file.write_text("name , email , username\n  Alice ,  alice@x.com ,  alice123  \n")
        users = parse_csv_users(str(csv_file))
        assert users[0] == {"name": "Alice", "email": "alice@x.com", "username": "alice123"}

    def test_username_omitted_when_empty(self, tmp_path: Path) -> None:
        """Test that the username key is not included when the field is empty."""
        csv_file = tmp_path / "no_user.csv"
        csv_file.write_text("name, email, username\nAlice, alice@x.com,\n")
        users = parse_csv_users(str(csv_file))
        assert "username" not in users[0]


# --- Tests for update_user_groups_in_yaml_files ---


class TestUpdateUserGroupsInYamlFiles:
    """Tests for update_user_groups_in_yaml_files function."""

    def _write_yaml(self, path: Path, content: str) -> None:
        path.write_text(textwrap.dedent(content))

    def test_user_found_groups_merged(self, tmp_path: Path) -> None:
        """Test that new groups are merged into an existing user's groups list."""
        yaml_file = tmp_path / "users.yaml"
        self._write_yaml(
            yaml_file,
            """\
            # My users
            - name: Alice
              email: alice@example.com
              groups:
                - Group 1
            """,
        )

        result = update_user_groups_in_yaml_files(
            file_paths=[yaml_file],
            email="alice@example.com",
            groups_to_add=["Group 2", "Group 3"],
        )

        assert result is True
        content = yaml_file.read_text()
        assert "Group 1" in content
        assert "Group 2" in content
        assert "Group 3" in content
        # Comment should be preserved
        assert "# My users" in content

    def test_user_found_already_has_groups(self, tmp_path: Path) -> None:
        """Test idempotency: no changes when user already has all groups."""
        yaml_file = tmp_path / "users.yaml"
        self._write_yaml(
            yaml_file,
            """\
            - name: Alice
              email: alice@example.com
              groups:
                - Group 1
                - Group 2
            """,
        )
        original_content = yaml_file.read_text()

        result = update_user_groups_in_yaml_files(
            file_paths=[yaml_file],
            email="alice@example.com",
            groups_to_add=["Group 1", "Group 2"],
        )

        assert result is True
        # File should not have been rewritten (content unchanged)
        assert yaml_file.read_text() == original_content

    def test_user_found_no_groups_key(self, tmp_path: Path) -> None:
        """Test that groups key is created if user has no groups attribute."""
        yaml_file = tmp_path / "users.yaml"
        self._write_yaml(
            yaml_file,
            """\
            - name: Alice
              email: alice@example.com
            """,
        )

        result = update_user_groups_in_yaml_files(
            file_paths=[yaml_file],
            email="alice@example.com",
            groups_to_add=["Group 1"],
        )

        assert result is True
        content = yaml_file.read_text()
        assert "Group 1" in content

    def test_user_not_found(self, tmp_path: Path) -> None:
        """Test that False is returned when user is not in any file."""
        yaml_file = tmp_path / "users.yaml"
        self._write_yaml(
            yaml_file,
            """\
            - name: Alice
              email: alice@example.com
              groups:
                - Group 1
            """,
        )

        result = update_user_groups_in_yaml_files(
            file_paths=[yaml_file],
            email="bob@example.com",
            groups_to_add=["Group 2"],
        )

        assert result is False

    def test_dry_run_does_not_write(self, tmp_path: Path) -> None:
        """Test that dry run does not modify the file."""
        yaml_file = tmp_path / "users.yaml"
        self._write_yaml(
            yaml_file,
            """\
            - name: Alice
              email: alice@example.com
              groups:
                - Group 1
            """,
        )
        original_content = yaml_file.read_text()

        result = update_user_groups_in_yaml_files(
            file_paths=[yaml_file],
            email="alice@example.com",
            groups_to_add=["Group 2"],
            dry=True,
        )

        assert result is True
        assert yaml_file.read_text() == original_content

    def test_new_groups_appended_at_end(self, tmp_path: Path) -> None:
        """Test that new groups are appended at end, preserving existing order."""
        yaml_file = tmp_path / "users.yaml"
        self._write_yaml(
            yaml_file,
            """\
            - name: Alice
              email: alice@example.com
              groups:
                - Zebra Club
                - Alpha Team
                - Middle Group
            """,
        )

        result = update_user_groups_in_yaml_files(
            file_paths=[yaml_file],
            email="alice@example.com",
            groups_to_add=["Beta Squad", "Alpha Team"],
        )

        assert result is True
        from auth_user_mgr._config import load_yaml_file  # noqa: PLC0415

        data = load_yaml_file(yaml_file)
        groups = list(data[0]["groups"])
        # Existing groups stay in original order, new ones appended at end
        assert groups == [
            "Zebra Club",
            "Alpha Team",
            "Middle Group",
            "Beta Squad",
        ]

    def test_yaml_formatting_after_update(self, tmp_path: Path) -> None:
        """Test that YAML formatting is correct after group update."""
        yaml_file = tmp_path / "users.yaml"
        yaml_file.write_text(
            "# Comment\n"
            "- name: Alice\n"
            "  email: alice@example.com\n"
            "  groups:\n"
            "    - Group 1\n"
            "\n"
            "- name: Bob\n"
            "  email: bob@example.com\n"
            "  groups:\n"
            "    - Group 1\n"
        )

        update_user_groups_in_yaml_files(
            file_paths=[yaml_file],
            email="alice@example.com",
            groups_to_add=["Group 2"],
        )

        content = yaml_file.read_text()
        # Verify correct indentation (2 spaces for keys, 4 for groups)
        assert "  email: alice@example.com\n" in content
        assert "    - Group 1\n" in content
        assert "    - Group 2\n" in content
        # Verify blank line separator between entries is preserved
        assert "\n\n- name: Bob\n" in content
        # Verify comment is preserved
        assert content.startswith("# Comment\n")

    def test_comment_between_entries_preserved(self, tmp_path: Path) -> None:
        """Test that a section comment between entries is preserved after updating groups."""
        yaml_file = tmp_path / "users.yaml"
        yaml_file.write_text(
            "- name: Alice\n"
            "  email: alice@example.com\n"
            "  groups:\n"
            "    - Group 1\n"
            "\n"
            "# Section Two\n"
            "- name: Bob\n"
            "  email: bob@example.com\n"
            "  groups:\n"
            "    - Group 1\n"
        )

        update_user_groups_in_yaml_files(
            file_paths=[yaml_file],
            email="alice@example.com",
            groups_to_add=["Group 2"],
        )

        content = yaml_file.read_text()
        assert "# Section Two\n" in content

    def test_searches_multiple_files(self, tmp_path: Path) -> None:
        """Test that multiple files are searched and the correct one is updated."""
        file1 = tmp_path / "group1.yaml"
        file2 = tmp_path / "group2.yaml"
        self._write_yaml(
            file1,
            """\
            - name: Alice
              email: alice@example.com
              groups:
                - Group 1
            """,
        )
        self._write_yaml(
            file2,
            """\
            - name: Bob
              email: bob@example.com
              groups:
                - Group 2
            """,
        )

        result = update_user_groups_in_yaml_files(
            file_paths=[file1, file2],
            email="bob@example.com",
            groups_to_add=["Group 3"],
        )

        assert result is True
        assert "Group 3" in file2.read_text()
        # file1 should be unchanged
        assert "Group 3" not in file1.read_text()


# --- Tests for append_user_to_yaml_file ---


class TestAppendUserToYamlFile:
    """Tests for append_user_to_yaml_file function."""

    def test_create_new_file(self, tmp_path: Path) -> None:
        """Test creating a new YAML file with one user."""
        yaml_file = tmp_path / "new_users.yaml"
        user_dict = {"name": "Bob", "email": "bob@example.com", "groups": ["Event"]}

        append_user_to_yaml_file(file_path=yaml_file, user_dict=user_dict)

        assert yaml_file.exists()
        content = yaml_file.read_text()
        assert "bob@example.com" in content
        assert "Event" in content

    def test_append_to_existing_file(self, tmp_path: Path) -> None:
        """Test appending a user to an existing YAML file preserving comments."""
        yaml_file = tmp_path / "users.yaml"
        yaml_file.write_text(
            "# Event participants\n- name: Alice\n  email: alice@example.com\n  groups:\n"
            "    - Event\n"
        )

        user_dict = {"name": "Bob", "email": "bob@example.com", "groups": ["Event"]}
        append_user_to_yaml_file(file_path=yaml_file, user_dict=user_dict)

        content = yaml_file.read_text()
        assert "# Event participants" in content
        assert "alice@example.com" in content
        assert "bob@example.com" in content

    def test_dry_run_does_not_create_file(self, tmp_path: Path) -> None:
        """Test that dry run does not create the file."""
        yaml_file = tmp_path / "new_users.yaml"
        user_dict = {"name": "Bob", "email": "bob@example.com", "groups": ["Event"]}

        append_user_to_yaml_file(file_path=yaml_file, user_dict=user_dict, dry=True)

        assert not yaml_file.exists()

    def test_dry_run_does_not_modify_existing(self, tmp_path: Path) -> None:
        """Test that dry run does not modify an existing file."""
        yaml_file = tmp_path / "users.yaml"
        yaml_file.write_text("- name: Alice\n  email: alice@example.com\n")
        original = yaml_file.read_text()

        user_dict = {"name": "Bob", "email": "bob@example.com", "groups": ["Event"]}
        append_user_to_yaml_file(file_path=yaml_file, user_dict=user_dict, dry=True)

        assert yaml_file.read_text() == original

    def test_with_username(self, tmp_path: Path) -> None:
        """Test that username is included in output when provided."""
        yaml_file = tmp_path / "new_users.yaml"
        user_dict = {
            "name": "Bob Smith",
            "email": "bob@example.com",
            "username": "bob.custom",
            "groups": ["Event"],
        }

        append_user_to_yaml_file(file_path=yaml_file, user_dict=user_dict)

        content = yaml_file.read_text()
        assert "bob.custom" in content

    def test_yaml_formatting_on_append(self, tmp_path: Path) -> None:
        """Test that appended users produce correct YAML formatting."""
        yaml_file = tmp_path / "users.yaml"
        user1 = {"name": "Alice", "email": "alice@example.com", "groups": ["Event", "Board"]}
        user2 = {"name": "Bob", "email": "bob@example.com", "groups": ["Event"]}

        append_user_to_yaml_file(file_path=yaml_file, user_dict=user1)
        append_user_to_yaml_file(file_path=yaml_file, user_dict=user2)

        content = yaml_file.read_text()
        # No leading indentation at root level
        assert content.startswith("- name: Alice\n")
        # Keys indented 2 spaces
        assert "  email: alice@example.com\n" in content
        # Groups indented 4 spaces
        assert "    - Event\n" in content
        assert "    - Board\n" in content
        # Blank line between entries
        assert "\n\n- name: Bob\n" in content


# --- Integration test for run_import ---


class TestRunImport:
    """Integration tests for the full import workflow."""

    def test_full_import_new_and_existing(self, tmp_path: Path) -> None:
        """Test importing where one user exists and one is new."""
        # Setup existing user file
        existing_file = tmp_path / "existing.yaml"
        existing_file.write_text(
            "# Existing users\n"
            "- name: Tester Testerson\n"
            "  email: tester@example.com\n"
            "  groups:\n"
            "    - Old Group\n"
        )

        # Setup CSV
        csv_file = tmp_path / "import.csv"
        csv_file.write_text(
            "name, email, username\nTester Testerson, tester@example.com,\n"
            "New User, new@example.com,\n"
        )

        output_file = tmp_path / "output.yaml"

        # Run import logic directly
        from auth_user_mgr._config import (  # noqa: PLC0415
            append_user_to_yaml_file,
            parse_csv_users,
            update_user_groups_in_yaml_files,
        )

        csv_users = parse_csv_users(str(csv_file))
        groups = ["Group A", "Group B"]
        existing_file_paths = [existing_file]

        for csv_user in csv_users:
            email = csv_user["email"]
            if not update_user_groups_in_yaml_files(
                file_paths=existing_file_paths, email=email, groups_to_add=groups
            ):
                user_dict = {"name": csv_user["name"], "email": email, "groups": sorted(groups)}
                append_user_to_yaml_file(file_path=output_file, user_dict=user_dict)

        # Verify existing user got updated
        existing_content = existing_file.read_text()
        assert "# Existing users" in existing_content  # comment preserved
        assert "Old Group" in existing_content
        assert "Group A" in existing_content
        assert "Group B" in existing_content

        # Verify new user was written to output
        assert output_file.exists()
        output_content = output_file.read_text()
        assert "new@example.com" in output_content
        assert "Group A" in output_content
        assert "Group B" in output_content
        # Existing user should NOT be in output file
        assert "tester@example.com" not in output_content
