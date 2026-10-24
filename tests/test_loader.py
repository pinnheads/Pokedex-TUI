"""Phase 1: reading, cleaning and validating Pokemon.csv."""

import os
import sys
from collections import Counter
from pathlib import Path

import pytest

from pokedex_tui.loader import PokedexDataError, bundled_csv_path, load_pokemon
from pokedex_tui.models import TYPES, Pokemon

HEADER = '"ID","Name","Form","Type1","Type2","Total","HP","Attack","Defense","Sp. Atk","Sp. Def","Speed","Generation"'
GOOD_ROW_1 = '1,"Bulbasaur"," ","Grass","Poison",318,45,49,49,65,65,45,1'
GOOD_ROW_2 = '4,"Charmander"," ","Fire"," ",309,39,52,43,60,50,65,1'


def find(records, name, form=None):
    """Return the single record with this name and form, failing loudly otherwise."""
    matches = [r for r in records if r.name == name and r.form == form]
    assert len(matches) == 1, f"expected one {name!r}/{form!r}, found {len(matches)}"
    return matches[0]


def write_csv(tmp_path: Path, *rows: str, header: str = HEADER) -> Path:
    path = tmp_path / "pokemon.csv"
    path.write_text("\n".join([header, *rows]) + "\n", encoding="utf-8")
    return path


# =========================================================================
# Small fixture: cleaning rules
# =========================================================================


def test_loads_every_row_of_the_fixture(small_records):
    assert len(small_records) == 14


def test_returns_an_immutable_sequence_of_pokemon(small_records):
    assert isinstance(small_records, tuple)
    assert all(isinstance(r, Pokemon) for r in small_records)


def test_keeps_file_order(small_records):
    assert [r.display_name for r in small_records[:4]] == [
        "Bulbasaur",
        "Charmander",
        "Charizard",
        "Mega Charizard X",
    ]


def test_accepts_str_path_as_well_as_path(small_csv):
    assert load_pokemon(str(small_csv)) == load_pokemon(small_csv)


def test_blank_form_becomes_none(small_records):
    assert find(small_records, "Bulbasaur").form is None


def test_blank_type2_becomes_none(small_records):
    assert find(small_records, "Charmander").type2 is None


def test_no_text_field_is_ever_a_single_space_or_padded(small_records):
    for r in small_records:
        for value in (r.name, r.form, r.type1, r.type2):
            if value is not None:
                assert value == value.strip(), f"{r.key}: {value!r} not trimmed"
                assert value != ""


def test_surrounding_whitespace_is_trimmed_from_names_and_types(small_records):
    pikachu = find(small_records, "Pikachu")
    assert pikachu.type1 == "Electric"


def test_numbers_are_ints(small_records):
    r = find(small_records, "Charizard")
    for value in (
        r.dex_id,
        r.hp,
        r.attack,
        r.defense,
        r.sp_atk,
        r.sp_def,
        r.speed,
        r.total,
        r.generation,
    ):
        assert type(value) is int


def test_all_columns_map_to_the_right_fields(small_records):
    r = find(small_records, "Charizard", "Mega Charizard X")
    assert r.dex_id == 6
    assert r.type1 == "Fire"
    assert r.type2 == "Dragon"
    assert r.stats == (78, 130, 111, 130, 85, 100)
    assert r.total == 634
    assert r.generation == 6


def test_form_rows_are_separate_records_with_their_own_generation(small_records):
    raichu = find(small_records, "Raichu")
    alolan = find(small_records, "Raichu", "Alolan Raichu")
    assert raichu.dex_id == alolan.dex_id == 26
    assert raichu.generation == 1
    assert alolan.generation == 7
    assert alolan.types == ("Electric", "Psychic")


def test_non_ascii_name_survives(small_records):
    assert find(small_records, "Flabébé").dex_id == 669


def test_punctuation_in_names_is_kept(small_records):
    assert find(small_records, "Mr. Mime").dex_id == 122


def test_keys_are_unique_even_when_dex_and_form_repeat(small_records):
    # Zygarde: two rows share ID 718 and a blank Form; only Name tells them apart.
    keys = [r.key for r in small_records]
    assert len(keys) == len(set(keys))


def test_keys_are_stable_across_loads(small_csv):
    first = [r.key for r in load_pokemon(small_csv)]
    second = [r.key for r in load_pokemon(small_csv)]
    assert first == second


def test_header_only_file_loads_as_empty(tmp_path):
    assert load_pokemon(write_csv(tmp_path)) == ()


