from collections.abc import Iterable

from pokedex_tui.models import Pokemon


def default_sort_pokemon(
    unsorted_pokemon_data: Iterable[Pokemon],
) -> tuple[Pokemon, ...]:
    return tuple(
        sorted(
            unsorted_pokemon_data,
            key=lambda pokemon: (pokemon.dex_id, pokemon.is_form),
        )
    )
