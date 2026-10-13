from .app import PokedexApp


def main() -> None:
    """Entry point of the app"""
    app = PokedexApp()
    app.run()


if __name__ == "__main__":
    main()
