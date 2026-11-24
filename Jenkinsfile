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
// "!" or BREAKING CHANGE -> major), bumps pyproject.toml and uv.lock, updates
// CHANGELOG.md, builds the wheel and sdist, commits "chore(release): X.Y.Z", tags
// vX.Y.Z and pushes both. Jenkins archives dist/. No commits worth a release -> no-op.
//
// GITHUB_PAT needs Contents read/write on this repo (push the release commit and tag).

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
    }

    stages {
        stage('Guard') {
            // The release commit this pipeline pushes to main must not set off another release.
            when { branch 'main' }
            agent { label 'built-in' }
            steps {
                script {
                    def subject = sh(script: 'git log -1 --pretty=%s', returnStdout: true).trim()
                    if (subject.startsWith('chore(release):')) {
                        env.SKIP_BUILD = 'true'
                        currentBuild.result = 'NOT_BUILT'
                        currentBuild.description = "Skipped: ${subject}"
                        echo "Release commit (${subject}); nothing to do."
                    }
                }
            }
            post {
                always { cleanWs() }
            }
        }

        stage('Checks') {
            when { not { environment name: 'SKIP_BUILD', value: 'true' } }
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
                allOf {
                    branch 'main'
                    not { environment name: 'SKIP_BUILD', value: 'true' }
                }
            }
            agent {
                docker {
                    image 'ghcr.io/astral-sh/uv:python3.14-trixie'
                    label 'built-in'
                    args '-e HOME=/tmp'
                }
            }
            environment {
                // semantic-release reads GH_TOKEN and pushes over HTTPS with it.
                GH_TOKEN = credentials('GITHUB_PAT')
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
                    # Jenkins checks out a detached HEAD; semantic-release needs to be on main.
                    git checkout -q -B main HEAD
                    git branch -q --set-upstream-to=origin/main main

                    # uvx, so semantic-release doesn't have to be in uv.lock.
                    uvx --from "python-semantic-release>=10,<11" semantic-release version --no-vcs-release
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
