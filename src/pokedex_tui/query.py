from collections.abc import Iterable, Mapping
from types import MappingProxyType

from pokedex_tui.models import Pokemon


def default_sort_pokemon(
    unsorted_pokemon_data: Iterable[Pokemon],
) -> tuple[Pokemon, ...]:
    """Sorts a iterable list of pokemons by dex id and form"""
    return tuple(
        sorted(
            unsorted_pokemon_data,
            key=lambda pokemon: (pokemon.dex_id, pokemon.is_form),
        )
    )


def total_ranks(records: Iterable[Pokemon]) -> Mapping[str, int]:
    """
    Builds a look from each Pokemon's key to its rank by Total.
    Two equal totals share a rank.
    """
    # sort the data based on totals (reverse order)
    totals_sorted_data = sorted(
        records, key=lambda pokemon: pokemon.total, reverse=True
    )
    prev_pokemon: Pokemon | None = None
    ranks: Mapping[str, int] = {}
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
