from unittest.mock import MagicMock

from auth_user_mgr.main import user_check_existence


def test_existing_user(sample_users):
    user = sample_users[0]
    api = MagicMock()
    mail = MagicMock()

    # Simulate user exists
    api.get_users.return_value = [{"pk": 101}]
    api.get_pending_invitation_uuid_for_email.return_value = "uuid-123"

    exists = user_check_existence(api, user, mail)

    api.delete_invitation.assert_called_once_with("uuid-123")
    assert exists is True

def test_new_user_invited(sample_users):
    user = sample_users[1]
    api = MagicMock()
    mail = MagicMock()

    # Simulate no user and no pending invitation
    api.get_users.return_value = []
    api.get_pending_invitation_url_for_email.return_value = ""
    api.create_invitation.return_value = "https://example.com/invite"

    exists = user_check_existence(api, user, mail)

    mail.send_email.assert_called_once()
    assert exists is False
