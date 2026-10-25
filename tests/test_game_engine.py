"""Check Classic rules without starting the web application."""

import unittest

from game_engine import ClassicGame


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


if __name__ == "__main__":
    unittest.main()
