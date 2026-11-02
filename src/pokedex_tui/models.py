import dataclasses
from dataclasses import dataclass, field

TYPES: tuple[str, ...] = (
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
GENERATIONS: tuple[int, ...] = (1, 2, 3, 4, 5, 6, 7, 8, 9)
NO_SECOND_TYPE: str = "(single type)"
SORT_FIELDS: tuple[str, ...] = (
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
    sp_def: int
    speed: int
    total: int
    generation: int

    @property
    def display_name(self) -> str:
        if self.form and self.name in self.form:
            return self.form

        if self.form and self.name not in self.form:
            return f"{self.name} {self.form}"

        return self.name

    @property
    def types(self) -> tuple[str] | tuple[str, str]:
        return (self.type1, self.type2) if self.type2 else (self.type1,)

    @property
    def stats(self) -> tuple[int, ...]:
        return (
            self.hp,
            self.attack,
            self.defense,
            self.sp_atk,
            self.sp_def,
            self.speed,
        )

    @property
    def is_form(self) -> bool:
        return bool(self.form)

    @property
    def key(self) -> str:
        return f"{self.dex_id}|{self.name}|{self.form or ''}"


@dataclass(frozen=True)
class Criteria:
    """
    Search and filter criteria
    NOTE: None means to represent "Any" for type2 and NO_SECOND_TYPE means "single-type only"
    """

    search: str = field(default="")
    type1: str | None = field(default=None)
    type2: str | None = field(default=None)
    generations: frozenset[int] = field(default=frozenset([]))
    hide_forms: bool = field(default=False)

    @property
    def is_default(self) -> bool:
        return self == Criteria()

    def replace(self, **changes) -> Criteria:
        return dataclasses.replace(self, **changes)


@dataclass(frozen=True)
class SortOrder:
    """
    Sort order for the search bar
    """

    by: str = field(default="dex")
    descending: bool = field(default=False)

    @classmethod
    def for_field(cls, name: str = "dex"):
        """Returns new SortOrder by the given name"""
        if name not in SORT_FIELDS:
            raise ValueError(f"provided name: ({name}) is not recognized")

        if name == "dex" or name == "name":
            return cls(by=name, descending=False)

        return cls(by=name, descending=True)

    def flipped(self):
        """Returns the new SortOrder but with reverse sorting direction of the current one"""
        return SortOrder(by=self.by, descending=not self.descending)

    def next_field(self):
        for index, field_name in enumerate(SORT_FIELDS):
            if field_name == self.by:
                # wrap around to 0 if index + 1 equals the length of SORT_FIELDs
                next_index = (index + 1) % len(SORT_FIELDS)
                return SortOrder.for_field(SORT_FIELDS[next_index])


DEFAULT_SORT = SortOrder()
