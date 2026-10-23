"""Menus, player setup, and the local Classic game screen."""

from functools import partial

from nicegui import ui

from game_engine import ClassicGame


# Shared appearance for this page.
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


def show_game():
    """Create independent game state for each page visit."""
    game = ClassicGame()
    names = {"X": "Player 1", "O": "Player 2"}

    ui.dark_mode().enable()
    ui.add_css(PAGE_CSS)

    with ui.column().classes("arcade-shell items-center gap-5"):
        ui.label("GRAFFITI GRID").classes("arcade-title")
        ui.label("YOUR MOVE. YOUR MOMENT.").classes(
            "text-sm tracking-widest text-gray-400 text-center"
        )
        content = ui.column().classes("w-full items-center gap-5")

    def clear_screen():
        """Replace the current screen without losing player names."""
        content.clear()

    # Main menu.
    def show_menu():
        clear_screen()

        with content:
            with ui.column().classes("arcade-panel items-center gap-4"):
                ui.label("Choose your game").classes(
                    "text-2xl font-bold"
                )
                ui.label(
                    "Challenge a friend on the same screen."
                ).classes("text-gray-300 text-center")

                ui.button(
                    "PLAY CLASSIC",
                    on_click=show_setup,
                    color="cyan-8",
                ).classes("w-full").props("size=lg")

                ui.label(
                    "Classic: three in a row wins. No turn timer."
                ).classes("text-sm text-gray-400 text-center")

                ui.button(
                    "BLITZ · COMING NEXT",
                    color="grey-8",
                ).classes("w-full").disable()

                ui.label(
                    "Blitz: keep up to three pieces. "
                    "Your fourth placement removes your oldest."
                ).classes("text-sm text-gray-400 text-center")

                ui.button(
                    "How to play",
                    on_click=show_rules,
                ).props("flat")

            ui.label(
                "Local play available now · Online rooms coming later"
            ).classes("text-sm text-gray-400 text-center")

    # Instructions.
    def show_rules():
        clear_screen()

        with content:
            with ui.column().classes("arcade-panel gap-4"):
                ui.label("How to play Classic").classes(
                    "text-2xl font-bold"
                )
                for rule in (
                    "1. Enter a different name for each player.",
                    "2. Player X goes first.",
                    "3. Take turns choosing an empty square.",
                    "4. Get three in a row, column, or diagonal to win.",
                    "5. A full board with no winner is a draw.",
                ):
                    ui.label(rule).classes("text-gray-300")

                ui.button("Back to menu", on_click=show_menu)

    # Player names are display names, not account credentials.
    def show_setup():
        clear_screen()

        with content:
            with ui.column().classes("arcade-panel gap-4"):
                ui.label("Meet the players").classes(
                    "text-2xl font-bold"
                )
                ui.label("Classic · Same-screen play").classes(
                    "text-gray-400"
                )

                name_x = ui.input(
                    "Player X name", value=names["X"]
                ).classes("w-full").props("maxlength=20 outlined")

                name_o = ui.input(
                    "Player O name", value=names["O"]
                ).classes("w-full").props("maxlength=20 outlined")

                error = ui.label().classes("text-red-300")
                error.props('role="alert"')

                def start_game():
                    # Validate names before changing game state.
                    first = (name_x.value or "").strip()
                    second = (name_o.value or "").strip()

                    if not first or not second:
                        error.set_text("Enter a name for both players.")
                        return

                    if len(first) > 20 or len(second) > 20:
                        error.set_text("Use 20 characters or fewer.")
                        return

                    if first.casefold() == second.casefold():
                        error.set_text(
                            "Use different names so players are clear."
                        )
                        return

                    names.update({"X": first, "O": second})
                    game.reset()
                    show_board()

                ui.button(
                    "START MATCH",
                    on_click=start_game,
                    color="cyan-8",
                ).classes("w-full").props("size=lg")

                ui.button(
                    "Back to menu", on_click=show_menu
                ).props("flat")

    # Board and result display.
    def show_board():
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
                for line in game.WINNING_LINES:
                    if all(
                        game.board[index] == game.winner
                        for index in line
                    ):
                        winning_positions.update(line)

            for position, button in enumerate(buttons):
                piece = game.board[position]
                button.set_text(piece)
                button.set_enabled(
                    not game.finished and piece == ""
                )
                button.classes(
                    remove="piece-x piece-o winning-cell"
                )

                if piece:
                    button.classes(f"piece-{piece.lower()}")
                if position in winning_positions:
                    button.classes("winning-cell")

                row, column = divmod(position, 3)
                button.props(
                    f'aria-label="Row {row + 1}, '
                    f'column {column + 1}"'
                )
                # Set text through NiceGUI instead of HTML interpolation.
                button.set_text(piece)

            if game.winner:
                winner = names[game.winner]
                status.set_text(f"{winner} wins!")
                result_icon.set_text("🏆")
                result_title.set_text(f"{winner} takes the crown!")
                result_detail.set_text("Three in a row. Well played.")
            elif game.is_draw:
                status.set_text("It's a draw!")
                result_icon.set_text("🤝")
                result_title.set_text("An even match")
                result_detail.set_text(
                    "The board is full. Ready for another round?"
                )
            else:
                player = game.current_player
                status.set_text(f"{names[player]}'s turn · {player}")

            result.set_visibility(game.finished)
            leave_button.set_visibility(not game.finished)
            leave_confirmation.set_visibility(False)

        with content:
            ui.label("CLASSIC · LOCAL MATCH").classes(
                "text-sm text-gray-400"
            )

            with ui.row().classes("w-full justify-between gap-3"):
                ui.label(f"X · {names['X']}").classes(
                    "text-cyan-300 font-bold break-all"
                )
                ui.label(f"O · {names['O']}").classes(
                    "text-pink-300 font-bold break-all"
                )

            status = ui.label().classes(
                "text-2xl font-bold text-center break-all"
            )
            status.props('role="status" aria-live="polite"')

            with ui.element("div").classes("game-board"):
                for position in range(9):
                    button = ui.button(
                        "",
                        on_click=partial(play_move, position),
                        color=None,
                    ).classes("game-cell")
                    buttons.append(button)

            # Show the trophy only after a finished round.
            with ui.column().classes(
                "arcade-panel items-center gap-3"
            ) as result:
                result_icon = ui.label().classes("victory-icon")
                result_title = ui.label().classes(
                    "text-2xl font-bold text-center break-all"
                )
                result_detail = ui.label().classes(
                    "text-gray-300 text-center"
                )
                ui.button(
                    "PLAY AGAIN",
                    on_click=play_again,
                    color="cyan-8",
                ).classes("w-full")
                ui.button(
                    "Main menu", on_click=show_menu
                ).props("flat")

            # Confirm before leaving an unfinished round.
            leave_button = ui.button(
                "Leave round",
                on_click=lambda: leave_confirmation.set_visibility(True),
            ).props("flat")

            with ui.column().classes(
                "arcade-panel items-center gap-3"
            ) as leave_confirmation:
                ui.label(
                    "Leave this round? Your board will be discarded."
                ).classes("text-center")
                with ui.row():
                    ui.button("Leave", on_click=show_menu)
                    ui.button(
                        "Keep playing",
                        on_click=lambda: (
                            leave_confirmation.set_visibility(False)
                        ),
                    ).props("flat")

            ui.label(
                "Names last until refresh. X starts each local round."
            ).classes("text-sm text-gray-400 text-center")

        refresh_board()

    show_menu()