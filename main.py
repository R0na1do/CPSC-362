"""Start the Graffiti Grid web application."""

import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from nicegui import app, ui

from game_screen import show_game

load_dotenv(Path(__file__).with_name(".env"))

app.add_static_files("/assets", "assets")


@ui.page("/")
def home():
    """Render the local game for the current browser session."""
    show_game()


if __name__ == "__main__":
    # Session files contain tokens; only the server account should access this folder.
    app.storage.path.mkdir(mode=0o700, parents=True, exist_ok=True)
    app.storage.path.chmod(0o700)
    ui.run(
        title="Graffiti Grid",
        host="127.0.0.1",
        port=8080,
        reload=False,
        storage_secret=os.getenv("NICEGUI_STORAGE_SECRET") or secrets.token_urlsafe(32),
    )
