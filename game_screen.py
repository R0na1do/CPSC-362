"""Menus, player setup, and the local Classic game screen."""

from functools import partial
from typing import Any

from nicegui import ui

from game_engine import ClassicGame

# Keep the arcade styling together so screen logic stays easy to scan.
PAGE_CSS = """
body {
    background: radial-gradient(circle at top, #243253, #090e1a 65%);
    color: #f1f5f9;
}

.arcade-shell {
    width: 100%;
    max-width: 620px;
    margin: 0 auto;
    padding: 24px 16px;
}

.arcade-title {
    font-size: clamp(36px, 9vw, 62px);
    font-weight: 900;
    font-style: italic;
    letter-spacing: -2px;
    color: #facc15;
    text-shadow: 3px 3px #db2777;
    text-align: center;
}

.arcade-panel {
    width: 100%;
    padding: 24px;
    border: 1px solid #475569;
    border-radius: 22px;
    background: #111a2d;
}

.game-board {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
    width: 100%;
    max-width: 390px;
    margin: 0 auto;
}

.game-cell {
    width: 100%;
    aspect-ratio: 1;
    font-size: clamp(32px, 8vw, 56px);
    font-weight: 900;
    border: 2px solid #475569;
    border-radius: 14px;
    background: #1e293b;
    transition: transform 150ms, border-color 150ms;
}

.game-cell:not([disabled]):hover {
    transform: translateY(-3px);
    border-color: #67e8f9;
}

.game-cell[disabled] {
    opacity: 1 !important;
}

.piece-x { color: #67e8f9 !important; }
.piece-o { color: #f9a8d4 !important; }

.winning-cell {
    border-color: #facc15;
    background: #3c3415;
}

.victory-icon {
    font-size: 72px;
    animation: trophy-arrive 400ms ease-out;
}

@keyframes trophy-arrive {
    from { transform: scale(0.7); opacity: 0; }
    to { transform: scale(1); opacity: 1; }
}

@media (prefers-reduced-motion: reduce) {
    .victory-icon { animation: none; }
    .game-cell { transition: none; }
}
"""


