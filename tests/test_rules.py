"""Run from the repository root: python3 -m unittest discover -v."""

import unittest

from graffiti_grid.rules import ClassicGame


class ClassicGameTests(unittest.TestCase):
    def setUp(self):
        self.game = ClassicGame()

    def play(self, positions):
        for position in positions:
            self.game.make_move(position)

    def assert_fresh_game(self):
        self.assertEqual(self.game.board, [None] * 9)
        self.assertEqual(self.game.current_player, "X")
        self.assertIsNone(self.game.winner)
        self.assertFalse(self.game.game_over)
        self.assertFalse(self.game.is_draw())

    def assert_rejected_without_changes(self, position):
        before = (
            self.game.board.copy(), self.game.current_player,
            self.game.winner, self.game.game_over,
        )
        with self.assertRaises(ValueError):
            self.game.make_move(position)
        after = (
            self.game.board, self.game.current_player,
            self.game.winner, self.game.game_over,
        )
        self.assertEqual(after, before)

    def test_new_game(self):
        self.assert_fresh_game()

    def test_valid_moves_alternate_players(self):
        self.game.make_move(0)
        self.assertEqual(self.game.board[0], "X")
        self.assertEqual(self.game.current_player, "O")
        self.game.make_move(4)
        self.assertEqual(self.game.board[4], "O")
        self.assertEqual(self.game.current_player, "X")
        self.assertFalse(self.game.game_over)

    def test_invalid_positions_leave_state_unchanged(self):
        self.game.make_move(4)
        for position in (-1, 9, 100, "0", 1.0, None, True, False, [], {}):
            with self.subTest(position=position):
                self.assert_rejected_without_changes(position)

    def test_occupied_cell_leaves_state_unchanged(self):
        self.game.make_move(0)
        self.assert_rejected_without_changes(0)

    def test_all_winning_lines_for_both_players(self):
        # These expected lines are explicit so the test does not depend on
        # the implementation's own list of winning combinations.
        lines = (
            (0, 1, 2), (3, 4, 5), (6, 7, 8),
            (0, 3, 6), (1, 4, 7), (2, 5, 8),
            (0, 4, 8), (2, 4, 6),
        )
        for line in lines:
            others = [cell for cell in range(9) if cell not in line]
            for player in ("X", "O"):
                with self.subTest(line=line, player=player):
                    self.game.reset()
                    if player == "X":
                        moves = [line[0], others[0], line[1], others[1], line[2]]
                    else:
                        moves = [others[0], line[0], others[1], line[1], others[-1], line[2]]
                    self.play(moves[:-1])
                    self.assertFalse(self.game.game_over)
                    self.assertIsNone(self.game.winner)
                    self.game.make_move(moves[-1])
                    self.assertEqual(self.game.winner, player)
                    self.assertTrue(self.game.game_over)
                    self.assertFalse(self.game.is_draw())
                    self.assertEqual(self.game.current_player, player)

    def test_full_board_without_winner_is_draw(self):
        self.play([0, 1, 2, 4, 3, 5, 7, 6, 8])
        self.assertTrue(self.game.is_draw())
        self.assertTrue(self.game.game_over)
        self.assertIsNone(self.game.winner)

    def test_ninth_move_win_is_not_draw(self):
        self.play([0, 1, 2, 4, 3, 5, 7, 8, 6])
        self.assertEqual(self.game.winner, "X")
        self.assertTrue(self.game.game_over)
        self.assertFalse(self.game.is_draw())

    def test_move_after_win_is_rejected(self):
        self.play([0, 3, 1, 4, 2])
        self.assert_rejected_without_changes(8)

    def test_move_after_draw_is_rejected(self):
        self.play([0, 1, 2, 4, 3, 5, 7, 6, 8])
        self.assert_rejected_without_changes(0)

    def test_reset_during_play_after_win_and_after_draw(self):
        for moves in ([4], [0, 3, 1, 4, 2], [0, 1, 2, 4, 3, 5, 7, 6, 8]):
            with self.subTest(moves=moves):
                self.play(moves)
                self.game.reset()
                self.assert_fresh_game()
                self.game.make_move(0)
                self.assertEqual(self.game.board[0], "X")
                self.game.reset()

    def test_games_have_separate_boards(self):
        other_game = ClassicGame()
        self.game.make_move(0)
        self.assertEqual(other_game.board, [None] * 9)


if __name__ == "__main__":
    unittest.main()
