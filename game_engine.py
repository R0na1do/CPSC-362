class ClassicGame:
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

    def __init__(self):
        self.reset()

    def reset(self):
        self.board = [""] * 9
        self.current_player = "X"
        self.winner = None
        self.is_draw = False

    @property
    def finished(self):
        return self.winner is not None or self.is_draw

    def make_move(self, cell):
        if self.finished:
            return False, "The game has already ended."

        if type(cell) is not int or not 0 <= cell < 9:
            return False, "Choose a valid square."

        if self.board[cell] != "":
            return False, "That square is already occupied."

        self.board[cell] = self.current_player

        for a, b, c in self.WINNING_LINES:
            if (
                self.board[a]
                == self.board[b]
                == self.board[c]
                == self.current_player
            ):
                self.winner = self.current_player
                return True, f"{self.winner} wins!"

        if all(self.board):
            self.is_draw = True
            return True, "The game is a draw."

        self.current_player = (
            "O" if self.current_player == "X" else "X"
        )
        return True, f"{self.current_player}'s turn."
