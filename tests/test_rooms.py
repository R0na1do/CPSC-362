"""Test room requests without signing in or writing to Supabase."""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from rooms import (
    RoomError,
    create_room,
    get_room,
    join_room,
    leave_room,
    move_room,
    normalize_code,
    ready_room,
    rematch_room,
    validate_name,
)


class RoomTests(unittest.TestCase):
    """Check code validation, request identity, and safe errors."""

    def setUp(self):
        """Use a fake signed-in client and a room response."""
        self.client = Mock()
        self.room = {"id": "test-game", "room_code": "AB12CD34"}
        self.client.rpc.return_value.execute.return_value.data = self.room

    def test_normalize_code(self):
        """New numeric codes retain zeros; older rooms remain accessible."""
        self.assertEqual(normalize_code("  12345  "), "12345")
        self.assertEqual(normalize_code("00123"), "00123")
        self.assertEqual(normalize_code("  ab12cd34  "), "AB12CD34")

    def test_invalid_code_does_not_contact_supabase(self):
        """Reject missing codes, invalid characters, and incorrect lengths."""
        for code in (
            None, "", "1234", "123456", "12A45", "１２３４５",
            "ABC", "GG12CD34", "AB12CD345", "';drop table",
        ):
            with self.subTest(code=code), self.assertRaises(RoomError):
                join_room(self.client, code)
        self.client.rpc.assert_not_called()

    def test_join_preserves_five_digits_and_leading_zeroes(self):
        """Room codes stay strings so a phone's numeric keyboard does not lose zeros."""
        self.client.rpc.return_value.execute.return_value.data = {"room_code": "00123"}
        self.assertEqual(join_room(self.client, " 00123 ")["room_code"], "00123")
        self.client.rpc.assert_called_once_with(
            "gg_join_room", {"p_code": "00123", "p_name": "Player O"}
        )

    def test_sign_in_is_required(self):
        """Unsigned clients cannot request rooms."""
        with self.assertRaises(RoomError):
            create_room(None)
        self.client.auth.get_session.return_value = None
        with self.assertRaises(RoomError):
            create_room(self.client)
        self.client.rpc.assert_not_called()

    def test_create_does_not_send_player_identity(self):
        """The database obtains identity from the authenticated session."""
        self.assertEqual(create_room(self.client), self.room)
        self.client.rpc.assert_called_once_with(
            "gg_create_room", {"p_name": "Player X"}
        )
        self.client.auth.get_session.assert_called_once_with()

    def test_join_sends_only_normalized_code(self):
        """The browser cannot choose which player seat to claim."""
        self.assertEqual(join_room(self.client, "ab12cd34"), self.room)
        self.client.rpc.assert_called_once_with(
            "gg_join_room", {"p_code": "AB12CD34", "p_name": "Player O"}
        )

    def test_refresh_uses_participant_read_function(self):
        """Refresh does not download every game to search in Python."""
        self.assertEqual(get_room(self.client, "AB12CD34"), self.room)
        self.client.rpc.assert_called_once_with("gg_get_room", {"p_code": "AB12CD34"})

    def test_names_are_trimmed_and_validated(self):
        """Only short, nonempty display names are sent to the database."""
        self.assertEqual(validate_name(" Alice "), "Alice")
        for name in (None, "", "  ", "x" * 21):
            with self.subTest(name=name), self.assertRaises(RoomError):
                create_room(self.client, name)
        self.client.rpc.assert_not_called()

    def test_ready_request_does_not_supply_identity(self):
        """Only the signed-in user's readiness can be changed."""
        ready_room(self.client, "AB12CD34")
        self.client.rpc.assert_called_once_with("gg_ready_room", {"p_code": "AB12CD34"})

    def test_moves_send_only_cell_version_and_request_id(self):
        """The caller cannot supply a new board or winner."""
        request = "00000000-0000-0000-0000-000000000001"
        move_room(self.client, "ab12cd34", 4, 2, request)
        self.client.rpc.assert_called_once_with(
            "gg_make_move",
            {
                "p_code": "AB12CD34",
                "p_cell": 4,
                "p_version": 2,
                "p_request": request,
            },
        )

    def test_invalid_move_arguments_do_not_contact_supabase(self):
        """Reject invalid cells, versions, and request IDs before sending."""
        for cell in (-1, 9, True, None, "1"):
            with self.subTest(cell=cell), self.assertRaises(RoomError):
                move_room(self.client, "AB12CD34", cell, 2)
        for version in (-1, True, "2"):
            with self.subTest(version=version), self.assertRaises(RoomError):
                move_room(self.client, "AB12CD34", 1, version)
        with self.assertRaises(RoomError):
            move_room(self.client, "AB12CD34", 1, 2, "invalid")
        self.client.rpc.assert_not_called()

    def test_rematch_and_leave_include_round_number(self):
        """An old request must not alter a later round."""
        rematch_room(self.client, "AB12CD34", 3)
        self.client.rpc.assert_called_with(
            "gg_rematch",
            {
                "p_code": "AB12CD34",
                "p_round": 3,
            },
        )
        leave_room(self.client, "AB12CD34", 3)
        self.client.rpc.assert_called_with(
            "gg_leave_room",
            {
                "p_code": "AB12CD34",
                "p_round": 3,
            },
        )

    def test_incomplete_response_is_rejected(self):
        """A missing response is not displayed as a successful room."""
        for data in (None, [], {}):
            self.client.rpc.return_value.execute.return_value = SimpleNamespace(
                data=data
            )
            with self.assertRaises(RoomError):
                create_room(self.client)

    def test_provider_details_are_hidden(self):
        """Unexpected server errors must not expose private data."""
        self.client.rpc.side_effect = RuntimeError("private database details")
        with self.assertRaises(RoomError) as caught:
            create_room(self.client)
        self.assertNotIn("private database details", str(caught.exception))

    def test_full_room_and_missing_setup_have_clear_messages(self):
        """Known server errors explain the next action without a traceback."""
        for code, message, expected in (
            ("P0001", "ROOM_FULL", "two players"),
            ("PGRST202", "private database details", "not applied"),
        ):
            error = RuntimeError()
            error.code = code
            error.message = message
            self.client.rpc.side_effect = error
            with self.assertRaises(RoomError) as caught:
                create_room(self.client)
            self.assertIn(expected, str(caught.exception))
