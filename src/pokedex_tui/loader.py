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

    def __init__(self, line=None) -> None:
        super().__init__(line)
        self.line = line

    def __str__(self):
        return f"line {self.line}"


def bundled_csv_path():
    """
    Returns the path to the bundled CSV file of pokemon data
    """
    base_dir = Path(pokedex_tui.__file__).resolve().parent
    csv_path = base_dir / "data" / "Pokemon.csv"
    return csv_path


def load_pokemon(path=None):
    """
    Loads the given or bundled csv for pokemon data.
    Returns a tuple of Pokemon records in file order,
    """
    path = bundled_csv_path() if not path else path

    if Path(path).is_file():
        with open(path, "r") as f:
            data = csv.DictReader(f)
            for row in data:
                print(row)

    raise PokedexDataError(None)


if __name__ == "__main__":
    load_pokemon()
