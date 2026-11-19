"""Start the Graffiti Grid NiceGUI application."""

from nicegui import app, ui

from game_screen import show_game

# Make the project's public artwork available to the browser.
app.add_static_files("/assets", "assets")


@ui.page("/")
def home():
    """Create a separate local game for each browser session."""
    show_game()


if __name__ == "__main__":
    ui.run(
        title="Graffiti Grid",
        host="127.0.0.1",
        port=8080,
        reload=False,
    )