def test_crlf_line_endings_are_accepted(tmp_path):
    path = tmp_path / "pokemon.csv"
    path.write_bytes(
        (f"{HEADER}\r\n{GOOD_ROW_1}\r\n{GOOD_ROW_2}" + "\r\n").encode("utf-8")
    )
    assert [r.name for r in load_pokemon(path)] == ["Bulbasaur", "Charmander"]


# =========================================================================
# Validation: clear, specific errors
# =========================================================================


def test_broken_fixture_names_line_column_and_value(broken_csv):
    with pytest.raises(PokedexDataError) as excinfo:
        load_pokemon(broken_csv)
    err = excinfo.value
    assert err.line == 4  # the header is line 1
    message = str(err)
    assert "4" in message
    assert "Attack" in message
    assert "eighty-four" in message


def test_data_error_is_a_value_error():
    # Lets callers catch it broadly without importing the loader.
    assert issubclass(PokedexDataError, ValueError)


@pytest.mark.parametrize(
    ("bad_row", "column"),
    [
        ('x6,"Charizard"," ","Fire","Flying",534,78,84,78,109,85,100,1', "ID"),
        ('0,"Charizard"," ","Fire","Flying",534,78,84,78,109,85,100,1', "ID"),
        ('6," "," ","Fire","Flying",534,78,84,78,109,85,100,1', "Name"),
        ('6,"Charizard"," "," ","Flying",534,78,84,78,109,85,100,1', "Type1"),
        ('6,"Charizard"," ","Fyre","Flying",534,78,84,78,109,85,100,1', "Type1"),
        ('6,"Charizard"," ","Fire","Flyng",534,78,84,78,109,85,100,1', "Type2"),
        ('6,"Charizard"," ","Fire","Flying",534,0,84,78,109,85,178,1', "HP"),
        ('6,"Charizard"," ","Fire","Flying",534,78,84,78,109,85,100,1.5', "Generation"),
        ('6,"Charizard"," ","Fire","Flying",534,78,84,78,109,85,100,0', "Generation"),
        ('6,"Charizard"," ","Fire","Flying",534,78,84,78,109,85,100,10', "Generation"),
        ('6,"Charizard"," ","Fire","Flying",999,78,84,78,109,85,100,1', "Total"),
        ('6,"Charizard"," ","Fire","Flying",448,78,84,78,109,-1,100,1', "Sp. Def"),
        ('6,"Charizard"," ","Fire","Flying",534,78,84,78,109,85,1', "column"),
        ('1_0,"Charizard"," ","Fire","Flying",534,78,84,78,109,85,100,1', "ID"),
        ('6,"Charizard"," ","Fire","Flying",534,+78,84,78,109,85,100,1', "HP"),
        ('6,"Charizard"," ","Fire","Flying",534,٧٨,84,78,109,85,100,1', "HP"),
    ],
    ids=[
        "id-not-a-number",
        "id-zero",
        "blank-name",
        "blank-type1",
        "unknown-type1",
        "unknown-type2",
        "stat-below-1",
        "generation-not-int",
        "generation-0",
        "generation-10",
        "total-mismatch",
        "negative-stat",
        "too-few-fields",
        "id-digit-separator",
        "stat-plus-sign",
        "stat-non-ascii-digits",
    ],
)
def test_bad_row_raises_with_line_and_column(tmp_path, bad_row, column):
    path = write_csv(tmp_path, GOOD_ROW_1, GOOD_ROW_2, bad_row)
    with pytest.raises(PokedexDataError) as excinfo:
        load_pokemon(path)
    assert excinfo.value.line == 4
    assert column in str(excinfo.value)


def test_stat_above_255_is_rejected(tmp_path):
    path = write_csv(
        tmp_path, '6,"Charizard"," ","Fire","Flying",712,256,84,78,109,85,100,1'
    )
    with pytest.raises(PokedexDataError) as excinfo:
        load_pokemon(path)
    assert excinfo.value.line == 2
    assert "HP" in str(excinfo.value)


def test_duplicate_row_is_rejected_and_points_at_the_second_copy(tmp_path):
    path = write_csv(tmp_path, GOOD_ROW_1, GOOD_ROW_2, GOOD_ROW_1)
    with pytest.raises(PokedexDataError) as excinfo:
        load_pokemon(path)
    assert excinfo.value.line == 4
    assert "duplicate" in str(excinfo.value).lower()


def test_missing_column_in_header_is_named(tmp_path):
    header = HEADER.replace(',"Speed"', "")
    row = '1,"Bulbasaur"," ","Grass","Poison",318,45,49,49,65,65,1'
    with pytest.raises(PokedexDataError) as excinfo:
        load_pokemon(write_csv(tmp_path, row, header=header))
    assert excinfo.value.line == 1
    assert "Speed" in str(excinfo.value)


