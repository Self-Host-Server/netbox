# NetBox

Docker Compose deployment of [NetBox](https://github.com/netbox-community/netbox) for
infrastructure documentation and IPAM/DCIM, with Authentik OIDC authentication and
automated inventory sync from Proxmox via NetBox SSOT.

## Stack

- **NetBox** — `netboxcommunity/netbox` (pinned via `NETBOX_VERSION`)
- **PostgreSQL 18** — primary datastore
- **Valkey** (Redis-compatible) — task queue (`redis`) and cache (`redis-cache`), separate instances
- **Authentik** — external OIDC provider for remote authentication and group/role sync
- **NetBox SSOT** — syncs Proxmox hosts/VMs into NetBox as a source of truth

## Prerequisites

- Docker Engine and Docker Compose plugin
- An Authentik (or other OIDC-compliant) instance with an OAuth2/OIDC provider configured
  for NetBox, scopes `openid profile email roles`
- Network access to a Proxmox host for inventory sync (optional)

## Setup

1. Copy the environment template and fill in real values:

   ```bash
   cp .env.sample .env
   ```

2. Generate secrets for `SECRET_KEY` and `API_TOKEN_PEPPER_1`:

   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(64))"
   ```

3. Fill in database, Redis, Authentik OIDC, and Proxmox credentials in `.env`.

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
| `netbox-ssot.yaml` | Config for [NetBox SSOT](https://github.com/bl4ko/netbox-ssot) (Proxmox → NetBox sync) |
| `netbox-sync.ini` | Config for [netbox-sync](https://github.com/bb-Ricardo/netbox-sync) (alternate Proxmox → NetBox sync tool) |
| `.gitlab-ci.yml` | CI pipeline: secret detection on every push |

## Authentication

Remote auth is delegated to Authentik via OIDC. Access is gated to members of the
`Netbox_Users` or `Netbox_Admins` groups (see `custom_pipeline.py`); members of
`Netbox_Admins` are granted staff/superuser rights automatically. Group membership is
re-synced from the OIDC token on every login, so removing a user from a group in
Authentik revokes NetBox access/roles on their next sign-in.

## Inventory sync

Two independent tools are configured to import Proxmox hosts/VMs into NetBox — pick one:

- **NetBox SSOT** (`netbox-ssot.yaml`) — run as a NetBox plugin/job
- **netbox-sync** (`netbox-sync.ini`) — run as a standalone sync script

Both read `NETBOX_HOST_FQDN`, `NETBOX_PORT`, `NETBOX_API_TOKEN`, and `PROXMOX_*` from the
environment.

## Security

Secrets live only in `.env` (git-ignored) and are never committed. GitLab CI runs secret
detection on every push. If you rotate a credential, update `.env` on the host directly —
`.env.sample` should only ever contain placeholders.
