from pokedex_tui.models import Pokemon


def default_sort_pokemon(unsorted_pokemon_data) -> list[Pokemon]:
    return sorted(
        unsorted_pokemon_data,
        key=lambda pokemon: (pokemon.dex_id, pokemon.is_form),
    )
