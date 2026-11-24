// CI and releases for pokedex-tui (multibranch job, GitHub Branch Source).
//
// Every branch and pull request: lint, format check, type check and tests on macOS and
// Linux in parallel.
//   macOS   on the Mac mini agent (label "macos"). The agent is a separate, non-admin
//           "jenkins" user, so tools come from the shared Homebrew prefix: needs
//           `brew install uv`. uv fetches Python 3.14 itself from .python-version.
//   Linux   in a uv + Python 3.14 container on the controller (label "built-in").
//           HOME=/tmp: Jenkins runs the container as its own uid, which has no home in
//           the image, and HOME=$WORKSPACE would put uv's cache (full of .py files)
//           where ruff would lint it.
//
// main, once both pass: a release. python-semantic-release works out the next version
// from conventional commits since the last v* tag (feat -> minor, fix/perf -> patch,
// "!" or BREAKING CHANGE -> major), writes it into pyproject.toml in the workspace only,
// builds the wheel and sdist, tags the main commit vX.Y.Z and pushes just the tag.
// Jenkins archives dist/. No commits worth a release -> no-op.
//
// Tag only, never a commit: main's ruleset requires every change to come through a PR,
// so a release commit can't be pushed. The tag is the record of the version, and
// pyproject.toml on main keeps its placeholder 0.1.0.
//
// GITHUB_PAT needs Contents read/write on this repo (push the tag).

// Same checks on both platforms; mirrors what pre-commit runs locally, plus the tests.
def checks() {
    sh '''#!/bin/bash
        set -euo pipefail
        uv sync --locked --dev
        uv run ruff check .
        uv run ruff format --check .
        uv run pyright
        uv run pytest -n auto --junitxml=reports/junit.xml
    '''
}

pipeline {
    agent none

    options {
        timeout(time: 30, unit: 'MINUTES')
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '30'))
    }

    environment {
        UV_NO_PROGRESS = '1'
        // The uv cache (HOME=/tmp in the container) and the workspace are on different
        // filesystems, so uv can't hardlink; say so up front instead of warning every run.
        UV_LINK_MODE = 'copy'
    }

    stages {
        stage('Checks') {
            parallel {
                stage('macOS') {
                    agent { label 'macos' }
                    steps {
                        withEnv(['PATH+BREW=/opt/homebrew/bin:/opt/homebrew/sbin']) {
                            checks()
                        }
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'reports/junit.xml'
                            cleanWs()
                        }
                    }
                }
                stage('Linux') {
                    agent {
                        docker {
                            image 'ghcr.io/astral-sh/uv:python3.14-trixie'
                            label 'built-in'
                            args '-e HOME=/tmp'
                        }
                    }
                    steps {
                        checks()
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'reports/junit.xml'
                            cleanWs()
                        }
                    }
                }
            }
        }

        stage('Release') {
            when {
                beforeAgent true
                branch 'main'
            }
            agent {
                docker {
                    image 'ghcr.io/astral-sh/uv:python3.14-trixie'
                    label 'built-in'
                    args '-e HOME=/tmp'
                }
            }
            environment {
                // semantic-release reads GH_TOKEN and pushes the tag over HTTPS with it.
                GH_TOKEN = credentials('GITHUB_PAT')
                // Annotated tags need a tagger identity; the container has no git config.
                GIT_COMMIT_AUTHOR = 'semantic-release <semantic-release>'
                GIT_COMMITTER_NAME = 'semantic-release'
                GIT_COMMITTER_EMAIL = 'semantic-release'
            }
            steps {
                sh '''#!/bin/bash
                    set -euo pipefail
                    # A plain HTTPS remote, which semantic-release adds the token to for the push.
                    git remote set-url origin https://github.com/pinnheads/Pokedex-TUI.git
                    # Full history and every tag are needed to work out the next version.
                    if [ "$(git rev-parse --is-shallow-repository)" = "true" ]; then
                        git fetch -q --unshallow --tags --force origin
                    else
                        git fetch -q --tags --force origin
                    fi
                    # Jenkins checks out a detached HEAD; semantic-release only releases from a
                    # branch in its release groups, so put it on main.
                    git checkout -q -B main HEAD

                    # uvx, so semantic-release doesn't have to be in uv.lock.
                    # --no-commit: stamp the version and build, but tag the existing main commit
                    # and push only the tag (main rejects direct pushes).
                    uvx --from "python-semantic-release>=10,<11" semantic-release version \
                        --no-commit --no-changelog --no-vcs-release
                '''
                script {
                    def tag = sh(script: 'git describe --tags --exact-match HEAD 2>/dev/null || true',
                                 returnStdout: true).trim()
                    currentBuild.description = tag ? "Released ${tag}" : 'No release needed'
                }
            }
            post {
                success {
                    archiveArtifacts artifacts: 'dist/*', allowEmptyArchive: true, fingerprint: true
                }
                always { cleanWs() }
            }
        }
    }
}
