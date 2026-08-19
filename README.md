# NetBox

Docker Compose deployment of [NetBox](https://github.com/netbox-community/netbox) for
infrastructure documentation and IPAM/DCIM, with Authentik OIDC authentication.

## Stack

- **NetBox** — `netboxcommunity/netbox` (pinned via `NETBOX_VERSION`)
- **PostgreSQL 18** — primary datastore
- **Valkey** (Redis-compatible) — task queue (`redis`) and cache (`redis-cache`), separate instances
- **Authentik** — external OIDC provider for remote authentication and group/role sync

## Prerequisites

- Docker Engine and Docker Compose plugin
- An Authentik (or other OIDC-compliant) instance with an OAuth2/OIDC provider configured
  for NetBox, scopes `openid profile email roles`

## Setup

For a full walkthrough, including how to configure Authentik as the OIDC provider, see
[SETUP.md](SETUP.md). Quick reference:

1. Copy the environment template and fill in real values:

   ```bash
   cp .env.sample .env
   ```

2. Generate secrets for `SECRET_KEY` and `API_TOKEN_PEPPER_1`:

   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(64))"
   ```

3. Fill in database, Redis, and Authentik OIDC credentials in `.env`.

4. Start the stack:

   ```bash
   docker compose up -d
   ```

5. NetBox is served on `http://localhost:8000`. On first run a superuser is created from
   `SUPERUSER_USERNAME`/`SUPERUSER_EMAIL`/`SUPERUSER_PASSWORD` unless `SKIP_SUPERUSER=true`.

## Repository layout

| Path | Purpose |
| --- | --- |
| `compose.yml` | Service definitions for Postgres, Redis/Valkey, and NetBox |
| `.env.sample` | Template for the required environment variables (copy to `.env`, never commit `.env`) |
| `configuration/authentik.py` | NetBox config plugin wiring OIDC settings and the auth pipeline |
| `custom_pipeline.py` | `python-social-auth` pipeline steps: group allow-listing and role/group sync from OIDC claims |
| `SETUP.md` | Full setup walkthrough, including Authentik OIDC provider configuration |
| `.github/workflows/secret-detection.yml` | CI workflow: secret detection on every push/PR |

## Authentication

Remote auth is delegated to Authentik via OIDC. Access is gated to members of the
`Netbox_Users` or `Netbox_Admins` groups (see `custom_pipeline.py`); members of
`Netbox_Admins` are granted staff/superuser rights automatically. Group membership is
re-synced from the OIDC token on every login, so removing a user from a group in
Authentik revokes NetBox access/roles on their next sign-in.

## Security

Secrets live only in `.env` (git-ignored) and are never committed. A GitHub Actions
workflow runs secret detection on every push and pull request. If you rotate a
credential, update `.env` on the host directly — `.env.sample` should only ever contain
placeholders.
