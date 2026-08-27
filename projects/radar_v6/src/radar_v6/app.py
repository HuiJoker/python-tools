from .export import configure_typography
from .ui import RadarApp


def main():
    configure_typography()
    app = RadarApp()
    app.mainloop()
