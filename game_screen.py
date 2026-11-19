"""Graffiti Grid menu, player setup, and local Classic game."""

from functools import partial

from nicegui import ui

from game_engine import ClassicGame

PAGE_CSS = """
body {
    min-height: 100vh;
    background:
        radial-gradient(ellipse at 15% 8%, #27113d 0, transparent 32rem),
        radial-gradient(ellipse at 90% 88%, #073342 0, transparent 30rem),
        #08090d;
    color: #f8fafc;
}

.arcade-shell {
    width: 100%;
    max-width: 760px;
    margin: 0 auto;
    padding: 24px 16px 40px;
}

.arcade-panel {
    width: 100%;
    padding: clamp(18px, 5vw, 30px);
    border: 1px solid rgba(255, 255, 255, .18);
    border-radius: 22px;
    background: rgba(13, 16, 25, .94);
    box-shadow: 0 18px 60px rgba(0, 0, 0, .42);
}

.menu-art {
    width: min(100%, 450px);
    max-height: 340px;
    object-fit: contain;
    border-radius: 18px;
    filter: drop-shadow(0 0 22px rgba(0, 204, 255, .2));
}

.arcade-heading {
    font-size: clamp(25px, 6vw, 38px);
    line-height: 1.05;
    font-weight: 900;
    font-style: italic;
    letter-spacing: .04em;
    color: #ffe52e;
    text-shadow: 2px 2px #fa168c, 4px 4px #10131b;
    text-align: center;
}

.game-board {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
    width: 100%;
    max-width: 430px;
    margin: 0 auto;
    padding: 12px;
    border: 3px solid #f1eee6;
    border-radius: 12px;
    background:
        linear-gradient(90deg, transparent 32.8%, #e8e5dc 33%, #e8e5dc 33.7%, transparent 34%),
        linear-gradient(90deg, transparent 66.2%, #e8e5dc 66.5%, #e8e5dc 67.2%, transparent 67.5%),
        linear-gradient(0deg, transparent 32.8%, #e8e5dc 33%, #e8e5dc 33.7%, transparent 34%),
        linear-gradient(0deg, transparent 66.2%, #e8e5dc 66.5%, #e8e5dc 67.2%, transparent 67.5%),
        #0a0c12;
    box-shadow: 0 0 24px rgba(0, 204, 255, .12);
}

.game-cell {
    width: 100%;
    min-width: 0;
    aspect-ratio: 1;
    border: 0;
    border-radius: 7px;
    background: rgba(8, 10, 15, .25);
    font-size: clamp(38px, 10vw, 72px);
    font-weight: 1000;
    text-shadow: 0 0 16px currentColor;
    transition: transform 140ms ease, background 140ms ease;
}

.game-cell:not([disabled]):hover {
    transform: scale(.94) rotate(-1deg);
    background: rgba(255, 255, 255, .08);
}

.game-cell[disabled] { opacity: 1 !important; }
.piece-x { color: #fa168c !important; }
.piece-o { color: #00d9ff !important; }
.winning-cell { background: rgba(255, 229, 46, .2) !important; }

.player-badge {
    padding: 10px 14px;
    border: 1px solid currentColor;
    border-radius: 12px;
    background: rgba(255, 255, 255, .04);
    font-weight: 800;
}

.action-button {
    width: 100%;
    font-weight: 900;
    letter-spacing: .04em;
}

.winner-icon {
    font-size: 76px;
    filter: drop-shadow(0 0 18px rgba(255, 229, 46, .5));
    animation: trophy-pop 420ms ease-out;
}

@keyframes trophy-pop {
    from { transform: scale(.65) rotate(-12deg); opacity: .2; }
    to { transform: scale(1) rotate(0); opacity: 1; }
}

@media (max-width: 480px) {
    .game-board { gap: 8px; padding: 8px; }
}

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { animation-duration: .01ms !important; transition-duration: .01ms !important; }
}
"""


