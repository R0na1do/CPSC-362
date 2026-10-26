"""Supabase room requests for the signed-in player."""

import re
from uuid import UUID, uuid4


class RoomError(Exception):
    """A room error that is safe to show on the page."""


ERROR_MESSAGES = {
    "SIGN_IN_REQUIRED": "Sign in as a guest first.",
    "INVALID_ROOM_CODE": "Enter the five-digit room code.",
    "ROOM_NOT_FOUND": "Room not found or not available to this player.",
    "ROOM_NOT_WAITING": "That room is no longer waiting for players.",
    "ROOM_FULL": "That room already has two players.",
    "ROOM_CODE_BUSY": "Could not create a room code. Try again.",
    "INVALID_NAME": "Enter a name with 1 to 20 characters.",
    "WAIT_FOR_OPPONENT": "Wait for a second player to join.",
    "GAME_NOT_ACTIVE": "This round is not in progress.",
    "NOT_YOUR_TURN": "Wait for your turn.",
    "CELL_OCCUPIED": "That square is already occupied.",
    "INVALID_CELL": "Choose a valid square.",
    "STALE_ROOM": "The room changed. Refresh before trying again.",
    "INVALID_REQUEST": "The move could not be sent. Try again.",
}


def normalize_code(code):
    """Accept five-digit codes and preserve access to older eight-character rooms."""
    if not isinstance(code, str):
        raise RoomError(ERROR_MESSAGES["INVALID_ROOM_CODE"])
    code = code.strip().upper()
    if not re.fullmatch(r"(?:[0-9]{5}|[0-9A-F]{8})", code):
        raise RoomError(ERROR_MESSAGES["INVALID_ROOM_CODE"])
    return code


def _call_room(client, function, parameters):
    """Refresh the session if needed, then ask Supabase to change or read a room."""
    if client is None:
        raise RoomError(ERROR_MESSAGES["SIGN_IN_REQUIRED"])
    try:
        if client.auth.get_session() is None:
            raise RoomError("Your session ended. Refresh and sign in again.")
        room = client.rpc(function, parameters).execute().data
        if not isinstance(room, dict) or not room.get("room_code"):
            raise RoomError("Supabase did not return a room. Try Refresh Room.")
        return room
    except RoomError:
        raise
    except Exception as error:  # pylint: disable=broad-exception-caught
        if getattr(error, "code", None) == "PGRST202":
            message = "Room database setup is not applied yet. Local play still works."
        else:
            message = ERROR_MESSAGES.get(
                getattr(error, "message", ""),
                "Room request failed. Check your connection and sign-in.",
            )
        raise RoomError(message) from None


def validate_name(name):
    """Keep display names short and nonempty."""
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 20:
        raise RoomError(ERROR_MESSAGES["INVALID_NAME"])
    return name.strip()


def create_room(client, name="Player X"):
    """Create a Classic lobby, or return the host's existing waiting lobby."""
    return _call_room(client, "gg_create_room", {"p_name": validate_name(name)})


def join_room(client, code, name="Player O"):
    """Claim the second seat through the database's atomic join function."""
    return _call_room(
        client,
        "gg_join_room",
        {
            "p_code": normalize_code(code),
            "p_name": validate_name(name),
        },
    )


def get_room(client, code):
    """Read a room only when the signed-in player occupies one of its seats."""
    return _call_room(client, "gg_get_room", {"p_code": normalize_code(code)})


def ready_room(client, code):
    """Confirm this player's readiness; the database starts when both agree."""
    return _call_room(client, "gg_ready_room", {"p_code": normalize_code(code)})


def move_room(client, code, cell, version, request_id=None):
    """Send a square and version, never a browser-calculated board or result."""
    if not isinstance(cell, int) or isinstance(cell, bool) or not 0 <= cell <= 8:
        raise RoomError(ERROR_MESSAGES["INVALID_CELL"])
    if not isinstance(version, int) or isinstance(version, bool) or version < 0:
        raise RoomError(ERROR_MESSAGES["STALE_ROOM"])
    try:
        request_id = str(UUID(str(request_id))) if request_id else str(uuid4())
    except ValueError:
        raise RoomError(ERROR_MESSAGES["INVALID_REQUEST"]) from None
    return _call_room(
        client,
        "gg_make_move",
        {
            "p_code": normalize_code(code),
            "p_cell": cell,
            "p_version": version,
            "p_request": request_id,
        },
    )


def rematch_room(client, code, round_no):
    """Request another round with the starter switched after both agree."""
    return _call_room(
        client,
        "gg_rematch",
        {
            "p_code": normalize_code(code),
            "p_round": round_no,
        },
    )


def leave_room(client, code, round_no):
    """Close a waiting host's room, release O, or forfeit an active round."""
    return _call_room(
        client,
        "gg_leave_room",
        {
            "p_code": normalize_code(code),
            "p_round": round_no,
        },
    )