def test_columns_in_a_different_order_still_load(tmp_path):
    header = '"Name","ID","Form","Type1","Type2","Total","HP","Attack","Defense","Sp. Atk","Sp. Def","Speed","Generation"'
    row = '"Bulbasaur",1," ","Grass","Poison",318,45,49,49,65,65,45,1'
    (record,) = load_pokemon(write_csv(tmp_path, row, header=header))
    assert (record.dex_id, record.name) == (1, "Bulbasaur")


def test_header_from_another_file_names_every_missing_column(tmp_path):
    # PTI-80: a wrong header is not an "empty file".
    with pytest.raises(PokedexDataError) as excinfo:
        load_pokemon(write_csv(tmp_path, "1,2", header="a,b"))
    message = str(excinfo.value)
    assert excinfo.value.line == 1
    assert "empty" not in message.lower()
    for column in HEADER.replace('"', "").split(","):
        assert column in message


def test_non_number_says_it_is_not_a_whole_number(tmp_path):
    # PTI-82
    path = write_csv(
        tmp_path, '6,"Charizard"," ","Fire","Flying",534,4.5,84,78,109,85,100,1'
    )
    with pytest.raises(PokedexDataError) as excinfo:
        load_pokemon(path)
    message = str(excinfo.value)
    assert "whole number" in message
    assert "HP" in message
    assert "4.5" in message


def test_total_mismatch_names_both_numbers(tmp_path):
    # PTI-82: Total 999, but the stats add up to 534.
    path = write_csv(
        tmp_path, '6,"Charizard"," ","Fire","Flying",999,78,84,78,109,85,100,1'
    )
    with pytest.raises(PokedexDataError) as excinfo:
        load_pokemon(path)
    assert "999" in str(excinfo.value)
    assert "534" in str(excinfo.value)


@pytest.mark.parametrize(
    ("bad_row", "column"),
    [
        ('6," "," ","Fire","Flying",534,78,84,78,109,85,100,1', "Name"),
        ('6,"Charizard"," "," ","Flying",534,78,84,78,109,85,100,1', "Type1"),
    ],
    ids=["blank-name", "blank-type1"],
)
def test_blank_required_value_names_the_column_not_the_whole_row(
    tmp_path, bad_row, column
):
    # PTI-82: the message names the column instead of printing the row dict.
    with pytest.raises(PokedexDataError) as excinfo:
        load_pokemon(write_csv(tmp_path, bad_row))
    message = str(excinfo.value)
    assert column in message
    assert "Flying" not in message


def test_too_few_fields_names_the_missing_columns(tmp_path):
    # PTI-82: keeps the word "column" and says which columns are missing.
    path = write_csv(
        tmp_path, '6,"Charizard"," ","Fire","Flying",534,78,84,78,109,85,1'
    )
    with pytest.raises(PokedexDataError) as excinfo:
        load_pokemon(path)
    message = str(excinfo.value)
    assert excinfo.value.line == 2
    assert "column" in message
    assert "Generation" in message


def test_missing_file_raises_data_error_naming_the_path(tmp_path):
    missing = tmp_path / "nope.csv"
    with pytest.raises(PokedexDataError) as excinfo:
        load_pokemon(missing)
    assert "nope.csv" in str(excinfo.value)
    assert excinfo.value.line is None


