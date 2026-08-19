# Setup guide

Detailed walkthrough for setting up this NetBox deployment from scratch, including
configuring Authentik as the OIDC provider. For a quick reference, see the
[README](README.md#setup).

## 1. Prerequisites

- Docker Engine + Docker Compose plugin on the host
- A running Authentik instance you have admin access to
- DNS/reverse proxy in front of NetBox if you're exposing it beyond `localhost`
  (the compose file publishes NetBox on `8000` internally, mapped from container port `8080`)

## 2. Clone and create the environment file

```bash
git clone https://github.com/Self-Host-Server/netbox.git
cd netbox
cp .env.sample .env
```

Every value in `.env.sample` is a placeholder (`changeme`, `example.com`, etc.) — `.env`
is git-ignored, so real secrets never get committed. Fill it in as you go through the
sections below.

## 3. Generate NetBox secrets

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

Run this twice and set the output as `SECRET_KEY` and `API_TOKEN_PEPPER_1` in `.env`.
These must be unique per deployment and kept secret — rotating `SECRET_KEY` invalidates
all existing sessions and API tokens.

## 4. Database and cache credentials

Set real passwords for:

- `DB_PASSWORD` (used by both `POSTGRES_PASSWORD` and NetBox's DB connection)
- `REDIS_PASSWORD` (task queue instance)
- `REDIS_CACHE_PASSWORD` (cache instance — must differ from `REDIS_PASSWORD` since they're
  separate containers/volumes)

Leave `DB_USER`/`POSTGRES_DB`/hosts as-is unless you're customizing the compose service
names.

## 5. Configure Authentik (OIDC provider)

NetBox authenticates via OIDC and expects the token to carry a `groups` claim so
`custom_pipeline.py` can gate access and assign roles. Authentik doesn't send group
membership by default, so you need a custom scope mapping in addition to the standard
provider/application setup.

### 5.1 Create the groups

In Authentik, go to **Directory → Groups** and create:

- `Netbox_Users` — general NetBox access
- `Netbox_Admins` — staff + superuser in NetBox

Add the appropriate users to each group.

### 5.2 Create a custom scope mapping for group claims

Go to **Customization → Property Mappings → Create → Scope Mapping**:

- **Name**: `NetBox groups`
- **Scope name**: `roles` (matches `SOCIAL_AUTH_OIDC_SCOPE` in `.env.sample`)
- **Expression**:

  ```python
  return {
      "groups": [group.name for group in user.ak_groups.all()],
  }
  ```

This makes the token/userinfo response include a `groups` array, which
`custom_pipeline.py` reads to allow-list access (`Netbox_Users`/`Netbox_Admins`) and set
`is_staff`/`is_superuser` for `Netbox_Admins`.

### 5.3 Create the OAuth2/OIDC provider

Go to **Applications → Providers → Create → OAuth2/OpenID Provider**:

- **Authorization flow**: your default authorization flow
- **Client type**: Confidential
- **Redirect URIs**: `https://<your-netbox-host>/oauth/complete/oidc/`
  (use `http://localhost:8000/oauth/complete/oidc/` for local testing)
- **Scopes**: add `openid`, `email`, `profile`, and the `NetBox groups` mapping created above
- **Signing key**: select an available certificate

Save, then note the generated **Client ID** and **Client Secret**.

### 5.4 Create the application

Go to **Applications → Applications → Create**, bind it to the provider above, and note
the application **slug** — it's part of the OIDC endpoint URL.

### 5.5 Fill in `.env`

```env
REMOTE_AUTH_ENABLED=true
REMOTE_AUTH_BACKEND=social_core.backends.open_id_connect.OpenIdConnectAuth

SOCIAL_AUTH_OIDC_OIDC_ENDPOINT=https://<authentik-host>/application/o/<app-slug>/
SOCIAL_AUTH_OIDC_KEY=<client-id-from-5.3>
SOCIAL_AUTH_OIDC_SECRET=<client-secret-from-5.3>
SOCIAL_AUTH_OIDC_SCOPE=openid profile email roles
LOGOUT_REDIRECT_URL=https://<authentik-host>/application/o/<app-slug>/end-session/
```

`SOCIAL_AUTH_OIDC_OIDC_ENDPOINT` is the issuer — Authentik serves its discovery document
at `<endpoint>.well-known/openid-configuration`; you can curl that URL to sanity-check the
provider is reachable before wiring up NetBox.

### 5.6 Set allowed hosts

```env
ALLOWED_HOSTS=localhost 127.0.0.1 netbox <your-netbox-host>
CSRF_TRUSTED_ORIGINS=https://<your-netbox-host>
```

`CSRF_TRUSTED_ORIGINS` must match the scheme + host NetBox is actually accessed on, or the
OIDC callback will fail CSRF checks.

## 6. Start the stack

```bash
docker compose up -d
docker compose ps       # wait for all services to report healthy
docker compose logs -f netbox   # tail startup logs if anything looks off
```

NetBox is served on `http://localhost:8000` (or your reverse-proxied host). First boot
runs migrations and, unless `SKIP_SUPERUSER=true`, creates a local superuser from
`SUPERUSER_USERNAME`/`SUPERUSER_EMAIL`/`SUPERUSER_PASSWORD` — useful as a break-glass
login independent of OIDC.

## 7. Verify OIDC login

1. Visit NetBox and click the OIDC/SSO login option.
2. Authenticate as a user in `Netbox_Users` or `Netbox_Admins` — you should land back in
   NetBox logged in.
3. Confirm in **Admin → Users** that the account was created and, if applicable, has
   staff/superuser set (for `Netbox_Admins`).
4. Test the deny path: authenticate as a user in neither group and confirm login is
   rejected (`AuthForbidden` from `custom_pipeline.check_allowed_groups`).
5. Remove a logged-in user from their Authentik group and confirm their NetBox
   access/role updates on next login (group sync is re-evaluated every sign-in, not cached).

## Troubleshooting

- **Login redirects back to NetBox but fails silently** — check `docker compose logs
netbox` for `social_core` errors; usually a scope/claim mismatch (missing `groups`
  claim) or `CSRF_TRUSTED_ORIGINS` not matching the request origin.
- **User logs in but has no access** — the `groups` claim is empty or the user isn't in
  `Netbox_Users`/`Netbox_Admins` in Authentik; check the scope mapping in 5.2 is actually
  attached to the provider.
- **`invalid_client` or similar OAuth error** — `SOCIAL_AUTH_OIDC_KEY`/`SECRET` don't match
  the provider, or the redirect URI registered in Authentik doesn't exactly match NetBox's
  callback URL (scheme and trailing slash matter).