class ClassicGameScreen:
    """Build and manage one browser session's local Classic game."""

    def __init__(self) -> None:
        """Initialize game state, shared display names, and the page shell."""
        self.game = ClassicGame()
        self.names: dict[str, str] = {"X": "Player 1", "O": "Player 2"}
        self.controls: dict[str, Any] = {}

        ui.dark_mode().enable()
        ui.add_css(PAGE_CSS)
        self._build_shell()
        self.show_menu()

    def _build_shell(self) -> None:
        """Create the persistent title and screen-content container."""
        with ui.column().classes("arcade-shell items-center gap-5"):
            ui.label("GRAFFITI GRID").classes("arcade-title")
            ui.label("YOUR MOVE. YOUR MOMENT.").classes(
                "text-sm tracking-widest text-gray-400 text-center"
            )
            self.content = ui.column().classes("w-full items-center gap-5")

    def _clear_screen(self) -> None:
        """Clear screen-specific controls before drawing another screen."""
        self.content.clear()
        self.controls.clear()

    def show_menu(self) -> None:
        """Display available modes and links to the game instructions."""
        self._clear_screen()

        with self.content:
            with ui.column().classes("arcade-panel items-center gap-4"):
                ui.label("Choose your game").classes("text-2xl font-bold")
                ui.label("Challenge a friend on the same screen.").classes(
                    "text-gray-300 text-center"
                )
                ui.button(
                    "PLAY CLASSIC",
                    on_click=self.show_setup,
                    color="cyan-8",
                ).classes("w-full").props("size=lg")
                ui.label("Classic: three in a row wins. No turn timer.").classes(
                    "text-sm text-gray-400 text-center"
                )
                ui.button("BLITZ · COMING NEXT", color="grey-8").classes(
                    "w-full"
                ).disable()
                ui.label(
                    "Blitz: keep up to three pieces. "
                    "Your fourth placement removes your oldest."
                ).classes("text-sm text-gray-400 text-center")
                ui.button("How to play", on_click=self.show_rules).props("flat")

            ui.label("Local play available now · Online rooms coming later").classes(
                "text-sm text-gray-400 text-center"
            )

    def show_rules(self) -> None:
        """Show the playable Classic rules in short, numbered steps."""
        self._clear_screen()

        with self.content:
            with ui.column().classes("arcade-panel gap-4"):
                ui.label("How to play Classic").classes("text-2xl font-bold")
                rules = (
                    "1. Enter a different name for each player.",
                    "2. Player X goes first.",
                    "3. Take turns choosing an empty square.",
                    "4. Get three in a row, column, or diagonal to win.",
                    "5. A full board with no winner is a draw.",
                )
                for rule in rules:
                    ui.label(rule).classes("text-gray-300")
                ui.button("Back to menu", on_click=self.show_menu)

    def show_setup(self) -> None:
        """Ask both local players for display names before a round."""
        self._clear_screen()

        with self.content:
            with ui.column().classes("arcade-panel gap-4"):
                ui.label("Meet the players").classes("text-2xl font-bold")
                ui.label("Classic · Same-screen play").classes("text-gray-400")
                name_x = (
                    ui.input("Player X name", value=self.names["X"])
                    .classes("w-full")
                    .props("maxlength=20 outlined")
                )
                name_o = (
                    ui.input("Player O name", value=self.names["O"])
                    .classes("w-full")
                    .props("maxlength=20 outlined")
                )
                error = ui.label().classes("text-red-300")
                error.props('role="alert"')
                ui.button(
                    "START MATCH",
                    on_click=lambda: self.start_match(name_x, name_o, error),
                    color="cyan-8",
                ).classes("w-full").props("size=lg")
                ui.button("Back to menu", on_click=self.show_menu).props("flat")

    def start_match(self, name_x, name_o, error) -> None:
        """Validate player names, then start a fresh local round."""
        first = (name_x.value or "").strip()
        second = (name_o.value or "").strip()

        if not first or not second:
            error.set_text("Enter a name for both players.")
            return
        if len(first) > 20 or len(second) > 20:
            error.set_text("Use 20 characters or fewer.")
            return
        if first.casefold() == second.casefold():
            error.set_text("Choose different names so players are clear.")
            return

        self.names.update({"X": first, "O": second})
        self.game.reset()
        self.show_board()

    def show_board(self) -> None:
        """Build the board, round status, result panel, and leave controls."""
        self._clear_screen()
        self.controls["buttons"] = []

        with self.content:
            self._build_player_labels()
            self._build_game_board()
            self._build_result_panel()
            self._build_leave_controls()
            ui.label("Names last until refresh. X starts each local round.").classes(
                "text-sm text-gray-400 text-center"
            )

        self.refresh_board()

    def _build_player_labels(self) -> None:
        """Show player names and the live turn status."""
        ui.label("CLASSIC · LOCAL MATCH").classes("text-sm text-gray-400")
        with ui.row().classes("w-full justify-between gap-3"):
            ui.label(f"X · {self.names['X']}").classes(
                "text-cyan-300 font-bold break-all"
            )
            ui.label(f"O · {self.names['O']}").classes(
                "text-pink-300 font-bold break-all"
            )
        self.controls["status"] = ui.label().classes(
            "text-2xl font-bold text-center break-all"
        )
        self.controls["status"].props('role="status" aria-live="polite"')

    def _build_game_board(self) -> None:
        """Create nine accessible buttons for the game board."""
        with ui.element("div").classes("game-board"):
            for position in range(9):
                button = ui.button(
                    "",
                    on_click=partial(self.play_move, position),
                    color=None,
                ).classes("game-cell")
                self.controls["buttons"].append(button)

    def _build_result_panel(self) -> None:
        """Create the hidden trophy or draw panel and replay actions."""
        with ui.column().classes("arcade-panel items-center gap-3") as result:
            self.controls["result"] = result
            self.controls["result_icon"] = ui.label().classes("victory-icon")
            self.controls["result_title"] = ui.label().classes(
                "text-2xl font-bold text-center break-all"
            )
            self.controls["result_detail"] = ui.label().classes(
                "text-gray-300 text-center"
            )
            ui.button("PLAY AGAIN", on_click=self.play_again, color="cyan-8").classes(
                "w-full"
            )
            ui.button("Main menu", on_click=self.show_menu).props("flat")

    def _build_leave_controls(self) -> None:
        """Build a confirmation panel before abandoning a live round."""
        self.controls["leave_button"] = ui.button(
            "Leave round", on_click=self.show_leave_confirmation
        ).props("flat")
        with ui.column().classes("arcade-panel items-center gap-3") as confirmation:
            self.controls["leave_confirmation"] = confirmation
            ui.label("Leave this round? Your board will be discarded.").classes(
                "text-center"
            )
            with ui.row():
                ui.button("Leave", on_click=self.show_menu)
                ui.button("Keep playing", on_click=self.hide_leave_confirmation).props(
                    "flat"
                )

    def play_move(self, position: int) -> None:
        """Apply one move and refresh the board if the move is valid."""
        accepted, message = self.game.make_move(position)
        if not accepted:
            ui.notify(message, type="warning")
            return
        self.refresh_board()

    def play_again(self) -> None:
        """Reset the current names and show a fresh round."""
        self.game.reset()
        self.show_board()

    def _winning_positions(self) -> set[int]:
        """Return the winning cells to highlight, or an empty set."""
        if not self.game.winner:
            return set()
        for line in self.game.WINNING_LINES:
            if all(self.game.board[index] == self.game.winner for index in line):
                return set(line)
        return set()

    def refresh_board(self) -> None:
        """Update cell marks, accessibility labels, turn, and result panel."""
        winning_positions = self._winning_positions()
        buttons = self.controls["buttons"]

        for position, button in enumerate(buttons):
            self._update_cell(button, position, winning_positions)

        self._update_status_and_result()

    def _update_cell(self, button, position: int, winning_positions: set[int]) -> None:
        """Set one cell's mark, enabled state, styling, and accessible label."""
        piece = self.game.board[position]
        button.set_text(piece)
        button.set_enabled(not self.game.finished and not piece)
        button.classes(remove="piece-x piece-o winning-cell")

        if piece:
            button.classes(f"piece-{piece.lower()}")
        if position in winning_positions:
            button.classes("winning-cell")

        row, column = divmod(position, 3)
        occupant = piece or "empty"
        button.props(f'aria-label="Row {row + 1}, column {column + 1}: {occupant}"')

    def _update_status_and_result(self) -> None:
        """Display the current turn or the completed-round result."""
        status = self.controls["status"]
        result_finished = self.controls["result"]

        if self.game.winner:
            self._show_winner(status)
        elif self.game.is_draw:
            self._show_draw(status)
        else:
            player = self.game.current_player
            status.set_text(f"{self.names[player]}'s turn · {player}")

        result_finished.set_visibility(self.game.finished)
        self.controls["leave_button"].set_visibility(not self.game.finished)
        self.hide_leave_confirmation()

    def _show_winner(self, status) -> None:
        """Set the winner name and trophy message."""
        winner_piece = self.game.winner
        if winner_piece is None:
            return

        winner = self.names[winner_piece]
        status.set_text(f"{winner} wins!")
        self.controls["result_icon"].set_text("🏆")
        self.controls["result_title"].set_text(f"{winner} takes the crown!")
        self.controls["result_detail"].set_text("Three in a row. Well played.")

    def _show_draw(self, status) -> None:
        """Set the draw message and rematch prompt."""
        status.set_text("It's a draw!")
        self.controls["result_icon"].set_text("🤝")
        self.controls["result_title"].set_text("An even match")
        self.controls["result_detail"].set_text(
            "The board is full. Ready for another round?"
        )

    def show_leave_confirmation(self) -> None:
        """Show the leave-round confirmation panel."""
        self.controls["leave_confirmation"].set_visibility(True)

    def hide_leave_confirmation(self) -> None:
        """Hide the leave-round confirmation panel."""
        confirmation = self.controls.get("leave_confirmation")
        if confirmation:
            confirmation.set_visibility(False)


def show_game() -> None:
    """Create one independent local Classic game for the current page."""
    ClassicGameScreen()
