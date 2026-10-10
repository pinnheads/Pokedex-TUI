## Pokedex TUI

A terminal app for browsing Pokemon stats, with search and filters by name, type and generation. Built with Python and Textual, reading an offline CSV bundled with the app

## Pokemon Data

| Columns                                      | Meaning                        | Notes                                                                |
| -------------------------------------------- | ------------------------------ | -------------------------------------------------------------------- |
| ID                                           | National Dex Number            | Alternate forms get there own rows so not unique ID's and can repeat |
| Name                                         | Species name                   |                                                                      |
| Form                                         | Form name eg. "Mega Charizard" |                                                                      |
| Type 1                                       | Primary type                   | All pokemon have a primary type                                      |
| Type2                                        | Secondary type                 |                                                                      |
| HP, Attack, Defense, Sp. Atk, Sp. Def, Speed | Base Stats                     |                                                                      |
| Total                                        | Sum of the six base stats      |                                                                      |
| Generation                                   | 1 to 9                         |                                                                      |

## Project Structure

```
pokedex-tui/
├── pyproject.toml          project info, Textual dependency, launch command
├── README.md               screenshot, install steps, keybindings
├── src/
│   └── pokedex_tui/
│       ├── __main__.py     entry point, starts the app
│       ├── app.py          App class: bindings, theme, shared state
│       ├── data/
│       │   └── Pokemon.csv bundled offline data
│       ├── models.py       Pokémon record + filter criteria
│       ├── loader.py       read, clean and validate the CSV
│       ├── query.py        search, filter and sort (no Textual)
│       ├── theme.py        palette, type colours, stat bands
│       ├── screens/
│       │   ├── browser.py  main screen
│       │   ├── detail.py   full detail screen
│       │   └── help.py     keybinding overlay
│       ├── widgets/
│       │   ├── filter_bar.py
│       │   ├── results_table.py
│       │   ├── stats_panel.py
│       │   └── type_badge.py
│       └── styles/
│           └── app.tcss    layout and colours
└── tests/
    ├── fixtures/           small hand-made CSVs, incl. a broken one
    ├── test_loader.py      data tests
    ├── test_query.py       logic tests
    ├── test_ui.py          Textual pilot tests
    └── snapshots/          screenshot tests
```

## Getting Started

1. Clone the repository

```shell
git clone https://github.com/pinnheads/Pokedex-TUI.git
cd Pokedex-TUI
```

2. Start the app

```shell
uv run python -m pokedex_tui
```

## Acknowledgements

- CSV Data: [Igreski/pokemonData](https://github.com/lgreski/pokemonData)
