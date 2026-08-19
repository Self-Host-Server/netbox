# Contributing

This repo holds the deployment configuration for a self-hosted NetBox instance, not the
NetBox application itself. Changes here affect a running service, so treat them
accordingly.

## Workflow

1. Create a branch off `main` for your change.
2. Open a merge/pull request; `CODEOWNERS` requires review from
   `@Self-Host-Server/code-owners` before merging.
3. Keep `main` deployable — anything merged should be safe to `docker compose up -d`
   against a real instance.

## Making changes

- **Never commit `.env`** or any file containing real secrets, tokens, or passwords.
  `.env` is git-ignored; only `.env.sample` (placeholders only) belongs in the repo.
- If you add a new environment variable, add it to `.env.sample` with a placeholder value
  and document its purpose with a comment.
- Test `compose.yml` changes locally before opening a request:
  ```bash
  docker compose config   # validate syntax
  docker compose up -d    # bring the stack up
  docker compose ps       # confirm all services report healthy
  ```
- Changes to `custom_pipeline.py` or `configuration/authentik.py` affect login and
  authorization — verify a login round-trip against a real or test Authentik instance
  before merging, including both an allowed and a non-member group to confirm the deny
  path still works.

## Commit messages

Commit subjects **must** use [Conventional Commits](https://www.conventionalcommits.org/)
prefixes:

| Prefix                                 | Use for                                         |
| -------------------------------------- | ----------------------------------------------- |
| `feat:`                                | A new capability                                |
| `fix:`                                 | A bug fix                                       |
| `docs:`                                | Documentation only                              |
| `refactor:`                            | Code change that isn't a fix or a feature       |
| `perf:`                                | Performance improvement                         |
| `test:`                                | Adding or correcting tests                      |
| `style:` / `build:` / `ci:` / `chore:` | Formatting, tooling, CI, dependency bumps, etc. |

Add `!` after the type (e.g. `fix!:`) or a `BREAKING CHANGE:` footer for a breaking change.

This isn't just style — `.github/workflows/release.yml` parses these prefixes to decide
the next semver bump, and `git-cliff` (configured in `pyproject.toml`) uses them to
categorize the auto-generated release changelog. There's intentionally no catch-all
parser: a commit without a recognized prefix is silently **dropped from the release
notes entirely**, not filed under a generic bucket. If your subject doesn't fit one of
these types, it's a sign the commit should probably be split or reworded, not that the
convention doesn't apply.

Keep subjects short and imperative after the prefix (e.g. "fix: correct Redis cache
healthcheck", not "fix: fixed stuff"). Explain _why_ in the body when the change isn't
self-evident from the diff.

## Security

A GitHub Actions workflow (`.github/workflows/secret-detection.yml`) runs secret
detection on every push and pull request. A failed run almost always means a real secret
was staged — rotate the credential and scrub it from history rather than force-pushing
over it silently; loop in the repo owners.