def show_game():
    """Build this browser session's screens and Classic game state."""
    game = ClassicGame()
    names = {"X": "Player 1", "O": "Player 2"}

    ui.dark_mode().enable()
    ui.add_css(PAGE_CSS)

    with ui.column().classes("arcade-shell items-center gap-5"):
        content = ui.column().classes("w-full items-center gap-5")

    def clear_screen():
        """Remove the current screen before drawing the next one."""
        content.clear()

    def show_menu():
        """Show mode choices and the current local-play options."""
        clear_screen()
        with content:
            with ui.column().classes("arcade-panel items-center gap-4"):
                ui.image("/assets/graffiti-grid.png").classes("menu-art")
                ui.label("PICK YOUR MODE").classes("arcade-heading")
                ui.label("Two players · one screen · one winner").classes(
                    "text-center text-gray-300"
                )
                ui.button(
                    "PLAY CLASSIC",
                    on_click=show_setup,
                    color="pink-7",
                ).classes(
                    "action-button"
                ).props("size=lg")
                ui.label("Classic: take turns. Three in a row wins.").classes(
                    "text-sm text-center text-gray-400"
                )
                ui.button(
                    "BLITZ · COMING NEXT",
                    color="grey-8",
                ).classes("action-button").disable()
                ui.label(
                    "Blitz: keep up to three pieces; "
                    "your fourth removes your oldest."
                ).classes("text-sm text-center text-gray-400")
                ui.button("HOW TO PLAY", on_click=show_rules).props("flat")
            ui.label("Local game is ready · Online rooms are planned").classes(
                "text-xs text-gray-500 text-center"
            )

    def show_rules():
        """Explain the playable Classic rules."""
        clear_screen()
        with content:
            with ui.column().classes("arcade-panel gap-4"):
                ui.label("HOW TO PLAY").classes("arcade-heading")
                for rule in (
                    "Player X starts; then players alternate turns.",
                    "Choose any empty square. An occupied square cannot be reused.",
                    "Three matching marks in a row, column, or diagonal win.",
                    "A full board without a winner is a draw.",
                    "Use Play Again to start a fresh round.",
                ):
                    ui.label(f"•  {rule}").classes("text-gray-200")
                ui.button("BACK TO MENU", on_click=show_menu, color="pink-7")

    def show_setup():
        """Collect clear display names before starting a round."""
        clear_screen()
        with content:
            with ui.column().classes("arcade-panel gap-4"):
                ui.label("WHO’S PLAYING?").classes("arcade-heading")
                ui.label("Choose a name for each side.").classes("text-gray-300")
                name_x = (
                    ui.input("Player X · pink", value=names["X"])
                    .classes("w-full")
                    .props("maxlength=20 outlined")
                )
                name_o = (
                    ui.input("Player O · cyan", value=names["O"])
                    .classes("w-full")
                    .props("maxlength=20 outlined")
                )
                error = ui.label().classes("text-red-300")
                error.props('role="alert"')

                def start_match():
                    first = (name_x.value or "").strip()
                    second = (name_o.value or "").strip()
                    if not first or not second:
                        error.set_text("Enter a name for both players.")
                        return
                    if first.casefold() == second.casefold():
                        error.set_text("Choose two different names.")
                        return
                    names.update({"X": first, "O": second})
                    game.reset()
                    show_board()

                ui.button(
                    "START MATCH",
                    on_click=start_match,
                    color="pink-7",
                ).classes(
                    "action-button"
                ).props("size=lg")
                ui.button("BACK", on_click=show_menu).props("flat")

    def show_board():
        """Draw the board and update it after each accepted move."""
        clear_screen()
        buttons = []

        def play_move(position):
            accepted, message = game.make_move(position)
            if not accepted:
                ui.notify(message, type="warning")
                return
            refresh_board()

        def play_again():
            game.reset()
            show_board()

        def refresh_board():
            winning_positions = set()
            if game.winner:
                winning_line = next(
                    line
                    for line in game.WINNING_LINES
                    if all(game.board[index] == game.winner for index in line)
                )
                winning_positions.update(winning_line)

            for position, button in enumerate(buttons):
                piece = game.board[position]
                button.set_text(piece)
                button.set_enabled(not game.finished and piece == "")
                button.classes(remove="piece-x piece-o winning-cell")
                if piece:
                    button.classes(f"piece-{piece.lower()}")
                if position in winning_positions:
                    button.classes("winning-cell")
                row, column = divmod(position, 3)
                button.props(
                    f'aria-label="Row {row + 1}, column {column + 1}: '
                    f'{piece or "empty"}"'
                )

            if game.winner:
                winner = names[game.winner]
                status.set_text(f"{winner} wins!")
                result_title.set_text(f"{winner} takes the crown!")
                result_detail.set_text("Three in a row. Well played!")
                result_icon.set_text("🏆")
            elif game.is_draw:
                status.set_text("It’s a draw!")
                result_title.set_text("A close match!")
                result_detail.set_text("The board is full. Run it back?")
                result_icon.set_text("🤝")
            else:
                player = game.current_player
                status.set_text(f"{names[player]}’s turn · {player}")

            result.set_visibility(game.finished)
            leave_button.set_visibility(not game.finished)
            leave_confirmation.set_visibility(False)

        with content:
            ui.label("CLASSIC · LOCAL MATCH").classes(
                "text-xs tracking-widest text-gray-400"
            )
            with ui.row().classes("w-full justify-between gap-3"):
                ui.label(f'X  {names["X"]}').classes("player-badge piece-x break-all")
                ui.label(f'O  {names["O"]}').classes("player-badge piece-o break-all")

            status = ui.label().classes("text-2xl font-black text-center break-all")
            status.props('role="status" aria-live="polite"')

            with ui.element("div").classes("game-board"):
                for position in range(9):
                    buttons.append(
                        ui.button(
                            "",
                            on_click=partial(play_move, position),
                            color=None,
                        ).classes("game-cell")
                    )

            with ui.column().classes("arcade-panel items-center gap-3") as result:
                result_icon = ui.label().classes("winner-icon")
                result_title = ui.label().classes(
                    "text-2xl font-black text-center break-all"
                )
                result_detail = ui.label().classes("text-gray-300 text-center")
                ui.button(
                    "PLAY AGAIN",
                    on_click=play_again,
                    color="pink-7",
                ).classes("action-button")
                ui.button("MAIN MENU", on_click=show_menu).props("flat")

            leave_button = ui.button(
                "Leave round",
                on_click=lambda: leave_confirmation.set_visibility(True),
            ).props("flat")

            with ui.column().classes(
                "arcade-panel items-center gap-3"
            ) as leave_confirmation:
                ui.label(
                    "Leave this round? The current board will be discarded."
                ).classes("text-center")
                with ui.row():
                    ui.button("Leave", on_click=show_menu, color="pink-7")
                    ui.button(
                        "Keep playing",
                        on_click=lambda: leave_confirmation.set_visibility(False),
                    ).props("flat")

        refresh_board()

    show_menu()
