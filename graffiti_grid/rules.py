"""Rules for a two-player Classic Tic-Tac-Toe game.

Cells are numbered left to right, starting at zero::

    0 | 1 | 2
    3 | 4 | 5
    6 | 7 | 8
"""


class ClassicGame:
    """Store one game's board, turn, and result.

    Use make_move() to play and reset() to start again. Treat the public
    state attributes as read-only when connecting a user interface.
    """

    WINNING_LINES = (
        (0, 1, 2), (3, 4, 5), (6, 7, 8),
        (0, 3, 6), (1, 4, 7), (2, 5, 8),
        (0, 4, 8), (2, 4, 6),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        """Clear the board and result, with X taking the first turn."""
        self.board = [None] * 9
        self.current_player = "X"
        self.winner = None
        self.game_over = False

    def make_move(self, position):
        """Place the current player's mark in an empty cell from 0 to 8.

        Raise ValueError for an invalid move without changing any state.
        After a terminal move, current_player remains the player who moved.
        """
        if self.game_over:
            raise ValueError("The game is over. Reset to play again.")
        # bool is a subclass of int in Python, but is not a valid cell number.
        if type(position) is not int or not 0 <= position <= 8:
            raise ValueError("Position must be an integer from 0 to 8.")
        if self.board[position] is not None:
            raise ValueError("That cell is already occupied.")

        self.board[position] = self.current_player
        self.winner = self._find_winner()
        self.game_over = self.winner is not None or self.is_draw()

        if not self.game_over:
            self.current_player = "O" if self.current_player == "X" else "X"

    def _find_winner(self):
        """Return the winning mark, or None if no line is complete."""
        for first, second, third in self.WINNING_LINES:
            mark = self.board[first]
            if mark is not None and mark == self.board[second] == self.board[third]:
                return mark
        return None

    def is_draw(self):
        """Return True only for a full board without a winner."""
        return self.winner is None and all(cell is not None for cell in self.board)
