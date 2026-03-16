---
name: google-contacts
description: List Google Contacts — names, emails, and phone numbers. Uses Google OAuth2 via the google-auth skill.
version: 1.0.0
author: Nous Research
license: MIT
metadata:
  apollo:
    tags: [Google, Contacts, People]
    homepage: https://github.com/NousResearch/apollo-agent
    related_skills: [google-auth, gmail]
    school: true
    school_category: "Google Workspace"
---

# Google Contacts

List contacts from the user's Google account — names, email addresses, and phone numbers.

## Prerequisites

Requires Google OAuth2 setup via the `google-auth` skill:

```bash
GSETUP="python ~/.apollo/skills/productivity/google-auth/scripts/setup.py"
$GSETUP --check
```

If not authenticated, load `google-auth`: `skill_view("google-auth")`

## Usage

```bash
GAPI="python ~/.apollo/skills/productivity/google-auth/scripts/google_api.py"

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
