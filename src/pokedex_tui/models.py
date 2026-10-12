from dataclasses import dataclass

TYPES = (
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
)
GENERATIONS = [1, 2, 3, 4, 5, 6, 7, 8, 9]
NO_SECOND_TYPE = "NA"


@dataclass(frozen=True)
class Pokemon:
    """Class for Pokemon Data"""

    dex_id: int
    name: str
    form: str | None
    type1: str
    type2: str | None
    hp: int
    attack: int
    defense: int
    sp_atk: int
    speed: int
    total: int
    generation: int


@dataclass(frozen=True)
class Criteria:
    pass
