<a href="https://jenkins.utsavdeep.com/job/pokedex-tui/job/main/">
        <img alt="Build" src="https://jenkins.utsavdeep.com/buildStatus/icon?job=pokedex-tui%2Fmain&style=plastic&subject=main" />
</a>

## Pokedex TUI

A terminal app for browsing Pokemon stats, with search and filters by name, type and generation. Built with Python and Textual, reading an offline CSV bundled with the app

## Pokemon Data

| Columns                                      | Meaning                        | Notes                                                                |
| -------------------------------------------- | ------------------------------ | -------------------------------------------------------------------- |
| ID                                           | National Dex Number            | Alternate forms get their own rows so not unique ID's and can repeat |
| Name                                         | Species name                   |                                                                      |
| Form                                         | Form name eg. "Mega Charizard" |                                                                      |
| Type1                                        | Primary type                   | All pokemon have a primary type                                      |
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

## CI and Releases

CI runs on Jenkins (see `Jenkinsfile`):

- **Every branch and pull request:** `ruff check`, `ruff format --check`, `pyright` and `pytest` run in parallel on macOS (the `macos` agent) and Linux (a uv + Python 3.14 container on the controller).
- **Merges to `main`:** after the same checks pass, [python-semantic-release](https://python-semantic-release.readthedocs.io/) picks the next version from conventional commits (`feat` → minor, `fix`/`perf` → patch, `!`/`BREAKING CHANGE` → major). It tags the tested `main` commit `vX.Y.Z`, and Jenkins archives the wheel and sdist built with that version. Releases are tag-only: nothing is committed to `main`, so `pyproject.toml` keeps its placeholder version and the `v*` tags are the version history.

The macOS agent needs `uv` from Homebrew. The release stage pushes with the `GITHUB_PAT` Jenkins credential, which needs Contents read/write on this repo. To preview the next version locally:

```sh
uvx --from "python-semantic-release>=10,<11" semantic-release --noop version --print
```

## Acknowledgements

- CSV Data: [Igreski/pokemonData](https://github.com/lgreski/pokemonData)
