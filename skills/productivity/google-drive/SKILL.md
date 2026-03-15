---
name: google-drive
description: Read content from Google Drive — Docs, Sheets, PDFs, and file search. Tries Google API (OAuth2) first, falls back to browser-based SSO for school/enterprise accounts. Read-only — for writing, use google-drive-write.
version: 1.2.0
author: Nous Research
license: MIT
metadata:
  hermes:
    tags: [Google, Drive, Docs, Sheets, School, SSO, Education]
    homepage: https://github.com/NousResearch/hermes-agent
    related_skills: [google-auth, google-drive-write]
---

# Google Drive — Read Content

Read content from Google Drive links and search for files. **This skill is read-only** — for writing/editing, use the `google-drive-write` skill.

Three methods are available — try them in order:

1. **Direct Fetch** (fastest): `curl` the export URL — works for publicly shared files, no auth needed
2. **API Mode** (preferred for authenticated access): Uses Google OAuth2 via the `google-auth` skill
3. **Browser SSO Mode** (fallback): Uses browser automation with persistent login — works for school/enterprise accounts that block Developer Console access

**IMPORTANT**: All tool references in this skill (`browser_navigate`, `browser_snapshot`, `browser_click`, `browser_type`, `browser_press`, `web_extract`, `clarify`, `memory`) are **agent tools** — invoke them as tool calls, NOT as Python imports or function calls in `execute_code`.

## Scripts

- `scripts/gdrive_read.py` — URL parser and URL builder (export, edit, view URLs)

## How to Read a Google Drive Link

When a user shares a Google Drive link, **always start here**:

### Step 0: Parse the URL

```bash
GDRIVE="python3 ~/.hermes/skills/productivity/google-drive/scripts/gdrive_read.py"
$GDRIVE parse "THE_DRIVE_URL"
```

Returns JSON with `file_id`, `file_type`, `export_url`, `edit_url`, and `view_url`.

### Step 1: Try Direct Fetch (No Auth Needed)

Try fetching the export URL directly. This works for files shared as "Anyone with the link":

```bash
curl -sL "EXPORT_URL_FROM_STEP_0"
```

- If this returns **document content** (actual text / CSV data, not HTML) → done!
- If this returns **HTML containing "Sign in"** or a login page → requires authentication. Continue to Step 2.

### Step 2: Check Memory for Auth Method

Look in your memory for an existing `google-drive-auth` entry. If found, skip to the appropriate method below.

### Step 3: Check Existing Google Auth

```bash
GSETUP="python3 ~/.hermes/skills/productivity/google-auth/scripts/setup.py"
$GSETUP --check 2>/dev/null
```

If output is `AUTHENTICATED`, use **Method A (API Mode)** below. Save to memory:
```
memory(action="add", target="memory", content="google-drive-auth: API mode via google-auth skill.")
```

### Step 4: Check if Browser Tools Are Available

Check if `browser_navigate` is in your available tools list.

If NOT available, tell the user:
> "Browser tools aren't available. To enable browser-based Google Drive access, run:
> `cd /path/to/hermes-agent && npm install && npx agent-browser install --with-deps`
> Then restart the agent. Or make the document publicly accessible (Share → Anyone with the link)."

### Step 5: Ask About Developer Console Access

```
clarify("The file requires authentication. Can you access the Google Developer Console (console.cloud.google.com)? School/enterprise accounts often cannot.", ["Yes, I can access it", "No, I cannot / I'm not sure"])
```

- **Yes**: guide through `google-auth` skill setup, then use API mode.
- **No**: proceed with **Method B (Browser SSO Mode)** below.

---

## Method A: API Mode

Uses Google OAuth2 via the `google-auth` skill. For setup, load: `skill_view("google-auth")`

```bash
GAPI="python3 ~/.hermes/skills/productivity/google-auth/scripts/google_api.py"
```

### Read Content by Type

- **Google Docs**: `$GAPI docs get FILE_ID`
- **Google Sheets**: `$GAPI sheets get FILE_ID "Sheet1!A:Z"`
- **Search for files**: `$GAPI drive search "quarterly report" --max 10`
- **Raw Drive query**: `$GAPI drive search "mimeType='application/pdf'" --raw-query --max 5`

### Output Formats (API Mode)

- **docs get**: `{title, documentId, body}` — body is extracted plain text
- **sheets get**: `[[cell, cell, ...], ...]` — 2D array of cell values
- **drive search**: `[{id, name, mimeType, modifiedTime, webViewLink}]`

---

## Method B: Browser SSO Mode

Uses the browser with a persistent profile (`google-drive`) for school/enterprise SSO login. Sessions typically persist ~90 days.

