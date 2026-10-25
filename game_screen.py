"""Menus, player setup, and the local Classic game screen."""

from functools import partial
from math import ceil
from time import monotonic
from typing import Any

from nicegui import ui

from game_engine import BlitzGame, ClassicGame

PLAYER_COLORS = {
    "pink": {"name": "Neon Pink", "hex": "#ff35a8", "symbol": "🩷"},
    "cyan": {"name": "Electric Cyan", "hex": "#20dfff", "symbol": "🩵"},
    "lime": {"name": "Acid Lime", "hex": "#b9ff3b", "symbol": "💚"},
    "yellow": {"name": "Sunburst Yellow", "hex": "#ffe14a", "symbol": "💛"},
    "violet": {"name": "Violet Tag", "hex": "#b477ff", "symbol": "💜"},
    "orange": {"name": "Hot Orange", "hex": "#ff8a35", "symbol": "🧡"},
}
TIMER_OPTIONS = {
    0: "No timer",
    15: "15 seconds",
    30: "30 seconds · default",
    60: "60 seconds",
}

# Keep the arcade styling together so screen logic stays easy to scan.
PAGE_CSS = """
body {
    min-height: 100vh;
    background:
        radial-gradient(ellipse at 12% 5%, rgba(231, 30, 145, .22), transparent 34rem),
        radial-gradient(ellipse at 88% 82%, rgba(0, 200, 255, .17), transparent 34rem),
        repeating-linear-gradient(
            0deg, transparent 0 47px, rgba(255,255,255,.025) 48px
        ),
        repeating-linear-gradient(
            90deg, transparent 0 47px, rgba(255,255,255,.025) 48px
        ),
        #08090d;
    color: #f8fafc;
    font-family: Inter, ui-sans-serif, system-ui, sans-serif;
}

.arcade-shell {
    width: 100%;
    max-width: 820px;
    margin: 0 auto;
    padding: 8px 16px 28px;
}

.brand-art {
    width: min(100%, 360px);
    max-height: 175px;
    object-fit: contain;
    filter: drop-shadow(0 0 28px rgba(0, 217, 255, .14));
}

.arcade-kicker {
    color: #cbd5e1;
    font-size: 11px;
    font-weight: 900;
    letter-spacing: .28em;
    text-transform: uppercase;
}

.graffiti-heading {
    font-family: Impact, "Arial Black", sans-serif;
    font-size: clamp(30px, 7vw, 48px);
    font-weight: 900;
    font-style: italic;
    letter-spacing: .04em;
    color: #ffe14a;
    text-shadow: 3px 3px #f12e9b, 6px 6px #11131a;
    text-align: center;
    text-transform: uppercase;
}

.arcade-panel {
    width: 100%;
    padding: clamp(18px, 4vw, 30px);
    border: 1px solid rgba(255, 255, 255, .18);
    border-radius: 16px;
    background: linear-gradient(145deg, rgba(24, 27, 38, .97), rgba(10, 12, 18, .98));
    box-shadow: 0 20px 70px rgba(0, 0, 0, .42), inset 0 1px rgba(255,255,255,.08);
}

.mode-card {
    border-left: 4px solid #20dfff;
}

.mode-card.blitz-card {
    border-left-color: #ff35a8;
}

.game-board {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 9px;
    width: 100%;
    max-width: 470px;
    margin: 0 auto;
    padding: 10px;
    border: 3px solid rgba(255,255,255,.82);
    border-radius: 13px;
    background: #101117;
    box-shadow: 0 0 0 4px rgba(241, 46, 155, .24), 0 0 32px rgba(32, 223, 255, .14);
}

.game-cell {
    width: 100%;
    aspect-ratio: 1;
    min-width: 0;
    font-family: Impact, "Arial Black", sans-serif;
    font-size: clamp(42px, 10vw, 76px);
    font-weight: 900;
    border: 1px solid rgba(255,255,255,.17);
    border-radius: 7px;
    background: linear-gradient(145deg, rgba(37, 39, 50, .7), rgba(12, 13, 18, .86));
    transition: transform 140ms ease, background 140ms ease, box-shadow 140ms ease;
}

.game-cell:not([disabled]):hover {
    transform: scale(.96) rotate(-1deg);
    background: rgba(255,255,255,.09);
    box-shadow: inset 0 0 16px rgba(255,255,255,.08);
}

.game-cell[disabled] {
    opacity: 1 !important;
}

.mark-pink { color: #ff35a8 !important; text-shadow: 0 0 20px rgba(255,53,168,.65); }
.mark-cyan { color: #20dfff !important; text-shadow: 0 0 20px rgba(32,223,255,.65); }
.mark-lime { color: #b9ff3b !important; text-shadow: 0 0 20px rgba(185,255,59,.62); }
.mark-yellow { color: #ffe14a !important; text-shadow: 0 0 20px rgba(255,225,74,.62); }
.mark-violet { color: #b477ff !important; text-shadow: 0 0 20px rgba(180,119,255,.62); }
.mark-orange { color: #ff8a35 !important; text-shadow: 0 0 20px rgba(255,138,53,.62); }

.player-badge {
    min-width: 0;
    padding: 10px 14px;
    border: 1px solid currentColor;
    border-radius: 10px;
    background: rgba(255,255,255,.045);
    font-weight: 900;
    box-shadow: 0 0 18px currentColor;
}

.timer-panel {
    width: min(100%, 470px);
    border: 1px solid rgba(255,255,255,.18);
    border-radius: 14px;
    background: rgba(8, 9, 14, .8);
    padding: 14px 18px;
}

.timer-number {
    font-family: "SFMono-Regular", Consolas, monospace;
    font-size: clamp(32px, 8vw, 48px);
    font-weight: 900;
    line-height: 1;
    color: #f8fafc;
    text-shadow: 0 0 18px currentColor;
}

.timer-urgent {
    color: #ff4b6e !important;
    animation: clock-pulse .55s ease-in-out infinite alternate;
}

.timer-track {
    height: 8px;
    width: 100%;
    overflow: hidden;
    border-radius: 99px;
    background: rgba(255,255,255,.12);
}

.timer-fill {
    height: 100%;
    border-radius: inherit;
    transition: width 180ms linear, background-color 180ms ease;
}

.color-chip {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    border: 1px solid rgba(255,255,255,.16);
    border-radius: 9px;
    padding: 9px 12px;
    background: rgba(255,255,255,.04);
}

.color-swatch {
    min-width: 78px;
    min-height: 42px;
    border: 2px solid rgba(255,255,255,.2);
    border-radius: 9px;
    font-size: 12px;
    font-weight: 900;
    text-transform: uppercase;
    transition: transform 120ms ease, box-shadow 120ms ease;
}

.color-swatch:hover { transform: translateY(-2px); }
.color-swatch-selected { outline: 3px solid #fff; outline-offset: 2px; }

.winning-cell {
    border-color: #facc15;
    background: #3c3415;
}

.oldest-piece {
    outline: 3px dashed #ffe14a;
    outline-offset: -6px;
    box-shadow: inset 0 0 18px rgba(255, 225, 74, .24), 0 0 12px rgba(255,225,74,.22);
}

.victory-icon {
    font-size: 72px;
    animation: trophy-arrive 400ms ease-out;
}

@keyframes trophy-arrive {
    from { transform: scale(0.7); opacity: 0; }
    to { transform: scale(1); opacity: 1; }
}

@keyframes clock-pulse {
    from { transform: scale(1); }
    to { transform: scale(1.08); }
}

@media (max-width: 480px) {
    .game-board { gap: 6px; padding: 7px; }
    .player-badge { padding: 8px; font-size: 12px; }
}

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: .01ms !important;
        transition-duration: .01ms !important;
    }
}
"""


