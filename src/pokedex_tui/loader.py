"""
- Loads the given csv pokedex, defaults to bundled file in data/
- Returns clean and validated records
"""

import csv
from pathlib import Path

import pokedex_tui


class PokedexDataError(ValueError):
    """
    Single error class used to represent in loading, cleaning and validating records
    """

    def __init__(self, message: str | None, line: str | None = None) -> None:
        super().__init__(line)
        self.line = line
        self.message = message

    def __str__(self):
        return f"{self.message} Line: {self.line}" if self.line else f"{self.message}"


def bundled_csv_path():
    """
    Returns the path to the bundled CSV file of pokemon data
    """
    base_dir = Path(pokedex_tui.__file__).resolve().parent
    csv_path = base_dir / "data" / "Pokemon.csv"
    return csv_path


def load_pokemon(path: str | Path | None = None):
    """
    Loads the given or bundled csv for pokemon data.
    Returns a tuple of Pokemon records in file order,
    """
    path = Path(bundled_csv_path()) if path is None else Path(path)

    if path.is_file():
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                data = csv.DictReader(f)
                assert data is not None
        except UnicodeDecodeError as e:
            raise PokedexDataError(message=f"{e} file isn't UTF-8")

    raise PokedexDataError(message=f"{path} not found!!")


if __name__ == "__main__":
    load_pokemon()
