"""Sign in a guest without sharing their session with other players."""

import os
from urllib.parse import urlsplit


class GuestSignInError(Exception):
    """A sign-in problem that is safe to show on the page."""


def create_guest_client(url, key):
    """Create a separate client whose session stays in server memory."""
    # pylint: disable=import-outside-toplevel
    from supabase import ClientOptions, create_client

    return create_client(
        url,
        key,
        options=ClientOptions(persist_session=True, auto_refresh_token=False),
    )


def sign_in_guest():
    """Return a new guest's client and ID, or a safe error message."""
    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_PUBLISHABLE_KEY", "").strip()
    if not url or not key:
        raise GuestSignInError("Guest sign-in is not configured. Local play is available.")

    try:
        address = urlsplit(url)
    except ValueError:
        raise GuestSignInError("Check SUPABASE_URL in your local .env file.") from None
    if (
        address.scheme != "https"
        or not address.hostname
        or address.username
        or address.password
        or address.query
        or address.fragment
    ):
        raise GuestSignInError("Check SUPABASE_URL in your local .env file.")
    if not key.startswith("sb_publishable_"):
        raise GuestSignInError("Use a Supabase publishable key, not a secret key.")

    try:
        client = create_guest_client(url, key)
        response = client.auth.sign_in_anonymously()
        if not response.user or not response.session or not response.user.id:
            raise GuestSignInError("Supabase did not return a guest session. Try again.")
        return client, response.user.id
    except GuestSignInError:
        raise
    except Exception:  # pylint: disable=broad-exception-caught
        # Provider errors can contain private data; never display or log them.
        raise GuestSignInError(
            "Guest sign-in failed. Check your connection and Supabase settings."
        ) from None
