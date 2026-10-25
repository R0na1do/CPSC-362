"""Start the Graffiti Grid web application."""

from game_screen import show_game
from nicegui import ui


# Build a separate game screen for each page visit.
@ui.page("/")
def home():
    """Render the local game for the current browser session."""
    show_game()


# Run the application locally on this computer.
if __name__ == "__main__":
    ui.run(
        title="Graffiti Grid",
        host="127.0.0.1",
        port=8080,
        reload=False,
    )
