---
name: google-calendar
description: "Google Calendar event management — create, edit, view, and delete events, check availability, and schedule around existing commitments. Automatically checked when scheduling Todoist tasks to prevent overlap. Trigger on mentions of calendar, scheduling, events, availability, class schedule, or time slots."
version: 1.0.0
author: Nous Research
license: MIT
metadata:
  apollo:
    tags: [Google, Calendar, Scheduling, Events, Todoist]
    homepage: https://github.com/NousResearch/apollo-agent
    related_skills: [todoist, google-auth, school]
    school: true
    school_category: "Homework & Assignments"
---

# Google Calendar

Create, view, edit, and delete Google Calendar events. **Detected automatically** when scheduling tasks via Todoist to prevent double-booking.

## Prerequisites

Requires Google OAuth2 setup via the `google-auth` skill. Check auth first:

```bash
GSETUP="python ~/.apollo/skills/productivity/google-auth/scripts/setup.py"
$GSETUP --check
```

If not authenticated, load the `google-auth` skill: `skill_view("google-auth")` and follow setup instructions.

## Usage

```bash
GAPI="python ~/.apollo/skills/productivity/google-auth/scripts/google_api.py"
```

### List Events

```bash
# Next 7 days (default)
$GAPI calendar list

# Specific date range
$GAPI calendar list --start 2026-03-16T00:00:00Z --end 2026-03-16T23:59:59Z

# Different calendar
$GAPI calendar list --calendar "work@group.calendar.google.com"

# More results
$GAPI calendar list --max 50
```

### Create Event

```bash
# Basic event
$GAPI calendar create --summary "Team Standup" --start 2026-03-16T10:00:00-06:00 --end 2026-03-16T10:30:00-06:00

# With location
$GAPI calendar create --summary "Lunch" --start 2026-03-16T12:00:00Z --end 2026-03-16T13:00:00Z --location "Cafe"

# With attendees
$GAPI calendar create --summary "Review" --start 2026-03-16T14:00:00Z --end 2026-03-16T15:00:00Z --attendees "alice@co.com,bob@co.com"

# With description
$GAPI calendar create --summary "Study Session" --start 2026-03-16T16:00:00-06:00 --end 2026-03-16T18:00:00-06:00 --description "Chapter 5 review"
```

### Update Event

```bash
# Change time
$GAPI calendar update EVENT_ID --start 2026-03-16T11:00:00-06:00 --end 2026-03-16T11:30:00-06:00

# Change title
$GAPI calendar update EVENT_ID --summary "Updated Meeting Title"

# Change location
$GAPI calendar update EVENT_ID --location "Room 204"

# Multiple fields
$GAPI calendar update EVENT_ID --summary "New Title" --start 2026-03-16T14:00:00Z --end 2026-03-16T15:00:00Z --location "Online"
```

### Delete Event

```bash
$GAPI calendar delete EVENT_ID
```

## Output Format

**calendar list** returns:
```json
[{
  "id": "abc123",
  "summary": "Team Standup",
  "start": "2026-03-16T10:00:00-06:00",
  "end": "2026-03-16T10:30:00-06:00",
  "location": "Zoom",
  "description": "",
  "status": "confirmed",
  "htmlLink": "https://calendar.google.com/calendar/event?eid=..."
}]
```

**calendar create** returns:
```json
{"status": "created", "id": "abc123", "summary": "Team Standup", "htmlLink": "..."}
```

**calendar update** returns:
```json
{"status": "updated", "id": "abc123", "summary": "Updated Title", "htmlLink": "..."}
```

**calendar delete** returns:
```json
{"status": "deleted", "eventId": "abc123"}
```

## Todoist Integration — Preventing Overlap

**When scheduling tasks via the Todoist skill, ALWAYS check Google Calendar to prevent double-booking.**

### Workflow

1. **Get Todoist schedule** for the target date:
   ```bash
   TODOIST="python ~/.apollo/skills/productivity/todoist/scripts/todoist_api.py"
   $TODOIST get_scheduled 2026-03-16
   ```

