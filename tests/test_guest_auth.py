"""Check guest sign-in without contacting a real Supabase project."""

import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from guest_auth import GuestSignInError, sign_in_guest


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
