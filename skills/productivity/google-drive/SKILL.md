---
name: google-drive
description: Read content from Google Drive links (Docs, Sheets, PDFs). Supports both Google API (OAuth2) and browser-based SSO authentication for school/enterprise accounts that cannot access the Google Developer Console.
version: 1.0.0
author: Nous Research
license: MIT
metadata:
  hermes:
    tags: [Google, Drive, Docs, Sheets, School, SSO, Education]
    homepage: https://github.com/NousResearch/hermes-agent
    related_skills: [google-workspace]
---

# Google Drive Content Reader

Read content from Google Drive links. Supports two authentication methods:

- **API Mode**: Uses Google Workspace OAuth2 (requires Google Developer Console access)
- **Browser SSO Mode**: Uses browser automation with persistent login sessions — works for school/enterprise accounts that block Developer Console access

## Scripts

- `scripts/gdrive_read.py` — URL parser and export URL builder

## First-Time Setup (Auto-Detection)

When the user asks you to read a Google Drive link for the first time, follow this detection flow:

### Step 1: Check Memory

Look in your memory for an existing `google-drive-auth` entry. If found, skip to the appropriate method (API or Browser SSO) below.

### Step 2: Check Existing Google Workspace Auth

```bash
python ~/.hermes/skills/productivity/google-workspace/scripts/setup.py --check 2>/dev/null
```

If output is `AUTHENTICATED`, use **Method A (API Mode)** below. Save to memory:
```
memory(action="add", target="memory", content="google-drive-auth: API mode via google-workspace skill. Already authenticated.")
```

### Step 3: Ask About Developer Console Access

If not already authenticated, ask the user:

```
clarify("Can you access the Google Developer Console (console.cloud.google.com) with your Google account? If you're using a school or enterprise account, you may not have access.", ["Yes, I can access it", "No, I cannot / I'm not sure"])
```

- If **yes**: guide them through the google-workspace skill setup (load that skill with `skill_view("google-workspace")`), then use API mode.
- If **no**: proceed with **Method B (Browser SSO Mode)** below.

---

## Method A: API Mode

Delegate to the existing google-workspace skill's `google_api.py` for content reading.

### Setup

```bash
GAPI="python ~/.hermes/skills/productivity/google-workspace/scripts/google_api.py"
```

### Reading Content

First, parse the URL to get the file ID:

```bash
GDRIVE="python ~/.hermes/skills/productivity/google-drive/scripts/gdrive_read.py"
$GDRIVE parse "THE_DRIVE_URL"
```

This returns JSON with `file_id`, `file_type`, `export_url`, and `view_url`.

Then use the appropriate API command:

- **Google Docs**: `$GAPI docs get FILE_ID`
- **Google Sheets**: `$GAPI sheets get FILE_ID "Sheet1!A:Z"`
- **Other files**: `$GAPI drive search "name = 'filename'"` to find, then download

---

## Method B: Browser SSO Mode

Uses the browser with a persistent profile (`google-drive`) to log in through school/enterprise SSO. Once logged in, the session typically persists for 90 days.

### Reading Content

Follow this procedure every time the user shares a Google Drive link:

**1. Parse the URL:**

```bash
GDRIVE="python ~/.hermes/skills/productivity/google-drive/scripts/gdrive_read.py"
$GDRIVE parse "THE_DRIVE_URL"
```

This returns JSON with `file_id`, `file_type`, `export_url`, and `view_url`.

**2. Navigate with persistent profile:**

For Google Docs and Sheets, use the **export URL** to get clean text/CSV content. For other files, use the **view URL**.

```
browser_navigate(url=export_url_or_view_url, profile="google-drive")
```

**3. Check if login is needed:**

```
browser_snapshot()
```

Analyze the snapshot:

- If it contains the **file content** (document text, CSV data, etc.) → proceed to content extraction below
- If it shows a **login page** → run the **SSO Login Flow** below
- If it shows a **"You need access" page** → tell the user the file isn't shared with their account

**4. Extract content:**

- **Google Docs** (export as txt): The page content IS the document text. Read it from the snapshot.
- **Google Sheets** (export as csv): The page content IS the CSV data. Read it from the snapshot.
- **PDFs / other files**: Use `browser_snapshot(full=True)` on the Drive viewer. If the snapshot is insufficient, use `browser_vision(question="Extract all text content from this document")`.
- For long documents, use `browser_scroll(direction="down")` and take additional snapshots.

### SSO Login Flow (AI-Driven)

When a login page is detected, navigate through it autonomously. Only prompt the user when you need actual credentials or 2FA confirmation.

**CRITICAL RULES:**
- **NEVER** save passwords to memory
- **DO** save the user's email to `USER.md` memory (with their permission)
- **DO** save the login flow pattern to `MEMORY.md` so you know what to expect next time

**Login Loop:**

