"""Check guest sign-in without contacting a real Supabase project."""

import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from guest_auth import (
    GuestSignInError,
    restore_guest,
    session_credentials,
    sign_in_guest,
)


class GuestSignInTests(unittest.TestCase):
    """Check configuration, separate sessions, and safe failure messages."""

    def setUp(self):
        """Use fake settings and clients for each test."""
        self.environment = patch.dict(
            os.environ,
            {
                "SUPABASE_URL": "https://example.supabase.co",
                "SUPABASE_PUBLISHABLE_KEY": "sb_publishable_test",
            },
            clear=True,
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.factory = patch("guest_auth.create_guest_client")
        self.create_client = self.factory.start()
        self.addCleanup(self.factory.stop)

    @staticmethod
    def guest_client(user_id):
        """Make a fake provider response without real tokens or credentials."""
        client = Mock()
        client.auth.sign_in_anonymously.return_value = SimpleNamespace(
            user=SimpleNamespace(id=user_id), session=object()
        )
        return client

    def test_missing_configuration_does_not_contact_supabase(self):
        """Local play can remain available when sign-in is not configured."""
        for variable in ("SUPABASE_URL", "SUPABASE_PUBLISHABLE_KEY"):
            with self.subTest(variable=variable):
                with patch.dict(os.environ, {variable: ""}):
                    with self.assertRaises(GuestSignInError):
                        sign_in_guest()
        self.create_client.assert_not_called()

    def test_invalid_url_is_rejected_before_connecting(self):
        """Require HTTPS and reject URLs with embedded credentials."""
        for url in (
            "not a URL",
            "https://[invalid",
            "http://example.com",
            "https://user:pass@example.com",
        ):
            with self.subTest(url=url), patch.dict(os.environ, {"SUPABASE_URL": url}):
                with self.assertRaises(GuestSignInError):
                    sign_in_guest()
        self.create_client.assert_not_called()

    def test_secret_or_legacy_key_is_rejected(self):
        """Only publishable keys are used for this guest sign-in step."""
        for key in ("sb_secret_test", "legacy-key"):
            with self.subTest(key=key):
                with patch.dict(os.environ, {"SUPABASE_PUBLISHABLE_KEY": key}):
                    with self.assertRaises(GuestSignInError):
                        sign_in_guest()
        self.create_client.assert_not_called()

    def test_guests_receive_separate_clients_and_identities(self):
        """One player's sign-in must not reuse another player's session."""
        first = self.guest_client("guest-one")
        second = self.guest_client("guest-two")
        self.create_client.side_effect = [first, second]
        self.assertEqual(sign_in_guest(), (first, "guest-one"))
        self.assertEqual(sign_in_guest(), (second, "guest-two"))
        first.auth.sign_in_anonymously.assert_called_once_with()
        second.auth.sign_in_anonymously.assert_called_once_with()

    def test_incomplete_response_is_not_a_success(self):
        """Both a user and session are required before showing success."""
        for user, session in ((None, object()), (SimpleNamespace(id="guest"), None)):
            self.create_client.return_value.auth.sign_in_anonymously.return_value = (
                SimpleNamespace(user=user, session=session)
            )
            with self.assertRaises(GuestSignInError):
                sign_in_guest()

    def test_provider_error_details_are_not_displayed(self):
        """Private provider details must not appear in the page message."""
        self.create_client.return_value.auth.sign_in_anonymously.side_effect = (
            RuntimeError("private provider details")
        )
        with self.assertRaises(GuestSignInError) as caught:
            sign_in_guest()
        self.assertNotIn("private provider details", str(caught.exception))

    def test_restore_verifies_original_identity_without_creating_guest(self):
        """Recovery uses stored tokens and asks the provider for the user."""
        client = self.create_client.return_value
        client.auth.set_session.return_value = SimpleNamespace(session=object())
        client.auth.get_user.return_value = SimpleNamespace(
            user=SimpleNamespace(id="original-guest")
        )
        self.assertEqual(
            restore_guest("access", "refresh"), (client, "original-guest")
        )
        client.auth.set_session.assert_called_once_with("access", "refresh")
        client.auth.get_user.assert_called_once_with()
        client.auth.sign_in_anonymously.assert_not_called()

    def test_restore_missing_tokens_does_not_contact_provider(self):
        """Missing credentials must not silently create a replacement identity."""
        for access, refresh in ((None, "r"), ("a", ""), (" ", "r"), (1, "r")):
            with self.subTest(access=access, refresh=refresh):
                with self.assertRaises(GuestSignInError):
                    restore_guest(access, refresh)
        self.create_client.assert_not_called()

    def test_restore_requires_session_and_verified_user(self):
        """A local token response alone is insufficient proof of identity."""
        client = self.create_client.return_value
        for session, user in ((None, SimpleNamespace(id="guest")), (object(), None)):
            client.auth.set_session.return_value = SimpleNamespace(session=session)
            client.auth.get_user.return_value = SimpleNamespace(user=user)
            with self.subTest(session=session, user=user):
                with self.assertRaises(GuestSignInError):
                    restore_guest("access", "refresh")
        client.auth.sign_in_anonymously.assert_not_called()

    def test_restore_failure_hides_provider_details_and_does_not_sign_in(self):
        """Expired credentials produce a safe error, not a new guest."""
        client = self.create_client.return_value
        client.auth.set_session.side_effect = RuntimeError("private token details")
        with self.assertRaises(GuestSignInError) as caught:
            restore_guest("expired", "invalid")
        self.assertNotIn("private token details", str(caught.exception))
        client.auth.sign_in_anonymously.assert_not_called()

    def test_session_credentials_preserve_refreshed_tokens(self):
        """Storage keeps the latest token pair without copying other provider data."""
        session = SimpleNamespace(
            access_token="new-access", refresh_token="new-refresh", user="private"
        )
        self.assertEqual(
            session_credentials(session),
            {"access_token": "new-access", "refresh_token": "new-refresh"},
        )

    def test_incomplete_recovery_tokens_are_rejected(self):
        """A missing or malformed session must not overwrite saved credentials."""
        for session in (
            None, object(), SimpleNamespace(access_token="", refresh_token="r")
        ):
            with self.subTest(session=session), self.assertRaises(GuestSignInError):
                session_credentials(session)