### How to Read Content (Browser Mode)

**IMPORTANT — Lessons from real-world testing:**
- **Export URLs do NOT work** in the browser — they trigger downloads that the browser blocks (ERR_ABORTED)
- **Google Docs content is Canvas-rendered** — `browser_snapshot()` on a Doc view page returns NO document text (it's drawn on a `<canvas>` element, invisible to the DOM)
- **The working method**: Navigate to the **edit URL**, use the **File menu → Download** to save as a readable format, then read the downloaded file from disk

**Step-by-step procedure:**

**1. Parse the URL:**

```bash
GDRIVE="python3 ~/.hermes/skills/productivity/google-drive/scripts/gdrive_read.py"
$GDRIVE parse "THE_DRIVE_URL"
```

**2. Navigate to the EDIT URL with persistent profile:**

```
browser_navigate(url=edit_url, profile="google-drive")
```

**3. Take a snapshot to check state:**

```
browser_snapshot()
```

- If you see the **document editor** (Google Docs toolbar, sheet grid, etc.) → proceed to Step 4
- If you see a **login page** → run the **SSO Login Flow** below, then come back here
- If you see **"You need access"** → tell the user the file isn't shared with their account

**4. Download the content via File menu:**

The download method depends on the file type:

**For Google Docs:**
```
browser_click(ref="@REF_OF_FILE_MENU")          # Click "File" in the menu bar
```
Then take a snapshot, find "Download" submenu, click it, then select a format:
- **Plain text (.txt)** — simplest, best for reading content
- **Markdown (.md)** — preserves formatting if available
- **PDF (.pdf)** — preserves layout

```
browser_click(ref="@REF_OF_DOWNLOAD")            # Click "Download" submenu
browser_click(ref="@REF_OF_FORMAT")               # Click desired format (e.g., "Plain text (.txt)")
```

**For Google Sheets:**
Same File → Download flow, choose **CSV (.csv)** or **TSV (.tsv)**.

**For Google Slides:**
Same File → Download flow, choose **Plain text (.txt)** or **PDF (.pdf)**.

**5. Read the downloaded file:**

Downloads land in `~/Downloads/` (or `/root/Downloads/` for root users). Filenames have spaces replaced with underscores or may keep original names.

```bash
ls -t ~/Downloads/ | head -5                      # Find the most recent download
cat ~/Downloads/FILENAME                           # Read the content
```

If the file is a PDF, use OCR tools or the `ocr-and-documents` skill to extract text.

**6. Return the content to the user.**

### SSO Login Flow (AI-Driven)

When a login page is detected, navigate through it autonomously. Only prompt the user for credentials and 2FA.

**CRITICAL RULES:**
- **DO** save the user's password to `USER.md` memory so they don't have to re-enter it
- **DO** save the user's email to `USER.md` memory
- **DO** save the login flow pattern to `MEMORY.md`

**Login Loop:**

```
LOOP (max 15 iterations to prevent infinite loops):
  1. Take browser_snapshot()
  2. Analyze the current page:

  CASE: Google "Choose an account" or "Sign in" page (accounts.google.com)
    → Check USER.md memory for saved email
    → If no saved email: clarify("What is your email address for this Google/school account?")
    → Save email: memory(action="add", target="user", content="Google/school email: USER_EMAIL")
    → Fill email: browser_type(ref="@REF_OF_EMAIL_INPUT", text="USER_EMAIL")
    → Submit: browser_click(ref="@REF_OF_NEXT_BUTTON") or browser_press(key="Enter")
    → CONTINUE LOOP

  CASE: SSO redirect — Microsoft login page (login.microsoftonline.com)
    → The email may need to be re-entered on the Microsoft page
    → Fill email again using saved email from memory
    → Submit, CONTINUE LOOP

  CASE: Password input field visible
    → Check USER.md memory for saved password
    → If no saved password: clarify("Please enter your password for [email].")
    → Save password: memory(action="add", target="user", content="School account password: USER_PASSWORD")
    → Fill: browser_type(ref="@REF_OF_PASSWORD_INPUT", text="USER_PASSWORD")
    → Submit: browser_click(ref="@REF_OF_SIGN_IN_BUTTON") or browser_press(key="Enter")
    → CONTINUE LOOP

  CASE: 2FA / MFA prompt
    → Identify the 2FA method from the page:
    → If NUMBER MATCHING (e.g., Microsoft Authenticator shows a number):
        Take browser_snapshot() to read the number displayed on screen
        clarify("Please approve the sign-in on your phone. The number to match is: [NUMBER]", ["Done - I approved it", "I need more time", "Cancel"])
    → If PUSH NOTIFICATION (approve/deny without number):
        clarify("Please approve the sign-in request on your phone, then tell me when done.", ["Done - I approved it", "I need more time", "Cancel"])
    → If CODE ENTRY (TOTP, SMS):
        clarify("Please enter the verification code from your authenticator app or SMS.")
        Fill code: browser_type(ref="@REF_OF_CODE_INPUT", text="CODE")
        Submit, CONTINUE LOOP
    → If "I need more time" → wait 10 seconds, CONTINUE LOOP
    → If "Cancel" → abort and tell user

  CASE: "Stay signed in?" / "Remember this device?" / "Don't show this again"
    → Click "Yes" to maximize session duration
    → CONTINUE LOOP

  CASE: "Verify it's you" / additional Google verification after SSO
    → Click "Continue" or "Try another way" as appropriate
    → CONTINUE LOOP

  CASE: Consent / permissions page
    → Click "Accept" / "Allow" / "Continue"
    → CONTINUE LOOP

  CASE: Google Drive / Docs editor is visible
    → Login succeeded! EXIT LOOP
    → Save flow to memory (see below)

  CASE: Error or unrecognized page
    → browser_vision(question="What is shown on this page? Is it a login form, error, or content?")
    → If unclear: ask user for guidance

END LOOP
```

**After successful login, save the flow to memory:**

```
memory(action="add", target="memory", content="google-drive-auth: Browser SSO. Provider: [detected]. Profile: google-drive. Flow: [1. email at accounts.google.com → 2. redirect to login.microsoftonline.com → 3. re-enter email → 4. password → 5. MS Authenticator number match → 6. Stay signed in=Yes → 7. Google 'Verify it's you' Continue]. Content method: edit URL + File→Download. Downloads go to ~/Downloads/. Session ~90 days.")
```

### Handling Session Expiry

When a previously working session shows a login page:
1. Read memory for saved login flow
2. Email and password are already in `USER.md` — fill them automatically
3. Only prompt the user for 2FA approval
4. If flow has changed, adapt and update memory

### SSO Provider Identification

| Provider | URL Pattern | Identifying Features |
|----------|------------|---------------------|
| Google | `accounts.google.com` | "Sign in with Google" heading |
| Microsoft / Azure AD | `login.microsoftonline.com` | Microsoft logo, may require number matching for 2FA |
| Okta | `*.okta.com` | Okta widget |
| Clever | `clever.com` | Common in K-12 schools |
| ClassLink | `launchpad.classlink.com` | ClassLink branding |
| SAML / Generic | Various institutional URLs | School/university branding |

---

## Known Limitations & Workarounds

These are lessons learned from real-world testing:

| What Doesn't Work | Why | Workaround |
|---|---|---|
| Export URLs in browser | Browser blocks downloads (ERR_ABORTED) | Use edit URL + File → Download instead |
| `browser_snapshot()` on Google Docs | Content is Canvas-rendered, invisible to DOM | Download the doc as text/markdown/PDF and read the file |
| `browser_snapshot()` on Google Sheets | May work for simple sheets; complex ones are Canvas | Download as CSV and read the file |
| `curl` on private files | No auth cookies in terminal | Use browser mode with persistent profile |
| Direct `curl` export after browser login | Browser cookies aren't shared with `curl` | Always use browser File→Download for private files |

## Rules

1. **Save email, password, and login flow pattern to memory** so the user doesn't have to re-enter credentials each time.
2. **Always use `profile="google-drive"`** with `browser_navigate` — ensures session persistence.
3. **Use the edit URL, not export URL** for authenticated browser access.
4. **Download via File menu**, don't try to snapshot document content.
5. **Check `~/Downloads/`** for downloaded files — names may have underscores replacing spaces.
6. **For 2FA number matching**, read the number from the page and tell the user what to match.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Login page keeps appearing | Session expired. Re-run login flow (password + 2FA only). |
| "You need access" error | File isn't shared with user's account. Ask user to request access. |
| Export URL returns ERR_ABORTED | Expected — use File → Download from the edit URL instead. |
| Downloaded file not found | Check `ls -t ~/Downloads/ \| head` — filename may differ from doc title. |
| 2FA times out | Ask user to retry. Some authenticator apps have short approval windows. |
| Snapshot shows no content (blank) | Google Docs uses Canvas rendering. Download the file instead of snapshotting. |
| Browser profile corrupted | Delete `~/.hermes/browser-profiles/google-drive/` and re-login. |
| Browser tools not available | Run `npm install && npx agent-browser install --with-deps` in hermes-agent dir. |
| "Verify it's you" page after SSO | Click "Continue" — this is Google's additional verification after SSO redirect. |
