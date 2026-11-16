# CRM API

A learning CRM API built with FastAPI, SQLAlchemy, and SQLite.

## Installation and launch (PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$secret = (python -c "import secrets; print(secrets.token_urlsafe(48))")
[Environment]::SetEnvironmentVariable("CRM_SECRET_KEY", $secret, "User")
$env:CRM_SECRET_KEY = $secret
$invite = (python -c "import secrets; print(secrets.token_urlsafe(32))")
[Environment]::SetEnvironmentVariable("CRM_REGISTRATION_KEY", $invite, "User")
$env:CRM_REGISTRATION_KEY = $invite
alembic upgrade head
uvicorn app.main:app --reload
```

Windows loads the saved environment variables in new PowerShell windows. Open a new window after saving them for the first time. Do not commit secrets to Git. The local API and its documentation are available at http://127.0.0.1:8000 and http://127.0.0.1:8000/docs.

## Authentication

Create an account with `POST /auth/register`, providing a name, email, password of at least 12 characters, and the value of `CRM_REGISTRATION_KEY` as `invitation_key`. Sign in with `POST /auth/login`, then send the returned token as `Authorization: Bearer <token>`. Tokens are valid for 30 minutes. `GET /auth/me` returns the current account. All other CRM routes require authentication.

All invited users share access to the CRM data. Existing database users are kept, but they do not have passwords and cannot sign in. Duplicate email addresses belonging to existing users are changed to `legacy-user-<id>@invalid.local` to enforce email uniqueness. Create a new account with a different email address.

## Demo data

After applying the migration, run `python seed_data.py`. The script adds demo records in English and uses the valid task statuses `pending`, `in_progress`, and `completed`.

## Before deployment

Set unique secrets through your hosting provider's secure configuration, set the real domains in `CRM_ALLOWED_HOSTS` (comma-separated), enable HTTPS, configure login rate limiting at the reverse proxy, and set up backups. SQLite is intended for local development. All invited users can access the same CRM data. A public multi-organization service also needs organization-level data isolation and server-side rate-limit storage.