def test_empty_file_raises_data_error(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_text("", encoding="utf-8")
    with pytest.raises(PokedexDataError):
        load_pokemon(path)


def test_non_utf8_file_raises_data_error(tmp_path):
    path = tmp_path / "latin1.csv"
    path.write_bytes(
        (HEADER + '\n669,"Flabébé"," ","Fairy"," ",303,44,38,39,61,79,42,6\n').encode(
            "latin-1"
        )
    )
    with pytest.raises(PokedexDataError):
        load_pokemon(path)


def test_directory_path_raises_data_error_naming_the_path(tmp_path):
    # PTI-84
    folder = tmp_path / "not_a_csv"
    folder.mkdir()
    with pytest.raises(PokedexDataError) as excinfo:
        load_pokemon(folder)
    assert "not_a_csv" in str(excinfo.value)
    assert isinstance(excinfo.value.__cause__, OSError)


@pytest.mark.skipif(
    sys.platform == "win32" or os.geteuid() == 0,
    reason="file permissions can't make a file unreadable here",
)
def test_unreadable_file_raises_data_error_naming_the_path(tmp_path):
    # PTI-84
    path = write_csv(tmp_path, GOOD_ROW_1)
    path.chmod(0)
    try:
        with pytest.raises(PokedexDataError) as excinfo:
            load_pokemon(path)
    finally:
        path.chmod(0o644)
    assert "pokemon.csv" in str(excinfo.value)
    assert isinstance(excinfo.value.__cause__, PermissionError)


# =========================================================================
# Bundled data
# =========================================================================


def test_bundled_csv_ships_inside_the_package():
    import pokedex_tui

    path = Path(bundled_csv_path())
    package_dir = Path(pokedex_tui.__file__).parent
    assert path.is_file()
    assert path.name == "Pokemon.csv"
    assert path.parent.name == "data"
    assert package_dir in path.parents


def test_default_load_uses_the_bundled_csv(all_records):
    assert load_pokemon(bundled_csv_path()) == all_records


def test_bundled_csv_loads_from_any_working_directory(
    tmp_path, monkeypatch, all_records
):
    monkeypatch.chdir(tmp_path)
    assert load_pokemon() == all_records


# =========================================================================
# Real CSV: known facts
# =========================================================================


def test_real_csv_has_1215_records(all_records):
    assert len(all_records) == 1215


def test_real_csv_blank_counts(all_records):
    assert sum(r.form is None for r in all_records) == 985
    assert sum(r.type2 is None for r in all_records) == 546


def test_real_csv_has_no_single_space_values(all_records):
    for r in all_records:
        assert " " not in (r.form, r.type2)
        assert "" not in (r.form, r.type2)


def test_real_csv_keys_are_all_unique(all_records):
    assert len({r.key for r in all_records}) == 1215


def test_real_csv_totals_match_stat_sums(all_records):
    for r in all_records:
        assert r.total == sum(r.stats), r.key


def test_real_csv_types_are_all_known(all_records):
    for r in all_records:
        assert r.type1 in TYPES, r.key
        assert r.type2 is None or r.type2 in TYPES, r.key


def test_real_csv_uses_all_18_types(all_records):
    assert {r.type1 for r in all_records} == set(TYPES)


def test_real_csv_generations_are_1_to_9_and_all_present(all_records):
    assert {r.generation for r in all_records} == set(range(1, 10))


def test_real_csv_dex_numbers(all_records):
    counts = Counter(r.dex_id for r in all_records)
    assert len(counts) == 1025
    assert min(counts) == 1
    assert max(counts) == 1025
    assert sum(1 for n in counts.values() if n > 1) == 153


def test_real_csv_stat_extremes(all_records):
    assert min(r.hp for r in all_records) == 1
    assert max(max(r.stats) for r in all_records) == 255
    assert min(r.total for r in all_records) == 175
    assert max(r.total for r in all_records) == 1125


def test_real_csv_known_records(all_records):
    assert find(all_records, "Bulbasaur").types == ("Grass", "Poison")
    assert find(all_records, "Flabébé").dex_id == 669
    assert find(all_records, "Shedinja").hp == 1
    assert find(all_records, "Blissey").hp == 255

    mega_x = find(all_records, "Charizard", "Mega Charizard X")
    assert mega_x.display_name == "Mega Charizard X"
    assert mega_x.types == ("Fire", "Dragon")
    assert mega_x.generation == 6

    assert find(all_records, "Venusaur", "Mega Venusaur").generation == 6
    assert find(all_records, "Raichu", "Alolan Raichu").generation == 7


def test_real_csv_charizard_has_three_distinct_rows(all_records):
    charizards = [r for r in all_records if r.dex_id == 6]
    assert sorted(r.display_name for r in charizards) == [
        "Charizard",
        "Mega Charizard X",
        "Mega Charizard Y",
    ]
    assert len({r.key for r in charizards}) == 3


def test_real_csv_zygarde_rows_are_distinct(all_records):
    zygardes = [r for r in all_records if r.dex_id == 718]
    assert len(zygardes) == 3
    assert len({r.key for r in zygardes}) == 3


# =========================================================================
# Re-raised errors keep the original error as their cause (PTI-83)
# =========================================================================


def test_non_utf8_file_keeps_the_decode_error_as_cause(tmp_path):
    bad = tmp_path / "latin1.csv"
    bad.write_bytes("ID,Name\n1,Flabébé\n".encode("latin-1"))

    with pytest.raises(PokedexDataError) as info:
        load_pokemon(bad)

    assert isinstance(info.value.__cause__, UnicodeDecodeError)
