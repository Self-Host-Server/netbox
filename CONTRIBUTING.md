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
- Keep `netbox-ssot.yaml` and `netbox-sync.ini` consistent with each other where they
  configure the same source, even though only one sync tool is typically run at a time.

## Commit messages

Use short, imperative subject lines describing the change (e.g. "Add Redis cache
healthcheck", not "Fixed stuff"). Explain *why* in the body when the change isn't
self-evident from the diff.

## Security

GitLab CI runs secret detection (`.gitlab-ci.yml`) on every push. A pipeline failure on
that stage almost always means a real secret was staged — rotate the credential and scrub
it from history rather than force-pushing over it silently; loop in the repo owners.
