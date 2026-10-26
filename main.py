"""Start the Graffiti Grid web application."""

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
    ui.run(
        title="Graffiti Grid",
        host="127.0.0.1",
        port=8080,
        reload=False,
    )
