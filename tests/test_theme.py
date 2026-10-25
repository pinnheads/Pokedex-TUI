"""Phase 3 C1 (PTI-51): the colour palette in theme.py.

Checks main-screen.md section 6, point 2: every colour sits exactly on the
256-colour grid, every type has a style, and every text pair meets 4.5:1.

Names these tests expect (rename here if you chose different ones):
- PALETTE: the one Interface instance, with a field per role.
- TYPE_STYLES: a read-only mapping from type name to TypeStyle(badge, text).
- DARK_TEXT, LIGHT_TEXT: the two badge text colours.
- STAT_BANDS: (lower limit, colour) pairs in ascending order.
- SCALE_MAX, BAR_WIDTH.
"""

import dataclasses

import pytest

from pokedex_tui.models import TYPES
from pokedex_tui.theme import (
    BAR_WIDTH,
    DARK_TEXT,
    LIGHT_TEXT,
    PALETTE,
    SCALE_MAX,
    STAT_BANDS,
    TYPE_STYLES,
)

# --- Helpers ---------------------------------------------------------------

CUBE_LEVELS = {0x00, 0x5F, 0x87, 0xAF, 0xD7, 0xFF}
GREY_RAMP = {0x08 + 10 * i for i in range(24)}  # 08, 12, 1c ... ee


def rgb(hex_colour):
    assert len(hex_colour) == 7 and hex_colour.startswith("#"), hex_colour
    return tuple(int(hex_colour[i : i + 2], 16) for i in (1, 3, 5))


def on_256_grid(hex_colour):
    r, g, b = rgb(hex_colour)
    in_cube = {r, g, b} <= CUBE_LEVELS
    on_ramp = r == g == b and r in GREY_RAMP
    return in_cube or on_ramp


def luminance(hex_colour):
    def channel(value):
        c = value / 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(v) for v in rgb(hex_colour))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(foreground, background):
    light, dark = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


def all_colours():
    colours = {
        f"PALETTE.{f.name}": getattr(PALETTE, f.name)
        for f in dataclasses.fields(PALETTE)
    }
    for name, style in TYPE_STYLES.items():
        colours[f"TYPE_STYLES[{name!r}].badge"] = style.badge
        colours[f"TYPE_STYLES[{name!r}].text"] = style.text
    for limit, colour in STAT_BANDS:
        colours[f"STAT_BANDS[{limit}]"] = colour
    return colours


# --- Interface palette -----------------------------------------------------

EXPECTED_INTERFACE = {
    "background": "#1c1c1c",
    "surface": "#262626",
    "raised": "#303030",
    "border": "#444444",
    "text": "#e4e4e4",
    "muted_text": "#9e9e9e",
    "accent": "#ffd75f",
    "key_cap_text": "#121212",
    "selection": "#005f87",
    "selection_text": "#eeeeee",
    "header_bar": "#af0000",
    "header_text": "#eeeeee",
    "bar_track": "#4e4e4e",
    "error": "#ff5f5f",
    "success": "#87d787",
}


def test_palette_has_exactly_the_15_roles():
    names = {f.name for f in dataclasses.fields(PALETTE)}
    assert names == set(EXPECTED_INTERFACE)


def test_palette_values_match_table_2_1():
    actual = {
        f.name: getattr(PALETTE, f.name).lower() for f in dataclasses.fields(PALETTE)
    }
    assert actual == EXPECTED_INTERFACE


def test_palette_is_immutable():
    with pytest.raises(dataclasses.FrozenInstanceError):
        PALETTE.background = "#000000"  # type: ignore[misc]


# Text-on-background pairs from table 2.1.
INTERFACE_PAIRS = [
    ("text", "background"),
    ("text", "raised"),
    ("text", "surface"),
    ("muted_text", "background"),
    ("muted_text", "raised"),
    ("accent", "background"),
    ("accent", "raised"),
    ("key_cap_text", "accent"),
    ("selection_text", "selection"),
    ("header_text", "header_bar"),
    ("error", "background"),
    ("success", "background"),
]


