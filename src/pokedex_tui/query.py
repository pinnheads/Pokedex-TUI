from collections.abc import Iterable, Mapping
from types import MappingProxyType
import unicodedata

from pokedex_tui.models import DEFAULT_SORT, Criteria, Pokemon, SortOrder


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
    if len(all_records) == 0:
        return ()
    return all_records


def normalise(pokemon_name: str) -> str:
    """
    Normalise pokemon name strings, "Flabébé" becomes "flabebe"
    """
    # strip out spaces and lower case
    stripped_case_folded_name = pokemon_name.strip().casefold()
    # remove character accents
    nfkd_form = unicodedata.normalize("NFKD", stripped_case_folded_name)
    accent_removed = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    # remove special characters while keeping digits and spaces
    special_char_removed = "".join(
        [c for c in accent_removed if c.isdigit() or c.isalnum() or c.isspace()]
    )
    return special_char_removed
