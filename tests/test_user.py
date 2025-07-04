"""Test _user.py"""

from auth_user_mgr._user import User


def test_user_initialization_and_properties():
    """Test the initialization and properties of the User class"""
    user = User(name="Jane Doe", email="jane@example.com", configured_groups=["B", "A"])

    assert user.name == "Jane Doe"
    assert user.email == "jane@example.com"
    assert user.configured_groups == ["A", "B"]  # groups are sorted
    assert user.username == "jane.doe"
    assert user.invite_slug == "invite-jane-doe"
    assert len(user.invite_slug) <= 50


def test_user_with_special_characters():
    """Test user with special characters in the name"""
    user = User(name="Mårten Östlund", email="marten@example.com", configured_groups=["X"])
    assert user.username == "marten.ostlund"
    assert user.invite_slug.startswith("invite-marten-ostlund")


def test_user_with_multiple_spaces():
    """Test user with multiple spaces in the name"""
    user = User(name="  Alice    Bob   ", email="alice@example.com", configured_groups=["G"])
    assert user.username == "alice.bob"
    assert user.invite_slug.startswith("invite-alice-bob")


def test_user_with_hyphens_and_underscores():
    """Test user with hyphens in the name"""
    user = User(name="John-William Doe-Testerson", email="jd@example.com", configured_groups=[])
    assert user.username == "john-william.doe-testerson"
    assert user.invite_slug.startswith("invite-john-william-doe-testerson")


def test_user_with_very_long_name():
    """Test user with a very long name to ensure invite_slug is truncated correctly"""
    long_name = "Firstname Middlename Verylonglastname With Extra Suffix and more " + "a" * 100
    user = User(name=long_name, email="long@example.com", configured_groups=[])
    assert len(user.invite_slug) <= 50
    assert len(user.username) <= 150
    assert user.invite_slug.startswith("invite-firstname")