@pytest.mark.parametrize(("foreground", "background"), INTERFACE_PAIRS)
def test_interface_text_pairs_meet_4_5_to_1(foreground, background):
    ratio = contrast(getattr(PALETTE, foreground), getattr(PALETTE, background))
    assert ratio >= 4.5, f"{foreground} on {background} is only {ratio:.2f}:1"


# --- Type badges -----------------------------------------------------------

EXPECTED_TYPES = {
    "Normal": ("#afaf87", "dark"),
    "Fire": ("#ff8700", "dark"),
    "Water": ("#5f87ff", "dark"),
    "Electric": ("#ffd700", "dark"),
    "Grass": ("#87d75f", "dark"),
    "Ice": ("#87d7d7", "dark"),
    "Fighting": ("#d70000", "light"),
    "Poison": ("#af5faf", "dark"),
    "Ground": ("#d7af5f", "dark"),
    "Flying": ("#af87ff", "dark"),
    "Psychic": ("#ff5f87", "dark"),
    "Bug": ("#afaf00", "dark"),
    "Rock": ("#af8700", "dark"),
    "Ghost": ("#5f5f87", "light"),
    "Dragon": ("#5f00ff", "light"),
    "Dark": ("#875f5f", "light"),
    "Steel": ("#afafd7", "dark"),
    "Fairy": ("#ffafd7", "dark"),
}


def test_badge_text_colours_come_from_the_palette():
    assert PALETTE.key_cap_text == DARK_TEXT
    assert PALETTE.selection_text == LIGHT_TEXT


def test_every_type_has_a_style_and_no_extras():
    assert set(TYPE_STYLES) == set(TYPES)


def test_type_styles_match_table_2_2():
    text_for = {"dark": DARK_TEXT, "light": LIGHT_TEXT}
    for name, (badge, text) in EXPECTED_TYPES.items():
        style = TYPE_STYLES[name]
        assert style.badge.lower() == badge, name
        assert style.text == text_for[text], name


def test_type_styles_are_read_only():
    with pytest.raises(TypeError):
        TYPE_STYLES["Fire"] = TYPE_STYLES["Water"]  # type: ignore[index]


def test_a_type_style_is_immutable():
    with pytest.raises(dataclasses.FrozenInstanceError):
        TYPE_STYLES["Fire"].badge = "#000000"  # type: ignore[misc]


@pytest.mark.parametrize("name", sorted(EXPECTED_TYPES))
def test_badge_text_meets_4_5_to_1(name):
    style = TYPE_STYLES[name]
    ratio = contrast(style.text, style.badge)
    assert ratio >= 4.5, f"{name} badge text is only {ratio:.2f}:1"


# --- Stat bands and bar ----------------------------------------------------


def test_stat_bands_match_table_2_3():
    assert [(limit, colour.lower()) for limit, colour in STAT_BANDS] == [
        (0, "#ff5f5f"),
        (60, "#ffaf00"),
        (90, "#5fafff"),
        (120, "#afffff"),
    ]


def test_stat_bands_start_at_0_and_ascend():
    limits = [limit for limit, _ in STAT_BANDS]
    assert limits[0] == 0
    assert limits == sorted(set(limits))


def test_stat_bands_are_immutable():
    assert isinstance(STAT_BANDS, tuple)
    assert all(isinstance(band, tuple) for band in STAT_BANDS)


def test_bar_scale_and_width():
    assert SCALE_MAX == 255
    assert BAR_WIDTH == 18


# --- The 256-colour grid (Rule 1) ------------------------------------------


@pytest.mark.parametrize(("where", "colour"), sorted(all_colours().items()))
def test_every_colour_is_on_the_256_grid(where, colour):
    assert on_256_grid(colour), f"{where} = {colour} is off the 256-colour grid"