```
LOOP (max 10 iterations to prevent infinite loops):
  1. Take browser_snapshot()
  2. Analyze what the current page is:

  CASE: Email/username input field visible
    → Check USER.md memory for saved email
    → If no saved email: clarify("What is your email address for this Google/school account?")
    → Save email to memory: memory(action="add", target="user", content="Google/school email: USER_EMAIL")
    → Fill email: browser_type(ref="@REF_OF_EMAIL_INPUT", text="USER_EMAIL")
    → Submit: browser_click(ref="@REF_OF_NEXT_BUTTON") or browser_press(key="Enter")
    → Wait briefly, CONTINUE LOOP

  CASE: Password input field visible
    → clarify("Please enter your password for [email/account].")
    → Fill password: browser_type(ref="@REF_OF_PASSWORD_INPUT", text="USER_PASSWORD")
    → Submit: browser_click(ref="@REF_OF_SIGN_IN_BUTTON") or browser_press(key="Enter")
    → Wait briefly, CONTINUE LOOP

  CASE: 2FA / MFA prompt (authenticator app, push notification, SMS code, etc.)
    → Identify the 2FA method from the page content
    → If push notification (e.g., Microsoft Authenticator "Approve sign-in"):
        clarify("Please approve the sign-in request on your phone (Microsoft Authenticator / your authentication app), then tell me when done.", ["Done - I approved it", "I need more time", "Cancel login"])
        If "I need more time" → wait 10 seconds, CONTINUE LOOP
        If "Cancel login" → abort and tell user
    → If code entry (TOTP, SMS):
        clarify("Please enter the verification code from your authenticator app / SMS.")
        Fill code: browser_type(ref="@REF_OF_CODE_INPUT", text="CODE")
        Submit, CONTINUE LOOP

  CASE: "Stay signed in?" / "Remember this device?" prompt
    → Click "Yes" / "Don't show again" to maximize session duration
    → CONTINUE LOOP

  CASE: Consent / permissions page
    → Click "Accept" / "Allow"
    → CONTINUE LOOP

  CASE: Drive content is visible (document text, file list, etc.)
    → Login succeeded! EXIT LOOP
    → Save login flow to memory (see below)

  CASE: Error page or unrecognized page
    → browser_vision(question="What is shown on this page? Is it a login page, error, or something else?")
    → If error: report to user, ask how to proceed
    → If unrecognizable: show screenshot to user, ask for guidance

END LOOP
```

**After successful login, save the flow to memory:**

```
memory(action="add", target="memory", content="google-drive-auth: Browser SSO mode. Provider: [Google/Microsoft/Okta/other]. Profile: google-drive. Login flow: [1. email at accounts.google.com, 2. redirect to login.microsoftonline.com, 3. email again, 4. password, 5. MS Authenticator push, 6. 'Stay signed in' → Yes]. Session persists ~90 days.")
```

### Handling Session Expiry

When you navigate to a Drive URL with the persistent profile and get a login page instead of content:

1. Read memory for the saved login flow pattern
2. You already know the email (from `USER.md`) — skip asking for it
3. Only prompt for password + 2FA
4. If the flow has changed (different pages than expected), adapt and update memory

### SSO Provider Identification

Common SSO providers you may encounter — identify by page URL or content:

| Provider | URL Pattern | Identifying Features |
|----------|------------|---------------------|
| Google | `accounts.google.com` | "Sign in with Google" heading |
| Microsoft / Azure AD | `login.microsoftonline.com`, `login.live.com` | Microsoft logo, "Sign in" with Microsoft branding |
| Okta | `*.okta.com` | Okta branding, "Sign In" with Okta widget |
| Clever | `clever.com` | Clever branding (common in K-12 schools) |
| ClassLink | `launchpad.classlink.com` | ClassLink branding |
| SAML / Generic | Various institutional URLs | School/university branding, "Institutional Login" |

If you can't identify the provider from the snapshot, use `browser_vision()` to visually analyze the page.

---

## Rules

1. **NEVER save passwords to memory.** Only save email/username and login flow pattern.
2. **Always use `profile="google-drive"`** with `browser_navigate` for Drive access — this ensures session persistence.
3. **Parse URLs before navigating** — use `gdrive_read.py parse` to get the right export/view URL.
4. **For long documents**, scroll and take multiple snapshots to capture all content.
5. **If a file requires access permissions**, tell the user — don't try to bypass access controls.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Login page keeps appearing | Session may have expired. Re-run login flow (only password + 2FA needed since email is saved). |
| "You need access" error | File isn't shared with the user's account. Ask user to request access. |
| Export URL returns HTML instead of text | Navigate to view URL instead and use `browser_snapshot(full=True)`. |
| 2FA times out | Ask user to retry 2FA. Some authenticator apps have short windows. |
| Unrecognized login page | Use `browser_vision()` to see the page, ask user for guidance. |
| Browser profile corrupted | Delete `~/.hermes/browser-profiles/google-drive/` and re-login. |
