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


def test_display_name_is_form_name_when_the_form_contains_the_name(make_pokemon):
    p = make_pokemon(form="Mega Charizard X", type2="Dragon")
    assert p.display_name == "Mega Charizard X"


@pytest.mark.parametrize(
    ("name", "form", "expected"),
    [
        ("Nidoran", "Female", "Nidoran Female"),
        ("Castform", "Sunny Form", "Castform Sunny Form"),
        ("Darmanitan", "Zen Mode", "Darmanitan Zen Mode"),
        ("Darmanitan", "Galarian Zen Mode", "Darmanitan Galarian Zen Mode"),
    ],
)
def test_display_name_puts_the_name_first_when_the_form_lacks_it(
    make_pokemon, name, form, expected
):
    # C10: a form like "Female" alone does not say which Pokemon it is.
    assert make_pokemon(name=name, form=form).display_name == expected


@pytest.mark.parametrize(
    ("name", "form"),
    [
        ("Raichu", "Alolan Raichu"),
        ("Pikachu", "Partner Pikachu"),
        ("Greninja", "Ash-Greninja"),
    ],
)
def test_display_name_does_not_repeat_a_name_already_in_the_form(
    make_pokemon, name, form
):
    assert make_pokemon(name=name, form=form).display_name == form


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


def test_key_cannot_collide_when_spaces_move_between_name_and_form(make_pokemon):
    # PTI-85: "A B" + "C" and "A" + "B C" must not give the same key.
    one = make_pokemon(name="A B", form="C")
    two = make_pokemon(name="A", form="B C")
    assert one.key != two.key


def test_key_for_a_base_form_does_not_contain_the_text_none(make_pokemon):
    # PTI-85: a missing form is left empty, not written as "None".
    assert "None" not in make_pokemon(form=None).key


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
        setattr(c, "search", "pika")  # noqa: B010  pyright rejects a direct assignment


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


# --- Phase 4: SortOrder (PTI-22) --------------------------------------------
#
# Names these tests expect (rename here if you chose different ones):
# - SORT_FIELDS: the nine sort fields, in the order the s key cycles them.
#   The stat fields use the same names as the Pokemon fields.
# - SortOrder(by="dex", descending=False): an immutable sort choice.
#   SortOrder.for_field(name) gives that field at its default direction,
#   flipped() gives the other direction, next_field() gives the next field
#   in SORT_FIELDS at its default direction (back to "dex" after "speed").


def test_sort_fields_are_the_nine_in_cycle_order():
    from pokedex_tui.models import SORT_FIELDS

    assert SORT_FIELDS == (
        "dex",
        "name",
        "total",
        "hp",
        "attack",
        "defense",
        "sp_atk",
        "sp_def",
        "speed",
    )


def test_stat_sort_fields_are_pokemon_field_names(make_pokemon):
    from pokedex_tui.models import SORT_FIELDS

    charizard = make_pokemon()
    for name in SORT_FIELDS[2:]:
        assert isinstance(getattr(charizard, name), int), name


def test_default_sort_is_dex_ascending():
    from pokedex_tui.models import SortOrder

    order = SortOrder()

    assert order.by == "dex"
    assert order.descending is False


@pytest.mark.parametrize(
    ("name", "descending"),
    [
        ("dex", False),
        ("name", False),
        ("total", True),
        ("hp", True),
        ("attack", True),
        ("defense", True),
        ("sp_atk", True),
        ("sp_def", True),
        ("speed", True),
    ],
)
def test_each_field_starts_at_its_default_direction(name, descending):
    from pokedex_tui.models import SortOrder

    assert SortOrder.for_field(name) == SortOrder(by=name, descending=descending)


def test_for_field_rejects_an_unknown_field():
    from pokedex_tui.models import SortOrder

    with pytest.raises(ValueError):
        SortOrder.for_field("weight")


def test_flipped_gives_the_other_direction_and_leaves_the_original_alone():
    from pokedex_tui.models import SortOrder

    order = SortOrder.for_field("total")
    flipped = order.flipped()

    assert flipped == SortOrder(by="total", descending=False)
    assert order == SortOrder(by="total", descending=True)
    assert flipped.flipped() == order


def test_next_field_follows_the_cycle_and_wraps_round():
    from pokedex_tui.models import SORT_FIELDS, SortOrder

    order = SortOrder()
    seen = []
    for _ in SORT_FIELDS:
        seen.append(order.by)
        order = order.next_field()

    assert tuple(seen) == SORT_FIELDS
    assert order == SortOrder()


def test_next_field_starts_at_the_default_direction():
    from pokedex_tui.models import SortOrder

    # Name flipped to descending; the next field, Total, still starts
    # descending, and the one after, HP, too.
    order = SortOrder.for_field("name").flipped()

    assert order.next_field() == SortOrder(by="total", descending=True)
    assert order.next_field().flipped().next_field() == SortOrder(
        by="hp", descending=True
    )


def test_sort_order_is_immutable():
    from pokedex_tui.models import SortOrder

    with pytest.raises(dataclasses.FrozenInstanceError):
        SortOrder().descending = True  # type: ignore[misc]


def test_sort_order_compares_and_hashes_by_value():
    from pokedex_tui.models import SortOrder

    assert SortOrder() == SortOrder(by="dex", descending=False)
    assert len({SortOrder(), SortOrder(by="dex")}) == 1
    assert SortOrder() != SortOrder(by="dex", descending=True)
