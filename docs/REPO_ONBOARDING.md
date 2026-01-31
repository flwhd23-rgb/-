# Codebase onboarding (current state)

## Current structure

At the moment, the repository contains only a placeholder file (`.gitkeep`) and no
source code or application structure beyond the Git metadata directory. This
means there is no established module layout or runtime entry point yet.

## Important notes

- The codebase is effectively empty right now, so there are no build, runtime,
  or dependency conventions to follow.
- The only tracked file is the empty `.gitkeep` placeholder, which exists to
  keep the repository directory present in version control.

## Suggested next learning steps

1. Confirm the intended project type (e.g., service, library, web app) and
   decide on a base structure (e.g., `src/`, `tests/`, `docs/`).
2. Create a `README.md` that documents setup, tooling, and local dev workflows.
3. Establish initial tooling (linting, formatting, tests) and commit a minimal
   “hello world” entry point to anchor onboarding.

## Command notes

- `ls -a /workspace/-`
- `rg --files -g 'AGENTS.md' /workspace`