2. **Get Google Calendar events** for the same date:
   ```bash
   $GAPI calendar list --start 2026-03-16T00:00:00Z --end 2026-03-16T23:59:59Z
   ```

3. **Merge busy time**: Combine Todoist `scheduled_tasks` and Calendar events into a unified busy-time list. Both contribute to blocking out time slots.

4. **Find gaps**: Subtract all busy time from the working hours window (default 08:00–22:00) to find available gaps.

5. **Schedule into gaps**: Pick the best available gap for the task:
   - Prefer morning gaps for deep work / complex tasks
   - Prefer afternoon gaps for meetings / lighter tasks
   - If no gap is large enough: inform the user and suggest the next available date

### Example

```
Todoist tasks on 2026-03-16:
  09:00–10:00  Team meeting
  14:00–16:00  Coding session

Calendar events on 2026-03-16:
  10:30–11:30  Doctor appointment
  12:00–13:00  Lunch with friend

Combined busy time: 09:00–10:00, 10:30–11:30, 12:00–13:00, 14:00–16:00

Available gaps: 08:00–09:00 (60m), 10:00–10:30 (30m), 11:30–12:00 (30m),
               13:00–14:00 (60m), 16:00–22:00 (360m)

→ A 90min task fits best in the 16:00–22:00 gap → schedule at 16:00–17:30
```

### When Calendar Is Not Set Up

If `$GSETUP --check` fails, schedule using Todoist tasks only — do not error. Mention to the user that setting up `google-calendar` would improve scheduling accuracy.

## Event Lookup for Time References

When other skills (especially Todoist) need to resolve a named event reference like "after track" or "before class", Google Calendar serves as the source of truth for event timing.

### How to Look Up an Event by Name

1. **Query the target date**:
   ```bash
   $GAPI calendar list --start 2026-03-16T00:00:00Z --end 2026-03-16T23:59:59Z
   ```

2. **Match by summary**: Search the returned events for one whose `summary` contains the referenced name (case-insensitive, partial match). Examples:
   - "track" matches "Track Practice", "Track & Field"
   - "class" matches "Math Class", "English Class" — if ambiguous, ask the user which one
   - "school" — look for the last class/event of the school day to determine when school ends

3. **Return the relevant time**:
   - For "after X": return the event's `end` time
   - For "before X": return the event's `start` time
   - For "during X": return both `start` and `end`

### Handling Edge Cases

- **Event not found**: The event may not be on the calendar (e.g., informal activities). Do not guess — ask the user: "I couldn't find '[name]' on your calendar for [date]. What time does it start/end?"
- **Recurring events**: The query is date-bounded, so it naturally returns the instance for the requested date. No special handling needed.
- **Ambiguous matches**: If multiple events partially match (e.g., "math" matches both "Math Class" and "Math Tutoring"), present the options and ask the user which one they mean.
- **Generic references**: "after school" is not a specific event name. Look for the last event of the school day (latest `end` time among school-related events). If unclear, ask: "What time does school end?"
- **Multi-day search**: If the user says "after track on Thursday" but today is Monday, query Thursday's date specifically.

## Rules

1. **Never create or delete events without confirming with the user first.** Show the event details and ask for approval.
2. **Check auth before first use** — run `$GSETUP --check`. If it fails, guide through `google-auth` setup.
3. **Calendar times must include timezone** — always use ISO 8601 with offset (e.g., `2026-03-16T10:00:00-06:00`) or UTC (`Z`).
4. **Respect rate limits** — avoid rapid-fire sequential API calls.
5. **When used with Todoist**, always merge both Todoist tasks and Calendar events before finding available time slots.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `NOT_AUTHENTICATED` | Load `google-auth` skill and follow setup |
| `REFRESH_FAILED` | Token expired — redo auth steps 3-5 in `google-auth` |
| `HttpError 403` | Calendar API not enabled or missing scope — revoke and re-auth |
| No events returned | Check date range; ensure `--start` and `--end` are correct ISO 8601 |
| Wrong calendar | Use `--calendar` flag with the calendar ID |
