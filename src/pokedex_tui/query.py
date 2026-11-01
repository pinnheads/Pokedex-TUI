import unicodedata
from collections.abc import Iterable, Mapping
from types import MappingProxyType

from pokedex_tui.models import (
    DEFAULT_SORT,
    NO_SECOND_TYPE,
    Criteria,
    Pokemon,
    SortOrder,
)


def default_sort_pokemon(
    unsorted_pokemon_data: Iterable[Pokemon],
) -> tuple[Pokemon, ...]:
    """Sorts Pokemon by Dex number, base form first"""
    return tuple(
        sorted(
            unsorted_pokemon_data,
            key=lambda pokemon: (pokemon.dex_id, pokemon.is_form),
        )
    )


def total_ranks(records: Iterable[Pokemon]) -> Mapping[str, int]:
    """
    Builds a lookup from each Pokemon's key to its rank by Total.
    Two equal totals share a rank.
    """
    # sort the data based on totals (reverse order)
    totals_sorted_data = sorted(
        records, key=lambda pokemon: pokemon.total, reverse=True
    )
    prev_pokemon: Pokemon | None = None
    ranks: dict[str, int] = {}
    current_rank = 1
    for pokemon in totals_sorted_data:
        # rank sharing logic
        if prev_pokemon is not None and pokemon.total == prev_pokemon.total:
            ranks[pokemon.key] = ranks[prev_pokemon.key]
        else:
            ranks[pokemon.key] = current_rank
        current_rank += 1
        prev_pokemon = pokemon

    return MappingProxyType(ranks)


def filter_and_sort(
    all_records: tuple[Pokemon, ...],
    criteria: Criteria,
    sort_in: SortOrder = DEFAULT_SORT,
):
    normalised_search = normalise(criteria.search)

    search_filtered_records = tuple(
        record
        for record in all_records
        if _match_search_and_record(record=record, search_text=normalised_search)
        and _match_type_and_record(record=record, criteria=criteria)
    )

    return default_sort_pokemon(search_filtered_records)


def normalise(pokemon_name: str) -> str:
    """
    Normalise pokemon name strings, "Flabébé" becomes "flabebe"
    """
    # lower case
    stripped_case_folded_name = pokemon_name.casefold()
    # remove character accents
    nfkd_form = unicodedata.normalize("NFKD", stripped_case_folded_name)
    accent_removed = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    # remove special characters while keeping digits and spaces
    special_char_removed = "".join(
        [c for c in accent_removed if c.isalnum() or c.isspace()]
    )
    return special_char_removed.strip()


def _match_search_and_record(record: Pokemon, search_text: str) -> bool:
    # empty search
    if not search_text:
        return True

    # search text in pokemon name
    if search_text in normalise(record.name):
        return True

    # search text in pokemon form
    return bool(record.form and search_text in normalise(record.form))


def _match_type_and_record(record: Pokemon, criteria: Criteria) -> bool:
    # both slots none
    if not criteria.type1 and not criteria.type2:
        return True

    # either slot set or both slot same
    if (
        (criteria.type1 and criteria.type1 in record.types)
        or (criteria.type2 and criteria.type2 in record.types)
        or (criteria.type1 == criteria.type2 and criteria.type1 in record.types)
    ):
        return True

    # both slot set and both in record
    if (
        (criteria.type1 and criteria.type2)
        and (criteria.type1 in record.types)
        and (criteria.type2 in record.types)
    ):
        return True

    # a type plus NO_SECOND_TYPE
    if (
        criteria.type1
        and criteria.type2 == NO_SECOND_TYPE
        and criteria.type1 == record.type1
        and record.type2 == None
    ) or (
        criteria.type1 == NO_SECOND_TYPE
        and criteria.type2
        and criteria.type2 == record.type2
        and record.type1 == None
    ):
        return True

    return bool(
        criteria.type1 == None
        and criteria.type2 == NO_SECOND_TYPE
        or (criteria.type1 == NO_SECOND_TYPE and criteria.type2 == None)
        and len(record.types) == 1
    )
