"""Phase 1: the Pokemon record and the filter Criteria value."""

import dataclasses

import pytest

from pokedex_tui.models import GENERATIONS, NO_SECOND_TYPE, TYPES, Criteria

# --- Constants -------------------------------------------------------------


def test_types_lists_all_18_types_once():
    assert len(TYPES) == 18
    assert len(set(TYPES)) == 18
    assert set(TYPES) == {
        "Bug",
        "Dark",
        "Dragon",
        "Electric",
        "Fairy",
        "Fighting",
        "Fire",
        "Flying",
        "Ghost",
        "Grass",
        "Ground",
        "Ice",
        "Normal",
        "Poison",
        "Psychic",
        "Rock",
        "Steel",
        "Water",
    }


def test_types_is_immutable():
    assert isinstance(TYPES, tuple)


def test_generations_are_one_to_nine_in_order():
    assert tuple(GENERATIONS) == (1, 2, 3, 4, 5, 6, 7, 8, 9)


def test_no_second_type_is_not_a_real_type():
    assert NO_SECOND_TYPE not in TYPES
    assert NO_SECOND_TYPE is not None


# --- Pokemon: fields --------------------------------------------------------


def test_pokemon_keeps_its_fields(make_pokemon):
    p = make_pokemon()
    assert p.dex_id == 6
    assert p.name == "Charizard"
    assert p.form is None
    assert p.type1 == "Fire"
    assert p.type2 == "Flying"
    assert (p.hp, p.attack, p.defense, p.sp_atk, p.sp_def, p.speed) == (
        78,
        84,
        78,
        109,
        85,
        100,
    )
    assert p.total == 534
    assert p.generation == 1


def test_pokemon_is_immutable(make_pokemon):
    p = make_pokemon()
    with pytest.raises((AttributeError, dataclasses.FrozenInstanceError, TypeError)):
        p.name = "Blastoise"


def test_pokemon_compares_and_hashes_by_value(make_pokemon):
    a = make_pokemon()
    b = make_pokemon()
    assert a == b
    assert hash(a) == hash(b)
    assert len({a, b}) == 1


# --- Pokemon: derived values ------------------------------------------------


def test_display_name_is_species_name_without_a_form(make_pokemon):
    assert make_pokemon().display_name == "Charizard"


def test_display_name_is_form_name_when_there_is_a_form(make_pokemon):
    p = make_pokemon(form="Mega Charizard X", type2="Dragon")
    assert p.display_name == "Mega Charizard X"


def test_types_has_both_types_in_slot_order(make_pokemon):
    assert make_pokemon().types == ("Fire", "Flying")


def test_types_has_one_entry_for_single_type(make_pokemon):
    p = make_pokemon(name="Charmander", dex_id=4, type2=None)
    assert p.types == ("Fire",)


def test_stats_are_the_six_base_stats_in_display_order(make_pokemon):
    # HP, Attack, Defense, Sp. Atk, Sp. Def, Speed
    assert make_pokemon().stats == (78, 84, 78, 109, 85, 100)


def test_is_form_false_for_base_record(make_pokemon):
    assert make_pokemon().is_form is False


def test_is_form_true_when_form_is_set(make_pokemon):
    assert make_pokemon(form="Mega Charizard Y").is_form is True


# --- Pokemon: unique key ----------------------------------------------------


def test_key_is_a_string(make_pokemon):
    assert isinstance(make_pokemon().key, str)


def test_key_is_stable_for_equal_records(make_pokemon):
    assert make_pokemon().key == make_pokemon().key


def test_key_differs_between_base_and_form_of_same_dex_number(make_pokemon):
    base = make_pokemon()
    mega = make_pokemon(form="Mega Charizard X", type2="Dragon")
    assert base.key != mega.key


def test_key_differs_between_two_forms_of_same_dex_number(make_pokemon):
    x = make_pokemon(form="Mega Charizard X")
    y = make_pokemon(form="Mega Charizard Y")
    assert x.key != y.key


def test_key_differs_when_only_the_name_differs(make_pokemon):
    # The real CSV puts some forms in Name with a blank Form (Zygarde 10% / 50%),
    # so Dex number plus form alone is not enough to tell rows apart.
    fifty = make_pokemon(dex_id=718, name="Zygarde50% Forme", form=None)
    ten = make_pokemon(dex_id=718, name="Zygarde10% Forme", form=None)
    assert fifty.key != ten.key


def test_key_differs_when_only_the_dex_number_differs(make_pokemon):
    assert make_pokemon(dex_id=6).key != make_pokemon(dex_id=7).key


# --- Criteria ---------------------------------------------------------------


def test_default_criteria_filter_nothing():
    c = Criteria()
    assert c.search == ""
    assert c.type1 is None
    assert c.type2 is None
    assert c.generations == frozenset()
    assert c.hide_forms is False


def test_default_criteria_report_themselves_as_default():
    assert Criteria().is_default is True


@pytest.mark.parametrize(
    "changes",
    [
        {"search": "char"},
        {"type1": "Fire"},
        {"type2": "Flying"},
        {"type2": NO_SECOND_TYPE},
        {"generations": frozenset({6})},
        {"hide_forms": True},
    ],
)
def test_any_set_criterion_is_not_default(changes):
    assert Criteria(**changes).is_default is False


def test_generations_hold_a_set_of_allowed_values():
    c = Criteria(generations=frozenset({1, 2, 3}))
    assert c.generations == frozenset({1, 2, 3})
    assert isinstance(c.generations, frozenset)


def test_criteria_are_immutable():
    c = Criteria()
    with pytest.raises((AttributeError, dataclasses.FrozenInstanceError, TypeError)):
        c.search = "pika"


def test_criteria_compare_and_hash_by_value():
    a = Criteria(search="char", type1="Fire", generations=frozenset({1}))
    b = Criteria(search="char", type1="Fire", generations=frozenset({1}))
    assert a == b
    assert hash(a) == hash(b)


def test_replace_returns_new_criteria_and_leaves_original_alone():
    original = Criteria(search="char")
    changed = original.replace(type1="Fire")
    assert changed == Criteria(search="char", type1="Fire")
    assert original == Criteria(search="char")
    assert changed is not original


def test_replace_with_no_changes_gives_equal_criteria():
    c = Criteria(type1="Water")
    assert c.replace() == c
