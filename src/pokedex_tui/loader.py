"""
- Loads the given csv pokedex, defaults to bundled file in data/
- Returns clean and validated records
"""

import csv
from pathlib import Path

import pokedex_tui

CSV_FIELD_MAP = {
    "ID": "dex_id",
    "Name": "name",
    "Form": "form",
    "Type1": "type1",
    "Type2": "type2",
    "Total": "total",
    "HP": "hp",
    "Attack": "attack",
    "Defense": "defense",
    "Sp. Atk": "sp_atk",
    "Sp. Def": "sp_def",
    "Speed": "speed",
    "Generation": "generation",
}


class PokedexDataError(ValueError):
    """
    Single error class used to represent in loading, cleaning and validating records
    """

    def __init__(self, message: str | None, line: int | None = None) -> None:
        super().__init__(message)
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


def check_headers(csv_fields) -> None:
    """Validates things related to the csv headers"""
    required_fields = list(CSV_FIELD_MAP.keys())
    missing_fields = []

    # TODO: this function definetly needs to be cleaned up

    # Check if the required fields do not match
    if csv_fields and required_fields != csv_fields:
        # check which fields are missing
        for field in required_fields:
            if field not in csv_fields:
                missing_fields.append(field)

    # if all the fields are missing then raise an error
    if missing_fields == required_fields or not csv_fields:
        raise PokedexDataError("empty file!!")
    # raise error only for missing fields in line 1 of the csv
    elif missing_fields:
        raise PokedexDataError(f"Fields missing in CSV file: {missing_fields}", 1)


def load_pokemon(path: str | Path | None = None):
    """
    Loads the given or bundled csv for pokemon data.
    Returns a tuple of Pokemon records in file order,
    """
    path = Path(bundled_csv_path()) if path is None else Path(path)

    # Check if path is actually a file
    if path.is_file():
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                check_headers(reader.fieldnames)
                if next(reader, None) is None:
                    return ()

        except UnicodeDecodeError as e:
            raise PokedexDataError(message=f"{e} file isn't UTF-8")
    else:
        raise PokedexDataError(message=f"{path} not found!!")


if __name__ == "__main__":
    load_pokemon("/Users/utsavdeep/personal/pokedex-tui/tests/fixtures/empty.csv")
