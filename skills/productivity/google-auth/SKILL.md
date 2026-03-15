---
name: google-auth
description: Shared OAuth2 setup for all Google services (Gmail, Calendar, Drive, Sheets, Docs, Contacts). Run this once to authorize, then use individual Google skills.
version: 1.0.0
author: Nous Research
license: MIT
metadata:
  hermes:
    tags: [Google, OAuth, Auth, Setup]
    homepage: https://github.com/NousResearch/hermes-agent
    related_skills: [google-calendar, gmail, google-drive, google-drive-write, google-contacts]
---

# Google Auth — Shared OAuth2 Setup

Shared authentication for all Google service skills. Run this setup once — all Google skills (`google-calendar`, `gmail`, `google-drive`, `google-drive-write`, `google-contacts`) use the same token.

## Scripts

- `scripts/setup.py` — OAuth2 setup (run once to authorize)
- `scripts/google_api.py` — API wrapper CLI (used by all Google service skills)

## Setup

Define shorthands:

```bash
GSETUP="python ~/.hermes/skills/productivity/google-auth/scripts/setup.py"
GAPI="python ~/.hermes/skills/productivity/google-auth/scripts/google_api.py"
```

### Step 0: Check if already set up

```bash
$GSETUP --check
```

If it prints `AUTHENTICATED`, setup is done — skip to the service skill you need.

### Step 1: Triage — ask the user what they need

**Question 1: "What Google services do you need? Just email, or also Calendar/Drive/Sheets/Docs?"**

- **Email only** → Use the `himalaya` skill instead — it works with a Gmail App Password and takes 2 minutes. No Google Cloud project needed.
- **Calendar, Drive, Sheets, Docs (or email + these)** → Continue with OAuth setup below.

**Question 2: "Does your Google account use Advanced Protection (hardware security keys required to sign in)? If you're not sure, you probably don't."**

- **No / Not sure** → Normal setup. Continue below.
- **Yes** → Their Workspace admin must add the OAuth client ID to the org's allowed apps list before Step 4 will work.

### Step 2: Create OAuth credentials (one-time, ~5 minutes)

Tell the user:

> You need a Google Cloud OAuth client. This is a one-time setup:
>
> 1. Go to https://console.cloud.google.com/apis/credentials
> 2. Create a project (or use an existing one)
> 3. Click "Enable APIs" and enable: Gmail API, Google Calendar API, Google Drive API, Google Sheets API, Google Docs API, People API
> 4. Go to Credentials → Create Credentials → OAuth 2.0 Client ID
> 5. Application type: "Desktop app" → Create
> 6. Click "Download JSON" and tell me the file path

Once they provide the path:

```bash
$GSETUP --client-secret /path/to/client_secret.json
```

### Step 3: Get authorization URL

```bash
$GSETUP --auth-url
```

This prints a URL. **Send the URL to the user** and tell them:

> Open this link in your browser, sign in with your Google account, and authorize access. After authorizing, you'll be redirected to a page that may show an error — that's expected. Copy the ENTIRE URL from your browser's address bar and paste it back to me.

### Step 4: Exchange the code

The user will paste back either a URL like `http://localhost:1/?code=4/0A...&scope=...` or just the code string. Either works:

```bash
$GSETUP --auth-code "THE_URL_OR_CODE_THE_USER_PASTED"
```

### Step 5: Verify

```bash
$GSETUP --check
```

Should print `AUTHENTICATED`. Setup is complete — token refreshes automatically.

## Notes

- Token stored at `~/.hermes/google_token.json` — auto-refreshes on expiry.
- To revoke: `$GSETUP --revoke`

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `NOT_AUTHENTICATED` | Run setup Steps 2-5 above |
| `REFRESH_FAILED` | Token revoked or expired — redo Steps 3-5 |
| `HttpError 403: Insufficient Permission` | Missing API scope — `$GSETUP --revoke` then redo Steps 3-5 |
| `HttpError 403: Access Not Configured` | API not enabled — user needs to enable it in Google Cloud Console |
| `ModuleNotFoundError` | Run `$GSETUP --install-deps` |
| Advanced Protection blocks auth | Workspace admin must allowlist the OAuth client ID |

## Revoking Access

```bash
$GSETUP --revoke
```
