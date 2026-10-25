"""Rules and state for a local two-player Classic Tic-Tac-Toe round."""


class ClassicGame:
    """Store and update the state of one Classic Tic-Tac-Toe round."""

    WINNING_LINES = (
        (0, 1, 2),
        (3, 4, 5),
        (6, 7, 8),
        (0, 3, 6),
        (1, 4, 7),
        (2, 5, 8),
        (0, 4, 8),
        (2, 4, 6),
    )

    def __init__(self) -> None:
        """Create a game and initialize its board."""
        self.reset()

    def reset(self) -> None:
        """Start a new round with X to move and an empty board."""
        self.board = [""] * 9
        self.current_player = "X"
        self.winner = None
        self.is_draw = False

    @property
    def finished(self) -> bool:
        """Return whether this round has a winner or ended in a draw."""
        return self.winner is not None or self.is_draw

    def make_move(self, cell: object) -> tuple[bool, str]:
        """Apply a legal move, returning whether it was accepted and a message."""
        if self.finished:
            return False, "The game has already ended."

        # bool is a subclass of int, but True and False are not board indexes.
        if (
            not isinstance(cell, int)
            or isinstance(cell, bool)
            or not 0 <= cell < len(self.board)
        ):
            return False, "Choose a valid square."

        if self.board[cell]:
            return False, "That square is already occupied."

        self.board[cell] = self.current_player

        if self._has_winning_line(self.current_player):
            self.winner = self.current_player
            return True, f"{self.winner} wins!"

        if all(self.board):
            self.is_draw = True
            return True, "The game is a draw."

        self.current_player = "O" if self.current_player == "X" else "X"
        return True, f"{self.current_player}'s turn."

    def _has_winning_line(self, player: str) -> bool:
        """Return whether player occupies any of the eight winning lines."""
        return any(
            all(self.board[index] == player for index in line)
            for line in self.WINNING_LINES
        )
