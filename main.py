"""Start the Graffiti Grid web application."""

from nicegui import ui

from game_screen import show_game


# Build a separate game screen for each page visit.
@ui.page("/")
def home():
    show_game()


# Run the application locally on this computer.
if __name__ == "__main__":
    ui.run(
        title="Graffiti Grid",
        host="127.0.0.1",
        port=8080,
        reload=False,
    )