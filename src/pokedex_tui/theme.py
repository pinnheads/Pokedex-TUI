from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from textual.theme import Theme


@dataclass(frozen=True)
class Interface:
    """Interface Colors"""

    background: str = "#1c1c1c"
    surface: str = "#262626"
    raised: str = "#303030"
    border: str = "#444444"
    text: str = "#e4e4e4"
    muted_text: str = "#9e9e9e"
    accent: str = "#ffd75f"
    key_cap_text: str = "#121212"
    selection: str = "#005f87"
    selection_text: str = "#eeeeee"
    header_bar: str = "#af0000"
    header_text: str = "#eeeeee"
    bar_track: str = "#4e4e4e"
    error: str = "#ff5f5f"
    success: str = "#87d787"


PALETTE = Interface()


@dataclass(frozen=True)
class TypeStyle:
    """How one type's badge is drawn"""

    badge: str
    text: str


DARK_TEXT: str = PALETTE.key_cap_text
LIGHT_TEXT: str = PALETTE.selection_text

TYPE_STYLES: Mapping[str, TypeStyle] = MappingProxyType(
    {
        "Normal": TypeStyle(badge="#afaf87", text=DARK_TEXT),
        "Fire": TypeStyle(badge="#ff8700", text=DARK_TEXT),
        "Water": TypeStyle(badge="#5f87ff", text=DARK_TEXT),
        "Electric": TypeStyle(badge="#ffd700", text=DARK_TEXT),
        "Grass": TypeStyle(badge="#87d75f", text=DARK_TEXT),
        "Ice": TypeStyle(badge="#87d7d7", text=DARK_TEXT),
        "Fighting": TypeStyle(badge="#d70000", text=LIGHT_TEXT),
        "Poison": TypeStyle(badge="#af5faf", text=DARK_TEXT),
        "Ground": TypeStyle(badge="#d7af5f", text=DARK_TEXT),
        "Flying": TypeStyle(badge="#af87ff", text=DARK_TEXT),
        "Psychic": TypeStyle(badge="#ff5f87", text=DARK_TEXT),
        "Bug": TypeStyle(badge="#afaf00", text=DARK_TEXT),
        "Rock": TypeStyle(badge="#af8700", text=DARK_TEXT),
        "Ghost": TypeStyle(badge="#5f5f87", text=LIGHT_TEXT),
        "Dragon": TypeStyle(badge="#5f00ff", text=LIGHT_TEXT),
        "Dark": TypeStyle(badge="#875f5f", text=LIGHT_TEXT),
        "Steel": TypeStyle(badge="#afafd7", text=DARK_TEXT),
        "Fairy": TypeStyle(badge="#ffafd7", text=DARK_TEXT),
    }
)

STAT_BANDS: tuple[tuple[int, str], ...] = (
    (0, "#ff5f5f"),
    (60, "#ffaf00"),
    (90, "#5fafff"),
    (120, "#afffff"),
)

SCALE_MAX: int = 255
BAR_WIDTH: int = 18

APP_THEME: Theme = Theme(
    name="pokedex",
    primary=PALETTE.accent,
    accent=PALETTE.accent,
    secondary=PALETTE.selection,
    warning=PALETTE.accent,
    error=PALETTE.error,
    success=PALETTE.success,
    foreground=PALETTE.text,
    background=PALETTE.background,
    surface=PALETTE.surface,
    panel=PALETTE.raised,
    dark=True,
    ansi=False,
    variables={
        # our own variables
        "header-bar": PALETTE.header_bar,
        "header-text": PALETTE.header_text,
        "key-cap-text": PALETTE.key_cap_text,
        "selection": PALETTE.selection,
        "selection-text": PALETTE.selection_text,
        "bar-track": PALETTE.bar_track,
        "raised": PALETTE.raised,
        # override textual defaults
        "text": PALETTE.text,
        "text-muted": PALETTE.muted_text,
        "border": PALETTE.accent,
        "border-blurred": PALETTE.border,
        "block-cursor-background": PALETTE.selection,
        "block-cursor-foreground": PALETTE.selection_text,
        "block-cursor-blurred-background": PALETTE.selection,
        "block-cursor-blurred-foreground": PALETTE.selection_text,
        "block-hover-background": PALETTE.background,
        "footer-background": PALETTE.raised,
        "footer-item-background": PALETTE.raised,
        "footer-key-background": PALETTE.accent,
        "footer-key-foreground": PALETTE.key_cap_text,
        "footer-description-background": PALETTE.raised,
        "footer-description-foreground": PALETTE.text,
        "input-cursor-background": PALETTE.text,
        "input-cursor-foreground": PALETTE.background,
        "input-selection-background": PALETTE.selection,
        "input-selection-foreground": PALETTE.selection_text,
        "scrollbar-background": PALETTE.background,
        "scrollbar": PALETTE.border,
        "scrollbar-active": PALETTE.border,
        "scrollbar-hover": PALETTE.border,
        "scrollbar-corner-color": PALETTE.background,
        "surface-active": PALETTE.surface,
    },
)
