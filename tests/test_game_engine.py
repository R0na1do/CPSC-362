"""Check Classic rules without starting the web application."""

import unittest

from game_engine import BlitzGame, ClassicGame

# These tests inspect internal snapshots to verify rejection and repetition rules.
# pylint: disable=protected-access


class ClassicGameTests(unittest.TestCase):
    """Verify Classic rules and rejected-move state preservation."""

    def setUp(self):
        """Give every test a fresh, independent game."""
        self.game = ClassicGame()

    def play(self, cells):
        """Play a sequence of legal moves, failing if one is rejected."""
        for cell in cells:
            accepted, message = self.game.make_move(cell)
            self.assertTrue(accepted, message)

    def assert_fresh_game(self):
        """Check every state field after a round is reset."""
        self.assertEqual(self.game.board, [""] * 9)
        self.assertEqual(self.game.current_player, "X")
        self.assertIsNone(self.game.winner)
        self.assertFalse(self.game.is_draw)
        self.assertFalse(self.game.finished)

    def assert_rejected_without_changes(self, cell):
        """Rejected moves must explain why and preserve all game state."""
        before = (
            self.game.board.copy(),
            self.game.current_player,
            self.game.winner,
            self.game.is_draw,
            self.game.finished,
        )
        accepted, message = self.game.make_move(cell)
        self.assertFalse(accepted)
        self.assertIsInstance(message, str)
        self.assertTrue(message.strip())
        after = (
            self.game.board,
            self.game.current_player,
            self.game.winner,
            self.game.is_draw,
            self.game.finished,
        )
        self.assertEqual(after, before)

    def test_new_game(self):
        """A new game should begin with a clean board and X to move."""
        self.assert_fresh_game()

    def test_valid_moves_alternate_players(self):
        """Accepted moves should place marks and alternate turns."""
        self.play([0])
        self.assertEqual(self.game.board, ["X"] + [""] * 8)
        self.assertEqual(self.game.current_player, "O")
        self.play([4])
        self.assertEqual(self.game.board, ["X", "", "", "", "O", "", "", "", ""])
        self.assertEqual(self.game.current_player, "X")
        self.assertFalse(self.game.finished)
        self.assertIsNone(self.game.winner)
        self.assertFalse(self.game.is_draw)

    def test_invalid_cell_inputs_leave_state_unchanged(self):
        """Out-of-range or non-integer cells should be rejected."""
        self.play([4])
        for cell in (-1, 9, 100, "0", 1.0, None, True, False, [], {}):
            with self.subTest(cell=cell):
                self.assert_rejected_without_changes(cell)

    def test_occupied_cell_leaves_state_unchanged(self):
        """A player cannot replace a mark already on the board."""
        self.play([0])
        self.assert_rejected_without_changes(0)

    def test_all_eight_winning_lines_for_both_players(self):
        """Each player should win through every row, column, and diagonal."""
        rows = [tuple(row * 3 + column for column in range(3)) for row in range(3)]
        columns = [tuple(row * 3 + column for row in range(3)) for column in range(3)]
        lines = rows + columns + [(0, 4, 8), (2, 4, 6)]
        for line in lines:
            others = [cell for cell in range(9) if cell not in line]
            for player in ("X", "O"):
                with self.subTest(line=line, player=player):
                    self.game.reset()
                    if player == "X":
                        moves = [line[0], others[0], line[1], others[1], line[2]]
                    else:
                        moves = [
                            others[0],
                            line[0],
                            others[1],
                            line[1],
                            others[-1],
                            line[2],
                        ]
                    self.play(moves[:-1])
                    self.assertFalse(self.game.finished)
                    self.assertIsNone(self.game.winner)
                    self.play(moves[-1:])
                    self.assertEqual(self.game.winner, player)
                    self.assertTrue(self.game.finished)
                    self.assertFalse(self.game.is_draw)

    def test_full_board_without_winner_is_draw(self):
        """A full board without a winning line should end in a draw."""
        self.play([0, 1, 2, 4, 3, 5, 7, 6])
        self.assertFalse(self.game.finished)
        self.assertFalse(self.game.is_draw)
        self.play([8])
        self.assertTrue(self.game.is_draw)
        self.assertTrue(self.game.finished)
        self.assertIsNone(self.game.winner)

    def test_ninth_move_win_takes_priority_over_draw(self):
        """A win on the last square should take priority over a draw."""
        self.play([0, 1, 2, 4, 3, 5, 7, 8])
        self.assertFalse(self.game.finished)
        self.play([6])
        self.assertEqual(self.game.winner, "X")
        self.assertTrue(self.game.finished)
        self.assertFalse(self.game.is_draw)

    def test_moves_after_win_are_rejected(self):
        """No further move should change state after a player wins."""
        self.play([0, 3, 1, 4, 2])
        for cell in (8, 0):
            with self.subTest(cell=cell):
                self.assert_rejected_without_changes(cell)

    def test_move_after_draw_is_rejected(self):
        """No further move should change state after a draw."""
        self.play([0, 1, 2, 4, 3, 5, 7, 6, 8])
        self.assert_rejected_without_changes(0)

    def test_reset_during_play_after_win_and_after_draw(self):
        """Reset should restore a playable round from each terminal state."""
        for moves in ([4], [0, 3, 1, 4, 2], [0, 1, 2, 4, 3, 5, 7, 6, 8]):
            with self.subTest(moves=moves):
                self.play(moves)
                self.game.reset()
                self.assert_fresh_game()
                self.play([0])
                self.assertEqual(self.game.board[0], "X")
                self.game.reset()

    def test_game_instances_do_not_share_state(self):
        """Separate game objects should keep independent boards and turns."""
        other_game = ClassicGame()
        self.play([0])
        self.assertEqual(other_game.board, [""] * 9)
        self.assertEqual(other_game.current_player, "X")
        self.assertFalse(other_game.finished)


