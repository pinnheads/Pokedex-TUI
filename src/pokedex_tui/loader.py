"""
- Loads the given csv pokedex, defaults to bundled file in data/
- Returns clean and validated records
"""

import csv
from pathlib import Path

import pokedex_tui
from pokedex_tui.models import GENERATIONS, TYPES, Pokemon

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

    # Check if the required fields do not match
    if csv_fields and required_fields != csv_fields:
        # check which fields are missing
        for field in required_fields:
            if field not in csv_fields:
                missing_fields.append(field)
    # raise error only for missing fields in line 1 of the csv
    if missing_fields:
        raise PokedexDataError(f"Fields missing in CSV file: {missing_fields}", 1)


def check_fields(row: dict, line_num: int):
    """Checks row data for missing/extra fields and raises Error if found"""

    # Check for extra fields
    if None in row:
        extra_values = row[None]
        raise PokedexDataError(
            f"Too many fields in row {line_num}: {extra_values}", line_num
        )

    # Check for too few fields
    if None in row.values():
        missing_fields = [k for k, v in row.items() if v is None]
        raise PokedexDataError(
            f"column {line_num} has TOO FEW fields. Missing: {missing_fields}", line_num
        )


def whole_number_in_range(val: int, field_name: str) -> bool:
    """Checks if the passed value a whole number and in range based on field name"""
    if field_name == "ID" and val < 1:
        return False

    if field_name in [
        "HP",
        "Attack",
        "Defense",
        "Sp. Atk",
        "Sp. Def",
        "Speed",
    ] and (val > 255 or val < 1):
        return False

    if field_name == "Generation" and val not in GENERATIONS:
        return False

    return not (field_name == "Total" and val < 1)


def get_pokemon(row: dict, line_num: int) -> Pokemon:
    """Converts CSV row into a Pokemon"""
    kwargs = {}
    for csv_field, poke_field in CSV_FIELD_MAP.items():
        trimmed_val = row[csv_field].strip()

        if csv_field in ["Name", "Type1"] and trimmed_val == "":
            raise PokedexDataError(f"{csv_field} contains blank data: {row}", line_num)

        # Deal with empty Form and Type2 Values
        if csv_field in ["Form", "Type2"] and trimmed_val == "":
            trimmed_val = None

        if (
            csv_field in ["Type1", "Type2"]
            and trimmed_val not in TYPES
            and trimmed_val is not None
        ):
            raise PokedexDataError(
                f"{csv_field} is an unrecognized type. {trimmed_val}", line_num
            )

        # Convert ID and stats to int
        if (
            csv_field
            in [
                "ID",
                "Total",
                "HP",
                "Attack",
                "Defense",
                "Sp. Atk",
                "Sp. Def",
                "Speed",
                "Generation",
            ]
            and trimmed_val is not None
        ):
            if str.isascii(trimmed_val) and str.isdigit(trimmed_val):
                trimmed_val = int(trimmed_val)
                if not whole_number_in_range(trimmed_val, csv_field):
                    raise PokedexDataError(
                        f"{csv_field} not in range: {trimmed_val}", line_num
                    )
            else:
                raise PokedexDataError(
                    f"{csv_field} value is not a whole number - {trimmed_val}", line_num
                )

        kwargs[poke_field] = trimmed_val

    new_pokemon = Pokemon(**kwargs)
    stats_total = sum(new_pokemon.stats)

    if new_pokemon.total != sum(new_pokemon.stats):
        raise PokedexDataError(
            f"Totals is {new_pokemon.total} but stats add up to {stats_total}", line_num
        )

    return new_pokemon


def load_pokemon(path: str | Path | None = None):
    """
    Loads the given or bundled csv for pokemon data.
    Returns a tuple of Pokemon records in file order,
    """
    path = Path(bundled_csv_path()) if path is None else Path(path)

    pokemon_list = []
    # Check if path is actually a file
    try:
        with open(path, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)

            # if all the fields are missing then raise an error
            if reader.fieldnames is None:
                raise PokedexDataError("empty file!!")

            check_headers(reader.fieldnames)
            keys = set()

            for row in reader:
                check_fields(row, reader.line_num)

                new_pokemon = get_pokemon(row, reader.line_num)

                if new_pokemon.key not in keys:
                    keys.add(new_pokemon.key)
                else:
                    raise PokedexDataError(f"Duplicate data: {row}", reader.line_num)

                pokemon_list.append(new_pokemon)

        return tuple(pokemon_list)

    except UnicodeDecodeError as e:
        raise PokedexDataError(message=f"{e} file isn't UTF-8") from e
    except OSError as oserr:
        raise PokedexDataError(message=f"{path} not found!!") from oserr


if __name__ == "__main__":
    load_pokemon()
