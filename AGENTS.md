# AGENTS.md

## CI (Jenkins, `Jenkinsfile`)

One multibranch job, `pokedex-tui`. `Jenkinsfile` is the only CI; there are no GitHub
Actions in this repo. Every branch and PR runs the same checks; only `main` releases:
- **any branch / PR** → `uv sync --locked --dev`, `ruff check`, `ruff format --check`,
  `pyright`, `pytest -n auto`. JUnit results show in Jenkins' test report.
- **main** → the same checks, then **Release**. A push that starts with
  `chore(release):` is the pipeline's own release commit and ends `NOT_BUILT` at the
  Guard stage, so it never releases twice.

The checks run in parallel on:

| Stage | Where |
|---|---|
| macOS | the Mac mini agent (`macos`). Non-admin `jenkins` user, so `uv` comes from the shared Homebrew prefix (`/opt/homebrew/bin`). uv fetches Python 3.14 from `.python-version`. |
| Linux | `ghcr.io/astral-sh/uv:python3.14-trixie` on the controller (`built-in`), with `HOME=/tmp`. Not `HOME=$WORKSPACE`: uv's cache would land in the workspace and ruff would lint it. The image has no Node.js, which is why the dev dependency is `pyright[nodejs]`: without that extra, pyright tries to download Node itself through `nodeenv`, and that fails in the container. |

**Release** runs in the same Linux container. It calls python-semantic-release via `uvx`, so it isn't in `uv.lock`. The config lives under `[tool.semantic_release]` in `pyproject.toml`. Semantic-release:
1. Works out the next version from conventional commits since the last `v*` tag: `feat:` → minor, `fix:`/`perf:` → patch, `!` or `BREAKING CHANGE` → major. `chore:` and other types don't release, so a main build with none of those is a no-op.
2. Bumps `pyproject.toml`, re-locks `uv.lock` (it holds the project's own version, and `uv sync --locked` fails without it), and updates `CHANGELOG.md`.
3. Builds the wheel and sdist, commits `chore(release): X.Y.Z`, and tags `vX.Y.Z`.
4. Pushes the commit and the tag over HTTPS with the `GITHUB_PAT` credential (Contents read/write on this repo).

Jenkins archives `dist/*`. There is no GitHub release and no PyPI upload. The version is
never bumped by hand, so don't edit `project.version` or `CHANGELOG.md` in a PR.

Preview the next version locally:

```sh
uvx --from "python-semantic-release>=10,<11" semantic-release --noop version --print
```

## Conventions

- Commits: conventional prefix (`feat:` / `fix:` / `chore:`), lowercase, one line. The
  prefix decides the release, so a user-visible change must not hide behind `chore:`.