class BlitzGameTests(unittest.TestCase):
    """Verify Blitz piece rotation, wins, draws, and invalid moves."""

    def setUp(self):
        """Give each test an independent Blitz round."""
        self.game = BlitzGame()

    def play(self, cells):
        """Play legal placements and fail immediately if one is rejected."""
        for cell in cells:
            accepted, message = self.game.make_move(cell)
            self.assertTrue(accepted, message)

    def test_new_game_has_empty_piece_queues(self):
        """A new round starts with X, no active marks, and one initial state."""
        self.assertEqual(self.game.board, [""] * 9)
        self.assertEqual(self.game.current_player, "X")
        self.assertEqual(self.game.piece_order, {"X": [], "O": []})
        self.assertEqual(self.game.oldest_cells, set())
        self.assertEqual(self.game.action_count, 0)
        self.assertEqual(list(self.game._state_occurrences.values()), [1])

    def test_each_player_keeps_only_three_active_pieces(self):
        """Each fourth placement removes only that player's oldest mark."""
        self.play([0, 1, 2, 3, 4, 5, 6])
        self.assertEqual(self.game.piece_order["X"], [2, 4, 6])
        self.assertEqual(self.game.piece_order["O"], [1, 3, 5])
        self.assertEqual(self.game.board[0], "")
        self.assertEqual(self.game.board[1], "O")
        self.assertEqual(self.game.board[2], "X")
        self.assertEqual(self.game.oldest_cells, {1, 2})

    def test_occupied_oldest_piece_cannot_be_selected(self):
        """Selecting an oldest mark is rejected without changing game state."""
        self.play([0, 1, 2, 3, 4, 5])
        before = (
            self.game.board.copy(),
            self.game.current_player,
            {player: queue.copy() for player, queue in self.game.piece_order.items()},
            self.game.action_count,
            self.game._state_occurrences.copy(),
        )

        accepted, message = self.game.make_move(0)

        self.assertFalse(accepted)
        self.assertIn("occupied", message)
        self.assertEqual(
            (
                self.game.board,
                self.game.current_player,
                self.game.piece_order,
                self.game.action_count,
                self.game._state_occurrences,
            ),
            before,
        )

    def test_fourth_placement_can_win_after_oldest_piece_is_removed(self):
        """Check wins on the post-rotation board, before ending by draw limits."""
        self.play([8, 3, 0, 4, 1, 6])
        self.game.action_count = self.game.MAX_ACTIONS - 1
        self.play([2])
        self.assertEqual(self.game.board[8], "")
        self.assertEqual(self.game.board[:3], ["X", "X", "X"])
        self.assertEqual(self.game.winner, "X")
        self.assertEqual(self.game.action_count, 100)
        self.assertTrue(self.game.finished)
        self.assertFalse(self.game.is_draw)

    def test_finished_game_rejects_additional_placements(self):
        """A winner ends the round and later moves do not change state."""
        self.play([8, 3, 0, 4, 1, 6, 2])
        before = (
            self.game.board.copy(),
            self.game.action_count,
            self.game.current_player,
        )
        accepted, _ = self.game.make_move(6)
        self.assertFalse(accepted)
        self.assertEqual(
            (self.game.board, self.game.action_count, self.game.current_player), before
        )

    def test_third_occurrence_of_full_state_is_a_draw(self):
        """Repetition tracking includes the board, next player, and queue order."""
        expected = BlitzGame()
        expected.make_move(0)
        self.game._state_occurrences[expected._state_key()] = 2

        accepted, message = self.game.make_move(0)

        self.assertTrue(accepted)
        self.assertIn("repetition", message)
        self.assertTrue(self.game.is_draw)
        self.assertEqual(self.game.draw_reason, "repetition")
        self.assertTrue(self.game.finished)

    def test_action_limit_ends_nonwinning_round_at_100(self):
        """The 100th action draws unless that action already won."""
        self.game.action_count = self.game.MAX_ACTIONS - 1
        accepted, message = self.game.make_move(0)
        self.assertTrue(accepted)
        self.assertIn("100 actions", message)
        self.assertEqual(self.game.action_count, 100)
        self.assertTrue(self.game.is_draw)
        self.assertEqual(self.game.draw_reason, "action_limit")

    def test_timeout_skips_turn_without_removing_or_placing_pieces(self):
        """A timeout advances the turn and preserves the board and queues."""
        self.play([0, 1, 2, 3, 4, 5])
        board_before = self.game.board.copy()
        queues_before = {
            player: queue.copy() for player, queue in self.game.piece_order.items()
        }
        active_player = self.game.current_player

        accepted, message = self.game.skip_turn_for_timeout()

        self.assertTrue(accepted)
        self.assertIn("ran out of time", message)
        self.assertEqual(self.game.board, board_before)
        self.assertEqual(self.game.piece_order, queues_before)
        self.assertEqual(self.game.current_player, "X" if active_player == "O" else "O")
        self.assertEqual(self.game.action_count, 7)

    def test_timeout_counts_toward_the_100_action_draw(self):
        """Timed-out turns count as actions and can end the round."""
        self.game.action_count = self.game.MAX_ACTIONS - 1
        accepted, message = self.game.skip_turn_for_timeout()
        self.assertTrue(accepted)
        self.assertIn("100 actions", message)
        self.assertEqual(self.game.action_count, 100)
        self.assertTrue(self.game.is_draw)
        self.assertEqual(self.game.draw_reason, "action_limit")

    def test_reset_clears_rotation_and_repetition_history(self):
        """A rematch starts with empty queues and a fresh occurrence count."""
        self.play([0, 1, 2, 3, 4, 5, 6])
        self.game.reset()
        self.assertEqual(self.game.board, [""] * 9)
        self.assertEqual(self.game.current_player, "X")
        self.assertEqual(self.game.piece_order, {"X": [], "O": []})
        self.assertEqual(self.game.action_count, 0)
        self.assertIsNone(self.game.draw_reason)
        self.assertEqual(list(self.game._state_occurrences.values()), [1])


if __name__ == "__main__":
    unittest.main()
