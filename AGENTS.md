# AGENTS.md

## CI (Jenkins, `Jenkinsfile`)

One multibranch job, `pokedex-tui`. `Jenkinsfile` is the only CI; there are no GitHub
Actions in this repo. Every branch and PR runs the same checks; only `main` releases:
- **any branch / PR** → `uv sync --locked --dev`, `ruff check`, `ruff format --check`,
  `pyright`, `pytest -n auto`. JUnit results show in Jenkins' test report.
- **main** → the same checks, then **Release**.

The checks run in parallel on:

| Stage | Where |
|---|---|
| macOS | the Mac mini agent (`macos`). Non-admin `jenkins` user, so `uv` comes from the shared Homebrew prefix (`/opt/homebrew/bin`). uv fetches Python 3.14 from `.python-version`. |
| Linux | `ghcr.io/astral-sh/uv:python3.14-trixie` on the controller (`built-in`), with `HOME=/tmp`. Not `HOME=$WORKSPACE`: uv's cache would land in the workspace and ruff would lint it. The image has no Node.js, which is why the dev dependency is `pyright[nodejs]`: without that extra, pyright tries to download Node itself through `nodeenv`, and that fails in the container. |

**Release** runs in the same Linux container. It calls python-semantic-release via `uvx`, so it isn't in `uv.lock`. The config lives under `[tool.semantic_release]` in `pyproject.toml`. Semantic-release:
1. Works out the next version from conventional commits since the last `v*` tag: `feat:` → minor, `fix:`/`perf:` → patch, `!` or `BREAKING CHANGE` → major. `chore:` and other types don't release, so a main build with none of those is a no-op.
2. Writes that version into `pyproject.toml` **in the Jenkins workspace only** and runs `uv build`, so the wheel and sdist carry it.
3. Tags the main commit that was just tested `vX.Y.Z` and pushes **only the tag** over HTTPS with the `GITHUB_PAT` credential (Contents read/write on this repo: tag, release and uploads).
4. Creates the GitHub release for that tag and uploads the wheel and sdist to it (`semantic-release publish`). The notes are generated from the commits since the previous tag, grouped by type (Features, Bug Fixes, …). The first release, `v0.1.0`, just says "Initial Release".

If the latest tag has no GitHub release, a main build with nothing new to release creates it. That covers `v0.1.0`, which was tagged before releases were turned on, and any run that pushed a tag and then failed. The tag's code is built at its version in a temporary `git worktree`, and the release is created with `semantic-release changelog --post-to-release-tag`.

**Releases are tag-only. Nothing is ever committed to main.** main's ruleset requires every change to go through a PR, so a release commit is rejected (`GH013`). The `v*` tags are the version history. `project.version` in `pyproject.toml` stays at its placeholder `0.1.0` on main, so don't bump it by hand: semantic-release ignores it and reads the tags. There is no `CHANGELOG.md`.

Jenkins also archives `dist/*` on the build. There is no PyPI upload.

Preview the next version locally:

```sh
uvx --from "python-semantic-release>=10,<11" semantic-release --noop version --print
```

## Conventions

- Commits: conventional prefix (`feat:` / `fix:` / `chore:`), lowercase, one line. The
  prefix decides the release, so a user-visible change must not hide behind `chore:`.
