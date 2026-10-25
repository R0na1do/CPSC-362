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
        self.board: list[str] = [""] * 9
        self.current_player: str = "X"
        self.winner: str | None = None
        self.is_draw: bool = False
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


class BlitzGame(ClassicGame):
    """Run Blitz rules while preserving each player's piece placement order."""

    MAX_ACTIVE_PIECES = 3
    MAX_ACTIONS = 100
    REPETITIONS_FOR_DRAW = 3

    def __init__(self) -> None:
        """Create a fresh Blitz round and its repetition history."""
        self.piece_order: dict[str, list[int]] = {"X": [], "O": []}
        self.action_count = 0
        self.draw_reason: str | None = None
        self._state_occurrences: dict[
            tuple[tuple[str, ...], str, tuple[int, ...], tuple[int, ...]], int
        ] = {}
        super().__init__()

    @property
    def oldest_cells(self) -> set[int]:
        """Return each player's oldest active cell for UI highlighting."""
        return {queue[0] for queue in self.piece_order.values() if queue}

    def reset(self) -> None:
        """Start a new Blitz round and clear its queues and draw history."""
        super().reset()
        self.piece_order = {"X": [], "O": []}
        self.action_count = 0
        self.draw_reason = None
        self._state_occurrences = {}
        self._record_current_state()

    def make_move(self, cell: object) -> tuple[bool, str]:
        """Apply a legal placement, rotating out a player's oldest mark."""
        if self.finished:
            return False, "The game has already ended."
        if (
            not isinstance(cell, int)
            or isinstance(cell, bool)
            or not 0 <= cell < len(self.board)
        ):
            return False, "Choose a valid square."
        if self.board[cell]:
            return False, "That square is already occupied."

        player = self.current_player
        queue = self.piece_order[player]
        if len(queue) == self.MAX_ACTIVE_PIECES:
            oldest_cell = queue.pop(0)
            self.board[oldest_cell] = ""

        self.board[cell] = player
        queue.append(cell)
        self.action_count += 1

        # A win takes priority over both repetition and the action limit.
        if self._has_winning_line(player):
            self.winner = player
            message = f"{player} wins!"
        else:
            self.current_player = "O" if player == "X" else "X"
            state = self._state_key()
            self._state_occurrences[state] = self._state_occurrences.get(state, 0) + 1

            if self._state_occurrences[state] >= self.REPETITIONS_FOR_DRAW:
                self.is_draw = True
                self.draw_reason = "repetition"
            elif self.action_count >= self.MAX_ACTIONS:
                self.is_draw = True
                self.draw_reason = "action_limit"

            if (
                self.is_draw
                and self._state_occurrences[state] >= self.REPETITIONS_FOR_DRAW
            ):
                message = "The game is a draw by repetition."
            elif self.is_draw:
                message = "The game is a draw after 100 actions."
            else:
                message = f"{self.current_player}'s turn."

        return True, message

    def skip_turn_for_timeout(self) -> tuple[bool, str]:
        """Skip the active turn without moving pieces when its clock expires."""
        if self.finished:
            return False, "The game has already ended."

        timed_out_player = self.current_player
        self.current_player = "O" if timed_out_player == "X" else "X"
        self.action_count += 1

        state = self._state_key()
        self._state_occurrences[state] = self._state_occurrences.get(state, 0) + 1
        if self._state_occurrences[state] >= self.REPETITIONS_FOR_DRAW:
            self.is_draw = True
            self.draw_reason = "repetition"
            return True, "The game is a draw by repetition."
        if self.action_count >= self.MAX_ACTIONS:
            self.is_draw = True
            self.draw_reason = "action_limit"
            return True, "The game is a draw after 100 actions."
        return (
            True,
            f"{timed_out_player} ran out of time. {self.current_player}'s turn.",
        )

    def _state_key(
        self,
    ) -> tuple[tuple[str, ...], str, tuple[int, ...], tuple[int, ...]]:
        """Capture the full state, including next turn and both piece queues."""
        return (
            tuple(self.board),
            self.current_player,
            tuple(self.piece_order["X"]),
            tuple(self.piece_order["O"]),
        )

    def _record_current_state(self) -> None:
        """Record the current full state for threefold-repetition detection."""
        state = self._state_key()
        self._state_occurrences[state] = self._state_occurrences.get(state, 0) + 1