class ClassicGameScreen:
    """Build and manage one browser session's local two-mode game."""

    def __init__(self) -> None:
        """Initialize game state, shared display names, and the page shell."""
        self.game = ClassicGame()
        self.names: dict[str, str] = {"X": "Player 1", "O": "Player 2"}
        self.colors = {"X": "pink", "O": "cyan"}
        self.mode = "Classic"
        self.clock_state: dict[str, int | float | None] = {
            "duration": 0,
            "deadline": None,
        }
        self.controls: dict[str, Any] = {}

        ui.dark_mode().enable()
        ui.add_css(PAGE_CSS)
        self._build_shell()
        self.show_menu()

    def _build_shell(self) -> None:
        """Create the persistent title and screen-content container."""
        with ui.column().classes("arcade-shell items-center gap-5"):
            ui.image("/assets/graffiti-grid.png").classes("brand-art")
            ui.label("YOUR MOVE · YOUR COLOR · YOUR CROWN").classes(
                "arcade-kicker text-center"
            )
            self.content = ui.column().classes("w-full items-center gap-5")

    def _clear_screen(self) -> None:
        """Clear screen-specific controls before drawing another screen."""
        timer = self.controls.get("clock_task")
        if timer is not None:
            timer.cancel()
        self.clock_state["deadline"] = None
        self.content.clear()
        self.controls.clear()

    def show_menu(self) -> None:
        """Display available modes and links to the game instructions."""
        self._clear_screen()

        with self.content:
            with ui.column().classes("arcade-panel mode-card items-center gap-4"):
                ui.label("PICK YOUR MODE").classes("graffiti-heading")
                ui.label("Two players. One screen. Make your mark.").classes(
                    "text-gray-300 text-center"
                )
                ui.button(
                    "✦  PLAY CLASSIC  ✦",
                    on_click=lambda: self.show_setup("Classic"),
                    color="cyan-8",
                ).classes("w-full text-lg font-black tracking-wider").props("size=lg")
                ui.label("Classic · steady hands · no clock").classes(
                    "text-xs uppercase tracking-widest text-gray-400 text-center"
                )
            with ui.column().classes(
                "arcade-panel mode-card blitz-card items-center gap-4"
            ):
                ui.button(
                    "⚡  PLAY BLITZ  ⚡",
                    on_click=lambda: self.show_setup("Blitz"),
                    color="pink-8",
                ).classes("w-full text-lg font-black tracking-wider").props("size=lg")
                ui.label("Blitz · 3 pieces each · 30-second turn clock").classes(
                    "text-xs uppercase tracking-widest text-gray-400 text-center"
                )
                ui.label("Your fourth mark rotates your oldest piece out.").classes(
                    "text-sm text-gray-300 text-center"
                )
            ui.button("HOW TO PLAY", on_click=self.show_rules).props("flat")

            ui.label("LOCAL ARCADE · ONLINE ROOMS IN DEVELOPMENT").classes(
                "text-xs text-gray-500 text-center tracking-widest"
            )

    def show_rules(self) -> None:
        """Explain both local game modes and their main rules."""
        self._clear_screen()

        with self.content:
            with ui.column().classes("arcade-panel gap-4"):
                ui.label("THE RULES ON THE WALL").classes("graffiti-heading")
                rules = (
                    "Both modes: X starts. Players alternate and choose empty squares.",
                    "Both modes: three matching pieces in a row, column, or "
                    "diagonal win.",
                    "Classic: a full board without a winner is a draw.",
                    "Blitz: each player keeps up to three pieces; a fourth placement "
                    "removes their oldest piece.",
                    "Blitz timer: 30 seconds by default; choose off, 15, 30, or 60. "
                    "A timeout passes the turn without moving pieces.",
                    "Blitz: a repeated full state draws on its third occurrence; "
                    "100 actions also ends in a draw.",
                )
                for rule in rules:
                    ui.label(rule).classes("text-gray-300")
                ui.button("Back to menu", on_click=self.show_menu)

    def show_setup(self, mode: str = "Classic") -> None:
        """Collect player names, mark colors, and the selected Blitz timer."""
        self.mode = mode
        self.clock_state["duration"] = 30 if mode == "Blitz" else 0
        self._clear_screen()

        with self.content:
            with ui.column().classes("arcade-panel gap-3"):
                ui.label("BUILD YOUR CREW").classes("graffiti-heading text-3xl")
                ui.label(f"{self.mode.upper()} · LOCAL ARCADE MATCH").classes(
                    "arcade-kicker text-center"
                )
                with ui.row().classes("w-full gap-3"):
                    name_x = (
                        ui.input("Player X · name your mark", value=self.names["X"])
                        .classes("w-full")
                        .props("maxlength=20 outlined dense")
                    )
                    name_o = (
                        ui.input("Player O · name your mark", value=self.names["O"])
                        .classes("w-full")
                        .props("maxlength=20 outlined dense")
                    )
                ui.label("PICK YOUR INK · TAP A COLOR").classes(
                    "arcade-kicker text-yellow-200"
                )
                self.controls["color_swatch_buttons"] = {"X": {}, "O": {}}
                self._build_color_picker("X")
                self._build_color_picker("O")
                timer_choice = None
                if mode == "Blitz":
                    timer_choice = ui.select(
                        options=TIMER_OPTIONS,
                        value=30,
                        label="Turn timer · default is 30 seconds",
                    ).classes("w-full").props("dense outlined")
                else:
                    ui.label("Classic is untimed.").classes("text-xs text-gray-400")
                error = ui.label().classes("text-red-300")
                error.props('role="alert"')
                self.controls.update(
                    {
                        "setup_name_x": name_x,
                        "setup_name_o": name_o,
                        "setup_timer": timer_choice,
                        "setup_error": error,
                    }
                )
                ui.button(
                    "LET’S PLAY  →",
                    on_click=self.start_match,
                    color="cyan-8",
                ).classes("w-full font-black tracking-widest").props("size=md")
                ui.button("BACK TO MODE SELECT", on_click=self.show_menu).props("flat")

    def _build_color_picker(self, player: str) -> None:
        """Show visible, clickable color swatches for one player."""
        with ui.row().classes("w-full items-center gap-2 flex-wrap"):
            ui.label(f"{player} · {self.names[player]}").classes(
                f"font-bold mark-{self.colors[player]} min-w-24"
            )
            for slug, color in PLAYER_COLORS.items():
                button = ui.button(
                    f"{color['symbol']} {color['name']}",
                    on_click=partial(self._select_color, player, slug),
                ).classes("color-swatch")
                button.style(
                    f"background-color: {color['hex']}; color: #101117;"
                )
                if self.colors[player] == slug:
                    button.classes("color-swatch-selected")
                self.controls["color_swatch_buttons"][player][slug] = button

    def _select_color(self, player: str, slug: str) -> None:
        """Select one palette color and update the setup swatch highlights."""
        self.colors[player] = slug
        for option, button in self.controls["color_swatch_buttons"][player].items():
            if option == slug:
                button.classes("color-swatch-selected")
            else:
                button.classes(remove="color-swatch-selected")

    def start_match(self) -> None:
        """Validate player settings, then start a fresh local round."""
        name_x = self.controls["setup_name_x"]
        name_o = self.controls["setup_name_o"]
        timer_choice = self.controls.get("setup_timer")
        error = self.controls["setup_error"]
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
        if self.colors["X"] == self.colors["O"]:
            error.set_text(
                "Pick two different colors so the marks stay easy to tell apart."
            )
            return

        self.names.update({"X": first, "O": second})
        self.clock_state["duration"] = int(timer_choice.value) if timer_choice else 0
        self.game = BlitzGame() if self.mode == "Blitz" else ClassicGame()
        self.show_board()

    def show_board(self) -> None:
        """Build the board, round status, result panel, and leave controls."""
        self._clear_screen()
        self.controls["buttons"] = []

        with self.content:
            self._build_player_labels()
            if self.mode == "Blitz":
                self._build_turn_clock()
            self._build_game_board()
            self._build_result_panel()
            self._build_leave_controls()
            ui.label("X starts · local round · no account needed").classes(
                "text-xs text-gray-500 text-center tracking-widest"
            )

        self.refresh_board()
        if self.mode == "Blitz" and self.clock_state["duration"]:
            self._start_turn_clock()
            self.controls["clock_task"] = ui.timer(0.2, self._tick_turn_clock)
            self._tick_turn_clock()

    def _build_player_labels(self) -> None:
        """Show player names and the live turn status."""
        ui.label(f"{self.mode.upper()} · LOCAL MATCH").classes("arcade-kicker")
        with ui.row().classes("w-full justify-between gap-3"):
            for player in ("X", "O"):
                color_class = f"mark-{self.colors[player]}"
                ui.label(f"{player} · {self.names[player]}").classes(
                    f"player-badge {color_class} break-all"
                )
        self.controls["status"] = ui.label().classes("graffiti-heading break-all")
        self.controls["status"].props('role="status" aria-live="polite"')
        if self.mode == "Blitz":
            ui.label(
                "GOLD DASH = OLDEST MARK · IT ROTATES OUT ON THE NEXT PLACEMENT"
            ).classes("arcade-kicker text-yellow-200 text-center")

    def _build_turn_clock(self) -> None:
        """Create a clear countdown display for Blitz matches."""
        with ui.column().classes("timer-panel items-center gap-2"):
            ui.label("TURN CLOCK").classes("arcade-kicker")
            self.controls["timer_value"] = ui.label().classes("timer-number")
            self.controls["timer_caption"] = ui.label().classes(
                "text-xs text-gray-400 uppercase tracking-widest text-center"
            )
            with ui.element("div").classes("timer-track"):
                self.controls["timer_fill"] = ui.element("div").classes("timer-fill")
        duration = int(self.clock_state["duration"] or 0)
        if duration == 0:
            self.controls["timer_value"].set_text("OFF")
            self.controls["timer_caption"].set_text("No turn limit")
            self.controls["timer_fill"].style(replace="width: 0%;")

    def _start_turn_clock(self) -> None:
        """Set a new deadline using server-side monotonic time."""
        duration = int(self.clock_state["duration"] or 0)
        self.clock_state["deadline"] = monotonic() + duration

    def _tick_turn_clock(self) -> None:
        """Render remaining time and apply an expired turn exactly once."""
        if not isinstance(self.game, BlitzGame) or self.game.finished:
            return
        deadline = self.clock_state["deadline"]
        if deadline is None:
            return

        remaining_seconds = max(0, deadline - monotonic())
        remaining = ceil(remaining_seconds)
        timer_value = self.controls["timer_value"]
        timer_caption = self.controls["timer_caption"]
        timer_fill = self.controls["timer_fill"]

        if remaining == 0:
            self._expire_current_turn()
            return

        player = self.game.current_player
        color = PLAYER_COLORS[self.colors[player]]["hex"]
        timer_value.set_text(f"00:{remaining:02d}")
        timer_value.classes(
            remove="timer-urgent " + " ".join(f"mark-{slug}" for slug in PLAYER_COLORS)
        )
        timer_value.classes(f"mark-{self.colors[player]}")
        if remaining <= 5:
            timer_value.classes("timer-urgent")
        timer_caption.set_text(f"{self.names[player]} is on the clock")
        duration = int(self.clock_state["duration"] or 1)
        progress = remaining_seconds / duration * 100
        timer_fill.style(replace=f"width: {progress:.1f}%; background-color: {color};")

    def _expire_current_turn(self) -> None:
        """Apply one timeout without removing or placing any game piece."""
        if not isinstance(self.game, BlitzGame) or self.game.finished:
            return
        timed_out_player = self.game.current_player
        self.game.skip_turn_for_timeout()
        if self.game.finished:
            self._stop_turn_clock()
        else:
            self._start_turn_clock()
        self.refresh_board()
        ui.notify(
            f"{self.names[timed_out_player]} ran out of time. Turn passed.",
            type="warning",
        )

    def _stop_turn_clock(self) -> None:
        """Cancel the page timer and clear the active deadline."""
        timer = self.controls.get("clock_task")
        if timer is not None:
            timer.cancel()
        self.clock_state["deadline"] = None

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
        deadline = self.clock_state["deadline"]
        if (
            isinstance(self.game, BlitzGame)
            and self.clock_state["duration"]
            and deadline is not None
            and monotonic() >= deadline
        ):
            self._expire_current_turn()
            ui.notify("That move arrived after the timer expired.", type="warning")
            return

        accepted, message = self.game.make_move(position)
        if not accepted:
            ui.notify(message, type="warning")
            return
        if self.game.finished:
            self._stop_turn_clock()
        elif isinstance(self.game, BlitzGame) and self.clock_state["duration"]:
            self._start_turn_clock()
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
        button.classes(
            remove=(
                "winning-cell oldest-piece "
                + " ".join(f"mark-{slug}" for slug in PLAYER_COLORS)
            )
        )

        if piece:
            button.classes(f"mark-{self.colors[piece]}")
        if position in getattr(self.game, "oldest_cells", set()):
            button.classes("oldest-piece")
        if position in winning_positions:
            button.classes("winning-cell")

        row, column = divmod(position, 3)
        occupant = piece or "empty"
        oldest = position in getattr(self.game, "oldest_cells", set())
        description = "; oldest piece, removed on next placement" if oldest else ""
        button.props(
            f'aria-label="Row {row + 1}, column {column + 1}: {occupant}{description}"'
        )

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
            status.classes(remove=" ".join(f"mark-{slug}" for slug in PLAYER_COLORS))
            status.classes(f"mark-{self.colors[player]}")

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
        status.classes(remove=" ".join(f"mark-{slug}" for slug in PLAYER_COLORS))
        status.classes(f"mark-{self.colors[winner_piece]}")
        self.controls["result_icon"].set_text("🏆")
        self.controls["result_title"].set_text(f"{winner} takes the crown!")
        self.controls["result_detail"].set_text("Three in a row. Well played.")

    def _show_draw(self, status) -> None:
        """Set the draw message and rematch prompt."""
        status.set_text("It's a draw!")
        self.controls["result_icon"].set_text("🤝")
        if isinstance(self.game, BlitzGame):
            if self.game.draw_reason == "repetition":
                title = "THE GRID LOOPED"
                detail = "The same full position appeared three times. Run it back?"
            else:
                title = "ACTION LIMIT HIT"
                detail = "100 actions played. Ready for another round?"
        else:
            title = "EVEN MATCH"
            detail = "The board is full. Ready for another round?"
        self.controls["result_title"].set_text(title)
        self.controls["result_detail"].set_text(detail)

    def show_leave_confirmation(self) -> None:
        """Show the leave-round confirmation panel."""
        self.controls["leave_confirmation"].set_visibility(True)

    def hide_leave_confirmation(self) -> None:
        """Hide the leave-round confirmation panel."""
        confirmation = self.controls.get("leave_confirmation")
        if confirmation:
            confirmation.set_visibility(False)


def show_game() -> None:
    """Create one independent local game for the current page."""
    ClassicGameScreen()
