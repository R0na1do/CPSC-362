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


def _configured_guest_client():
    """Validate settings before creating an isolated guest client."""
    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_PUBLISHABLE_KEY", "").strip()
    if not url or not key:
        raise GuestSignInError(
            "Guest sign-in is not configured. Local play is available."
        )

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
    return create_guest_client(url, key)


def sign_in_guest():
    """Return a new guest's client and ID, or a safe error message."""
    try:
        client = _configured_guest_client()
        response = client.auth.sign_in_anonymously()
        if not response.user or not response.session or not response.user.id:
            raise GuestSignInError(
                "Supabase did not return a guest session. Try again."
            )
        return client, response.user.id
    except GuestSignInError:
        raise
    except Exception:  # pylint: disable=broad-exception-caught
        # Provider errors can contain private data; never display or log them.
        raise GuestSignInError(
            "Guest sign-in failed. Check your connection and Supabase settings."
        ) from None


def restore_guest(access_token, refresh_token):
    """Restore an existing session and verify its identity with Supabase."""
    if not all(
        isinstance(token, str) and token.strip()
        for token in (access_token, refresh_token)
    ):
        raise GuestSignInError("Both session tokens are required for recovery.")
    try:
        client = _configured_guest_client()
        response = client.auth.set_session(access_token, refresh_token)
        if not response.session:
            raise GuestSignInError("Supabase did not restore a guest session.")
        user = client.auth.get_user().user
        if not user or not user.id:
            raise GuestSignInError("Supabase did not verify the guest identity.")
        return client, user.id
    except GuestSignInError:
        raise
    except Exception:  # pylint: disable=broad-exception-caught
        raise GuestSignInError(
            "Guest session recovery failed. Try again; no new guest was created."
        ) from None


def session_credentials(session):
    """Extract only the tokens needed for private server-side persistence."""
    if session is None or not all(
        isinstance(getattr(session, field, None), str) and getattr(session, field)
        for field in ("access_token", "refresh_token")
    ):
        raise GuestSignInError("Supabase did not return session recovery tokens.")
    return {
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
    }
