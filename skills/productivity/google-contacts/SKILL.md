---
name: google-contacts
description: List Google Contacts — names, emails, and phone numbers. Uses Google OAuth2 via the google-auth skill.
version: 1.0.0
author: Nous Research
license: MIT
metadata:
  hermes:
    tags: [Google, Contacts, People]
    homepage: https://github.com/NousResearch/hermes-agent
    related_skills: [google-auth, gmail]
---

# Google Contacts

List contacts from the user's Google account — names, email addresses, and phone numbers.

## Prerequisites

Requires Google OAuth2 setup via the `google-auth` skill:

```bash
GSETUP="python ~/.hermes/skills/productivity/google-auth/scripts/setup.py"
$GSETUP --check
```

If not authenticated, load `google-auth`: `skill_view("google-auth")`

## Usage

```bash
GAPI="python ~/.hermes/skills/productivity/google-auth/scripts/google_api.py"

# List contacts (default 50)
$GAPI contacts list

# Limit results
$GAPI contacts list --max 20
```

## Output Format

```json
[{
  "name": "Alice Smith",
  "emails": ["alice@example.com", "alice.smith@work.com"],
  "phones": ["+1-555-0123"]
}]
```

## Rules

1. **Check auth before first use** — run `$GSETUP --check`.
2. Contact data is **read-only** — this skill cannot create or modify contacts.
3. **Respect rate limits** — avoid rapid-fire sequential API calls.
