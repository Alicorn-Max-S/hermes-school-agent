---
name: gmail
description: "Gmail email management — search, read, compose, send, reply, forward, and organize with labels and filters. Uses Google OAuth2. Trigger on mentions of email, inbox, sending messages, Gmail, or composing a message to someone."
version: 1.0.0
author: Nous Research
license: MIT
metadata:
  apollo:
    tags: [Gmail, Email, Google]
    homepage: https://github.com/NousResearch/apollo-agent
    related_skills: [google-auth, himalaya]
    school: true
    school_category: "Google Workspace"
---

# Gmail

Search, read, send, reply, and manage Gmail messages with labels.

## References

- `references/gmail-search-syntax.md` — Gmail search operators (is:unread, from:, newer_than:, etc.)

## Prerequisites

Requires Google OAuth2 setup via the `google-auth` skill:

```bash
GSETUP="python ~/.apollo/skills/productivity/google-auth/scripts/setup.py"
$GSETUP --check
```

If not authenticated, load `google-auth`: `skill_view("google-auth")`

**Note:** If the user only needs email (no Calendar, Drive, Sheets, etc.), the `himalaya` skill is simpler — it uses a Gmail App Password and takes 2 minutes to set up with no Google Cloud project needed.

## Usage

```bash
GAPI="python ~/.apollo/skills/productivity/google-auth/scripts/google_api.py"
```

### Search

```bash
# Unread messages
$GAPI gmail search "is:unread" --max 10

# From a specific sender, recent
$GAPI gmail search "from:boss@company.com newer_than:1d"

# Attachments
$GAPI gmail search "has:attachment filename:pdf newer_than:7d"

# Complex query
$GAPI gmail search "is:unread -category:promotions -category:social"
```

For the full search syntax reference, load: `skill_view("gmail", file_path="references/gmail-search-syntax.md")`

### Read Full Message

```bash
$GAPI gmail get MESSAGE_ID
```

### Send Email

```bash
# Plain text
$GAPI gmail send --to user@example.com --subject "Hello" --body "Message text"

# HTML
$GAPI gmail send --to user@example.com --subject "Report" --body "<h1>Q4</h1><p>Details...</p>" --html

# With CC
$GAPI gmail send --to user@example.com --subject "FYI" --body "See below" --cc "team@example.com"
```

### Reply

```bash
# Automatically threads and sets In-Reply-To
$GAPI gmail reply MESSAGE_ID --body "Thanks, that works for me."
```

### Labels

```bash
# List all labels
$GAPI gmail labels

# Add a label
$GAPI gmail modify MESSAGE_ID --add-labels LABEL_ID

# Remove a label (e.g., mark as read)
$GAPI gmail modify MESSAGE_ID --remove-labels UNREAD
```

## Output Format

- **gmail search**: `[{id, threadId, from, to, subject, date, snippet, labels}]`
- **gmail get**: `{id, threadId, from, to, subject, date, labels, body}`
- **gmail send/reply**: `{status: "sent", id, threadId}`
- **gmail labels**: `[{id, name, type}]`
- **gmail modify**: `{id, labels}`

## Rules

1. **Never send email without confirming with the user first.** Show the draft (to, subject, body) and ask for approval.
2. **Check auth before first use** — run `$GSETUP --check`.
3. **Use the search syntax reference** for complex queries.
4. **Respect rate limits** — avoid rapid-fire sequential API calls.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `NOT_AUTHENTICATED` | Load `google-auth` skill and follow setup |
| `REFRESH_FAILED` | Token expired — redo auth steps 3-5 in `google-auth` |
| `HttpError 403: Insufficient Permission` | Missing Gmail scope — revoke and re-auth via `google-auth` |
| No results from search | Check query syntax — load `references/gmail-search-syntax.md` |
