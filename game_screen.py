"""Local Classic and Blitz screens with optional guest sign-in."""

import asyncio
from functools import partial
from math import ceil
from time import monotonic
from typing import Any

from nicegui import run, ui

from game_engine import BlitzGame, ClassicGame
from guest_auth import GuestSignInError, sign_in_guest
from rooms import (
    RoomError,
    create_room,
    get_room,
    join_room,
    leave_room,
    move_room,
    ready_room,
    rematch_room,
)

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
    display: grid;
    grid-template-columns: 220px minmax(0, 1fr);
    align-items: start;
    gap: 24px;
    width: 100%;
    max-width: 1140px;
    margin: 0 auto;
    padding: 16px;
}

.arcade-header, .screen-content {
    width: 100%;
    min-width: 0;
    gap: 12px;
}

.menu-grid, .player-names {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 16px;
    width: 100%;
}

.menu-grid { grid-template-columns: 1fr; gap: 12px; }
.menu-card { padding: 16px; gap: 10px; }
.mode-card.room-card { border-left-color: #ffe14a; }

.match-layout {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 210px;
    gap: 20px;
    align-items: start;
    width: 100%;
}

.match-board-area, .match-controls {
    width: 100%;
    min-width: 0;
    align-items: center;
    gap: 12px;
}

.color-picker {
    display: grid;
    grid-template-columns: repeat(6, minmax(0, 1fr));
    gap: 8px;
    width: 100%;
}

.color-picker > :first-child {
    grid-column: 1 / -1;
}

.arcade-shell .q-btn {
    min-height: 44px;
}

.guest-panel {
    padding: 16px;
    font-size: 13px;
}

.brand-art {
    width: 100%;
    max-height: 135px;
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
    font-size: clamp(26px, 4vw, 36px);
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
    padding: 18px;
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
    max-width: min(400px, calc(100dvh - 180px));
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
    line-height: 1;
    padding: 0;
    align-items: center;
    justify-content: center;
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

.online-board { max-width: clamp(200px, calc(100dvh - 330px), 320px); }
.room-message:empty { display: none; }
.online-player-names {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
    width: 100%;
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
    min-width: 0;
    min-height: 44px;
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

@media (max-width: 900px) {
    .nicegui-content { padding: 8px; }
    .arcade-shell { grid-template-columns: 1fr; gap: 12px; padding: 0; }
    .arcade-header {
        display: grid;
        grid-template-columns: 120px minmax(0, 1fr);
        align-items: center;
        gap: 12px;
    }
    .arcade-header > .arcade-kicker { display: none; }
    .brand-art { max-height: 90px; }
    .guest-panel { padding: 10px; }
    .match-layout { grid-template-columns: minmax(0, 1fr) 190px; }
}

@media (max-width: 600px) {
    .arcade-shell { padding-bottom: env(safe-area-inset-bottom, 0px); }
    .menu-grid, .match-layout, .player-names { grid-template-columns: 1fr; }
    .menu-grid, .match-layout { gap: 12px; }
    .arcade-panel { padding: 14px; }
    .guest-panel { padding: 10px; }
    .game-board { max-width: min(360px, calc(100dvh - 360px)); }
    .game-board { gap: 6px; padding: 7px; }
    .game-cell { font-size: clamp(28px, 9vw, 48px); min-height: 44px; }
    .game-board.online-board { max-width: clamp(180px, calc(100dvh - 420px), 280px); }
    .online-controls {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 8px;
    }
    .online-note { grid-column: 1 / -1; }
    .match-board-area .graffiti-heading { font-size: 22px; line-height: 1.3; }
    .player-badge { padding: 8px; font-size: 12px; }
    .timer-panel { padding: 8px 12px; }
    .timer-number { font-size: 28px; }
    .victory-icon { font-size: 40px; }
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
        self.guest_client = None
        self.guest_id = None
        self.signing_in = False
        self.room = None
        self.room_busy = False
        self.room_lock = asyncio.Lock()
        self.lobby_open = False
        self.online_name = "Guest"

        ui.dark_mode().enable()
        ui.add_css(PAGE_CSS)
        self._build_shell()
        self.show_menu()

    def _build_shell(self) -> None:
        """Create the persistent title and screen-content container."""
        with ui.element("main").classes("arcade-shell"):
            with ui.column().classes("arcade-header items-center"):
                ui.image("/assets/graffiti-grid.png").props("fit=contain").classes("brand-art")
                ui.label(
                    "YOUR MOVE · YOUR COLOR · YOUR CROWN"
                ).classes("arcade-kicker text-center")
                with ui.column().classes("arcade-panel guest-panel items-center gap-2"):
                    self.guest_status = ui.label("Not signed in. Local play is available.")
                    self.guest_status.props('role="status" aria-live="polite"')
                    self.guest_button = ui.button(
                        "SIGN IN AS GUEST", on_click=self.sign_in
                    )
                    ui.label(
                        "Guest sign-in lasts until refresh. Private rooms use Supabase."
                    ).classes("text-xs text-gray-400 text-center")
            self.content = ui.column().classes("screen-content items-center")
            ui.timer(1.0, self.poll_room, immediate=False)

    async def sign_in(self) -> None:
        """Sign in once for this page without blocking other players."""
        if self.signing_in or self.guest_client is not None:
            return
        self.signing_in = True
        self.guest_button.disable()
        self.guest_status.set_text("Signing in...")
        try:
            self.guest_client, self.guest_id = await run.io_bound(sign_in_guest)
            self.guest_status.set_text("Signed in as guest.")
            if self.lobby_open:
                self.show_lobby()
        except GuestSignInError as error:
            self.guest_status.set_text(str(error))
        finally:
            self.signing_in = False
            self.guest_button.set_enabled(self.guest_client is None)

    def _clear_screen(self) -> None:
        """Clear screen-specific controls before drawing another screen."""
        timer = self.controls.get("clock_task")
        if timer is not None:
            timer.cancel()
        self.clock_state["deadline"] = None
        self.content.clear()
        self.controls.clear()
        self.lobby_open = False

    def show_menu(self) -> None:
        """Display available modes and links to the game instructions."""
        self._clear_screen()

        with self.content:
            ui.label("PICK YOUR MODE").classes("graffiti-heading")
            with ui.element("div").classes("menu-grid"):
                with ui.column().classes("arcade-panel mode-card menu-card items-center"):
                    ui.button(
                        "✦  PLAY CLASSIC  ✦",
                        on_click=lambda: self.show_setup("Classic"),
                        color="cyan-8",
                    ).classes("w-full text-lg font-black tracking-wider").props("size=lg")
                    ui.label("Two players on one screen. Three in a row wins. No timer.").classes(
                        "text-sm text-gray-300 text-center"
                    )
                with ui.column().classes(
                    "arcade-panel mode-card blitz-card menu-card items-center"
                ):
                    ui.button(
                        "⚡  PLAY BLITZ  ⚡",
                        on_click=lambda: self.show_setup("Blitz"),
                        color="pink-8",
                    ).classes("w-full text-lg font-black tracking-wider").props("size=lg")
                    ui.label("Three pieces each. Your fourth replaces your oldest. Timed turns.").classes(
                        "text-sm text-gray-300 text-center"
                    )
                with ui.column().classes(
                    "arcade-panel mode-card room-card menu-card items-center"
                ):
                    ui.button(
                        "PRIVATE ROOM LOBBY", on_click=self.show_lobby, color="amber-9"
                    ).classes("w-full text-lg font-black tracking-wider").props("size=lg")
                    ui.label("Play Classic online. Create a room or join a friend by code.").classes(
                        "text-sm text-gray-300 text-center"
                    )
            ui.button("HOW TO PLAY", on_click=self.show_rules).props("flat")

            ui.label("LOCAL CLASSIC / BLITZ · PRIVATE ONLINE CLASSIC").classes(
                "text-xs text-gray-500 text-center tracking-widest"
            )

    async def poll_room(self) -> None:
        """Refresh a visible room once per second."""
        if (
            self.lobby_open
            and self.room
            and not self.room_busy
            and self.room["status"] != "abandoned"
        ):
            await self.update_room("refresh", quiet=True)

    def show_lobby(self) -> None:
        """Show the current room or the Create/Join form."""
        self._clear_screen()
        self.lobby_open = True
        self.room_buttons = []
        with self.content:
            with ui.column().classes("arcade-panel gap-3"):
                ui.label("ONLINE CLASSIC").classes("graffiti-heading")
                self.room_status = ui.label().classes("room-message")
                self.room_status.props('role="status" aria-live="polite"')
                if self.room:
                    self._show_online_room()
                elif self.guest_client is None:
                    self.room_status.set_text("Sign in as a guest above to use rooms.")
                else:
                    name = ui.input("Your name", value=self.online_name).props(
                        "maxlength=20 outlined dense"
                    )
                    ui.label("Private Classic rooms use no turn timer.")
                    ui.label("Create a room to get a code you can share.")
                    create = ui.button(
                        "CREATE ROOM",
                        on_click=lambda: self.update_room("create", name=name.value),
                    )
                    ui.separator()
                    ui.label("OR JOIN AN EXISTING ROOM").classes("font-bold")
                    code = ui.input(
                        "Code from the host", placeholder="Paste the host's code"
                    ).props("maxlength=32 inputmode=numeric outlined dense")
                    join = ui.button(
                        "JOIN ROOM",
                        on_click=lambda: self.update_room(
                            "join", code.value, name=name.value
                        ),
                    )
                    join.bind_enabled_from(
                        code, "value", backward=lambda value: bool(value and value.strip())
                    )
                    self.room_buttons.extend([create, join])
                back = ui.button("BACK TO MENU", on_click=self.show_menu).props("flat")
                self.room_buttons.append(back)

    def _show_online_room(self) -> None:
        """Build the online board and room controls."""
        room = self.room
        seat = "x" if room["x_player_id"] == self.guest_id else "o"
        ui.label(
            f"Room {room['room_code']} · Round {room['round_no']} · You are {seat.upper()}"
        ).classes("text-sm font-bold")
        with ui.element("div").classes("match-layout"):
            with ui.column().classes("match-board-area"):
                with ui.element("div").classes("online-player-names"):
                    for player in ("x", "o"):
                        name = room.get(f"{player}_name") or "Waiting for player"
                        ui.label(f"{player.upper()} · {name}").classes(
                            "break-all "
                            + ("mark-pink" if player == "x" else "mark-cyan")
                        )
                if room["status"] == "active":
                    status = f"{room[room['turn'] + '_name']}'s turn · {room['turn'].upper()}"
                elif room["status"] == "finished":
                    status = (
                        f"{room[room['winner'] + '_name']} wins!"
                        if room["winner"]
                        else "It's a draw!"
                    )
                elif room["status"] == "abandoned":
                    status = "The host closed this room."
                else:
                    status = "Both players must be ready to start."
                ui.label(status).classes(
                    "text-xl font-bold text-center break-all"
                ).props('role="status" aria-live="polite"')
                winning = set()
                if room["winner"] and room.get("end_reason") == "win":
                    for line in ClassicGame.WINNING_LINES:
                        if all(room["board"][cell] == room["winner"] for cell in line):
                            winning.update(line)
                with ui.element("div").classes("game-board online-board"):
                    for cell, mark in enumerate(room["board"]):
                        button = ui.button(
                            mark.upper(),
                            on_click=partial(self.update_room, "move", cell=cell),
                            color=None,
                        ).classes("game-cell")
                        row, column = divmod(cell, 3)
                        button.props(
                            f'aria-label="Online row {row + 1}, column {column + 1}: '
                            f'{mark.upper() or "empty"}"'
                        )
                        button.set_enabled(
                            room["status"] == "active"
                            and room["turn"] == seat
                            and not mark
                        )
                        if mark:
                            button.classes("mark-pink" if mark == "x" else "mark-cyan")
                        if cell in winning:
                            button.classes("winning-cell")
                        self.room_buttons.append(button)
            with ui.column().classes("match-controls online-controls"):
                if room["status"] == "waiting":
                    for player in ("x", "o"):
                        state = "Ready" if room[f"{player}_ready"] else "Not ready"
                        ui.label(f"{player.upper()}: {state}").classes("online-note")
                    ready = ui.button(
                        "READY", on_click=lambda: self.update_room("ready")
                    )
                    ready.set_enabled(
                        room["o_player_id"] is not None and not room[f"{seat}_ready"]
                    )
                    self.room_buttons.append(ready)
                elif room["status"] == "finished":
                    if room.get("end_reason") == "forfeit":
                        ui.label("Round ended by forfeit.").classes("online-note")
                    ui.label("Both players must agree to a rematch.").classes(
                        "online-note"
                    )
                    rematch = ui.button(
                        "REMATCH", on_click=lambda: self.update_room("rematch")
                    )
                    rematch.set_enabled(not room[f"{seat}_ready"])
                    self.room_buttons.append(rematch)
                    if room[f"{seat}_ready"]:
                        ui.label("Waiting for the other player to agree.").classes(
                            "online-note"
                        )
                refresh = ui.button(
                    "REFRESH ROOM", on_click=lambda: self.update_room("refresh")
                )
                self.room_buttons.append(refresh)
                with ui.dialog() as confirmation, ui.card():
                    ui.label(
                        "Leave this room? Leaving an active round counts as a loss."
                    )
                    ui.button("Keep playing", on_click=confirmation.close)
                    leave = ui.button(
                        "CONFIRM LEAVE", on_click=lambda: self.update_room("leave")
                    )
                    self.room_buttons.append(leave)
                leave = ui.button("LEAVE ROOM", on_click=confirmation.open).props(
                    "flat"
                )
                self.room_buttons.append(leave)

    async def update_room(
        self, action: str, code: str = "", name: str = "", cell=None, quiet=False
    ) -> None:
        """Wait for a background refresh before handling a player click."""
        if quiet and self.room_busy:
            return
        snapshot = self.room
        async with self.room_lock:
            if not self.lobby_open or (snapshot and self.room is None):
                return
            await self._send_room_request(action, code, name, cell, quiet, snapshot)

    async def _send_room_request(self, action, code, name, cell, quiet, snapshot):
        """Send a request and display only the confirmed database state."""
        self.room_busy = True
        buttons = [(button, button.enabled) for button in self.room_buttons]
        if not quiet:
            for button, _ in buttons:
                button.disable()
            self.room_status.set_text("Contacting Supabase...")
        changed = False
        try:
            if action == "create":
                room = await run.io_bound(create_room, self.guest_client, name)
                self.online_name = name.strip()
            elif action == "join":
                room = await run.io_bound(join_room, self.guest_client, code, name)
                self.online_name = name.strip()
            elif action == "ready":
                room = await run.io_bound(
                    ready_room, self.guest_client, self.room["room_code"]
                )
            elif action == "move":
                room = await run.io_bound(
                    move_room,
                    self.guest_client,
                    self.room["room_code"],
                    cell,
                    snapshot["version"],
                )
            elif action in ("rematch", "leave"):
                operation = rematch_room if action == "rematch" else leave_room
                room = await run.io_bound(
                    operation,
                    self.guest_client,
                    self.room["room_code"],
                    snapshot["round_no"],
                )
                if action == "leave":
                    room = None
            else:
                room = await run.io_bound(
                    get_room, self.guest_client, self.room["room_code"]
                )
            if quiet and not self.lobby_open:
                return
            changed = room != self.room
            self.room = room
            self.room_status.set_text("")
        except RoomError as error:
            if self.lobby_open:
                self.room_status.set_text(str(error))
        finally:
            self.room_busy = False
            if not quiet:
                for button, enabled in buttons:
                    button.set_enabled(enabled)
        if changed:
            self.show_lobby()

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
                with ui.element("div").classes("player-names"):
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
        with ui.element("div").classes("color-picker"):
            ui.label(f"{player} · {self.names[player]}").classes(
                f"font-bold mark-{self.colors[player]} min-w-24"
            )
            for slug, color in PLAYER_COLORS.items():
                button = ui.button(
                    color["symbol"],
                    on_click=partial(self._select_color, player, slug),
                    color=None,
                ).classes("color-swatch")
                button.props(f'aria-label="{player} color: {color["name"]}"')
                button.tooltip(color["name"])
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
            with ui.element("div").classes("match-layout"):
                with ui.column().classes("match-board-area"):
                    self._build_player_labels()
                    self._build_game_board()
                    ui.label("X starts · local round · no account needed").classes(
                        "text-xs text-gray-500 text-center tracking-widest"
                    )
                with ui.column().classes("match-controls"):
                    if self.mode == "Blitz":
                        self._build_turn_clock()
                    self._build_result_panel()
                    self._build_leave_controls()
            self.refresh_board()
            if self.mode == "Blitz" and self.clock_state["duration"]:
                self._start_turn_clock()
                self.controls["clock_task"] = ui.timer(
                    0.2, self._tick_turn_clock
                )
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
