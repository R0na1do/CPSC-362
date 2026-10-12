from nicegui import ui


@ui.page("/")
def home():
    ui.dark_mode().enable()

    with ui.column().classes("w-full items-center gap-4"):
        ui.label("GRAFFITI GRID").classes(
            "text-5xl font-bold text-yellow-400"
        )
        ui.label("Our Python game project is running!")
        ui.button(
            "Test Button",
            on_click=lambda: ui.notify("NiceGUI is working!"),
        )


if __name__ == "__main__":
    ui.run(
        title="Graffiti Grid",
        host="127.0.0.1",
        port=8080,
        reload=False,
    )