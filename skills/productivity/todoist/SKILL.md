---
name: todoist
description: "Todoist task and homework management — create tasks, set due dates, schedule study sessions, track assignments, estimate durations, auto-label by project, and log time for accuracy. Trigger on mentions of to-do lists, task planning, homework tracking, or time management."
version: 1.0.0
author: community
license: MIT
prerequisites:
  env_vars: [TODOIST_API_TOKEN]
metadata:
  apollo:
    tags: [Todoist, Tasks, Productivity, Scheduling, Time Management, Calendar]
    school: true
    school_category: "Homework & Assignments"
    related_skills: [google-calendar, school, canvas-lms]
---

# Todoist — Intelligent Task Management & Scheduling

Create, manage, and intelligently schedule Todoist tasks. Automatically estimates duration, priority, and labels. Tracks actual task duration to improve future estimates.

## Scripts

- `scripts/todoist_api.py` — Python CLI for Todoist API calls

## Setup

1. Open [Todoist web app](https://app.todoist.com)
2. Go to **Settings → Integrations → Developer**
3. Copy your **API token**
4. Add to `~/.apollo/.env`:

```
TODOIST_API_TOKEN=your_token_here
```

**Optional — Google Calendar:** If the `google-calendar` skill is set up (requires `google-auth` for OAuth2), scheduling will also check Google Calendar events to avoid double-booking. This is strongly recommended but not required.

## Step 0: Verify Setup

Before proceeding, verify that TODOIST_API_TOKEN is set. Use terminal to run: `echo $TODOIST_API_TOKEN | head -c5`. If empty, inform the user they need to get their API token from https://todoist.com/app/settings/integrations/developer

## Usage

```bash
TODOIST="python ~/.apollo/skills/productivity/todoist/scripts/todoist_api.py"

# List all active tasks
$TODOIST list_tasks

# List tasks with a filter
$TODOIST list_tasks --filter "today | overdue"

# List tasks by project
$TODOIST list_tasks --project-id 2345678

# List tasks by label
$TODOIST list_tasks --label "school"

# Get a single task's details
$TODOIST get_task 1234567890

# Create a task with all fields (priority 2 = P2/high, matches Todoist app)
$TODOIST create_task --content "Write research paper intro" --due-datetime "2026-03-16T10:00:00Z" --duration 120 --priority 2 --labels "school,writing" --deadline "2026-03-20"

# Create a task with natural language due date
$TODOIST create_task --content "Team meeting" --due-string "tomorrow at 2pm" --duration 60

# Update a task (priority 1 = P1/urgent, matches Todoist app)
$TODOIST update_task 1234567890 --duration 90 --priority 1

# Mark a task as complete
$TODOIST complete_task 1234567890

# Delete a task (ALWAYS confirm with user first)
$TODOIST delete_task 1234567890

# List all projects
$TODOIST list_projects

# Create a project (for grouping related tasks)
$TODOIST create_project --name "Essay — Climate Change"

# List all labels (useful for label suggestions)
$TODOIST list_labels

# Get schedule for a date (shows tasks + available gaps)
$TODOIST get_scheduled 2026-03-16

# Get schedule with custom working hours
$TODOIST get_scheduled 2026-03-16 --working-hours "10:00-18:00"
```

## Output Format

**list_tasks** returns:
```json
[{
  "id": "1234567890",
  "content": "Write report",
  "description": "Q1 summary",
  "due": {"date": "2026-03-16", "datetime": "2026-03-16T10:00:00Z", "string": "Mar 16 10:00 AM", "timezone": "America/New_York", "is_recurring": false},
  "duration": {"amount": 60, "unit": "minute"},
  "priority": 2,
  "project_id": "2345678",
  "labels": ["work"],
  "url": "https://todoist.com/showTask?id=1234567890"
}]
```

**get_scheduled** returns:
```json
{
  "date": "2026-03-16",
  "working_hours": {"start": "08:00", "end": "22:00"},
  "scheduled_tasks": [
    {"id": "123", "content": "Team meeting", "start": "09:00", "end": "10:00", "duration_minutes": 60, "priority": 2, "labels": ["work"]},
    {"id": "456", "content": "Coding session", "start": "14:00", "end": "16:00", "duration_minutes": 120, "priority": 3, "labels": ["work", "coding"]}
  ],
  "unscheduled_tasks": [
    {"id": "789", "content": "Buy groceries", "due_date": "2026-03-16"}
  ],
  "available_gaps": [
    {"start": "08:00", "end": "09:00", "duration_minutes": 60},
    {"start": "10:00", "end": "14:00", "duration_minutes": 240},
    {"start": "16:00", "end": "22:00", "duration_minutes": 360}
  ],
  "total_scheduled_minutes": 180,
  "total_available_minutes": 660
}
```

**list_labels** returns:
```json
[{"id": "456", "name": "school", "color": "blue", "order": 1, "is_favorite": false}]
```

**create_task / get_task / update_task** return the task summary object (same shape as list_tasks items).

**complete_task** returns:
```json
{"success": true, "task_id": "1234567890"}
```

**delete_task** returns:
```json
{"success": true, "task_id": "1234567890", "deleted": true}
```

## Scheduling Workflow

**When creating a task, ALWAYS follow this workflow:**

### Step 1: Gather Info

Extract from the user's request: content, description, and any explicitly provided duration, priority, deadline, or labels.

### Step 2: Resolve Relative Time References

If the user references a calendar event by name to anchor the task's timing (e.g., "after track", "before dinner", "between math and English", "when practice ends"), you MUST look up that event on Google Calendar before proceeding.

1. **Query Google Calendar** for the relevant date:
   ```bash
   GAPI="python ~/.apollo/skills/productivity/google-auth/scripts/google_api.py"
   $GAPI calendar list --start 2026-03-16T00:00:00Z --end 2026-03-16T23:59:59Z
   ```

2. **Search the results** for an event whose `summary` matches the referenced name (case-insensitive, partial match). For example, "track" should match "Track Practice", "Track & Field", etc.

3. **Extract the anchor time**:
   - "after X" → use the event's `end` time as the earliest start time for the new task
   - "before X" → use the event's `start` time as the latest end time (schedule the task to finish before it)
   - "between X and Y" → find both events and schedule within the gap between them

4. **If the event is NOT found** on the calendar for that date:
   - Ask the user: "I couldn't find '[event name]' on your calendar for [date]. What time does it end?" (or start, depending on the reference)
   - Do NOT guess or silently skip — the whole point is to anchor to the real time

5. **If multiple matching events are found** (e.g., "Math" matching "Math Class" and "Math Tutoring"):
   - Pick the one on the target date. If there are still multiple, ask the user which one they mean.

6. **If Google Calendar is not set up**:
   - Ask the user directly: "What time does [event] end/start? (I don't have Google Calendar access to look it up)"

Use the resolved time as a hard constraint in Step 5 (Find a Time Slot) — the task must start after/before the anchor time, not just fit into any available gap.

### Step 3: Estimate Missing Fields

For any field NOT explicitly provided by the user, estimate it:

**Duration** — Estimate from the task title/description:
- Quick tasks (reply to email, review a doc, make a call, quick errand): **15 min**
- Medium tasks (write a short report, attend a meeting, short assignment, workout): **30–60 min**
- Complex tasks (coding project, research, essay writing, studying a chapter): **90–120 min**
- Deep work (major project milestone, exam prep, thesis writing, full study session): **120 min** (but see "Breaking Up Large Tasks" below)

**IMPORTANT:** A task can only have a duration if it also has a specific start time (`--due-datetime`). Do NOT set `--duration` on tasks that only have a date (`--due-date`) or natural language due (`--due-string` without a time). If the user provides a duration but no start time, you must also find and assign a start time (see Step 4) before creating the task.

Before estimating, check your memory for past duration corrections. Search for entries containing "duration accuracy" — these record how long similar tasks actually took in the past. Adjust your estimate based on this user-specific data.

**Breaking Up Large Tasks** — If a task would take more than **120 minutes** (2 hours), break it into smaller tasks organized under a **dedicated project** instead of creating one giant task. For example, "Write essay on climate change" should become:

1. Create a project: "Essay — Climate Change"
2. Create individual tasks inside that project:
   - "Identify key quotes and sources" (60 min)
   - "Write general structure / outline" (30 min)
   - "Write rough draft" (90 min)
   - "Revise and write final draft" (90 min)

Each task gets its own duration, priority, labels, and scheduled time slot. Present the full breakdown to the user for confirmation before creating anything. The project groups everything together so the user can track overall progress.

**Priority** — Uses the same P1–P4 scale as the Todoist app (P1 = most urgent). The `--priority` flag accepts 1–4 where 1 is most urgent. The script automatically converts to the inverted API values internally.

Infer priority from urgency and importance cues. These are default guidelines — the user can override them at any time:

- **P1 (urgent)** `--priority 1`: Overdue tasks. Due today with a hard deadline. Explicitly marked urgent by the user. Exam/submission due within 24 hours.
- **P2 (high)** `--priority 2`: Important task with a clear deadline approaching (within 2–3 days). Tasks the user described as "important" or "high priority". Assignments due this week.
- **P3 (medium)** `--priority 3`: Somewhat important with a soft or distant deadline. Recurring responsibilities. Tasks due next week.
- **P4 (normal/default)** `--priority 4`: Routine tasks with no deadline pressure. Nice-to-do items. No urgency or importance cues present.

**Labels** — First run `$TODOIST list_labels` to see the user's existing labels. Reuse existing labels whenever they fit. Infer label from context:
- Academic/homework/studying → look for "school", "homework", "study" labels
- Work/professional → look for "work", "meeting" labels
- Personal/errands → look for "personal", "errands" labels
- Health/exercise → look for "health", "fitness" labels

If no matching label exists, **create a new one** — don't skip labeling just because the label doesn't exist yet. Simply include the new label name in `--labels` and Todoist will create it automatically.

**Projects** — Run `$TODOIST list_projects` to see existing projects. Assign tasks to the most relevant project. If no suitable project exists, you can create a new one. Organizing tasks into projects helps the user keep related work together (e.g. a "School" project for all academic tasks, a "Home" project for chores).

**Deadline** — Only set if the user explicitly mentions a deadline ("due Friday", "by end of week", "submit by March 20"). Do NOT set a deadline if none is mentioned.

### Step 4: Confirm Guessed Fields

If you estimated ANY field (duration, priority, labels, or deadline) rather than the user explicitly providing it, you MUST present a summary and ask for confirmation before creating:

```
Here's what I'll create:
- Task: "Write research paper intro"
- Duration: 120 min (estimated — complex writing task)
- Priority: P2/High (estimated — academic deadline approaching)
- Labels: school (estimated — matches your existing label)
- Deadline: 2026-03-20 (from "by next Friday")
- Scheduled: 2026-03-16 10:00–12:00 (first available 2h gap)

Want me to adjust anything before creating this task?
```

Wait for the user to confirm or request changes before proceeding.

### Step 5: Find a Time Slot

1. Run `$TODOIST get_scheduled DATE` for the target date to see existing tasks and available gaps.

2. **Also check Google Calendar** (if the `google-calendar` skill is set up):
   ```bash
   GAPI="python ~/.apollo/skills/productivity/google-auth/scripts/google_api.py"
   $GAPI calendar list --start 2026-03-16T00:00:00Z --end 2026-03-16T23:59:59Z
   ```
   This captures meetings and calendar events not tracked in Todoist. Treat calendar events as busy time when looking for gaps.

3. Merge Todoist tasks and Google Calendar events into a combined view of busy time.

4. Find a gap in `available_gaps` that fits the duration. Prefer earlier gaps (morning) for deep work and later gaps for lighter tasks.

5. If Step 2 resolved a time anchor (e.g., "after track ends at 4:30 PM"), only consider gaps that respect the anchor — gaps starting at or after the anchor time for "after" references, or ending at or before the anchor time for "before" references. The anchor is a hard constraint, not a preference.

6. If no gap is large enough on the requested date:
   - Inform the user: "No available gap on DATE for a Xmin task."
   - Suggest the next date with availability.
   - Ask if they want to override and schedule anyway.

7. If Google Calendar is not set up (`google-calendar` skill), schedule using Todoist tasks only — do not error.

### Step 6: Create the Task

Create the task with ALL fields set:
```bash
$TODOIST create_task --content "..." --due-datetime "..." --duration N --priority P --labels "..." --deadline "..."
```

## Time Tracking & Accuracy Improvement

### Recording Actual Duration

When a user tells you they are **starting** a task, note the current time.

When they say they **finished**, calculate the elapsed time and compare it to the estimated duration.

### After Task Completion

When a task is completed (user says "done with X" or you run `complete_task`), follow up:

> "You completed **[task name]**. It was estimated at **[N] minutes** — did it actually take about that long, or was it different?"

If the user provides a correction (e.g., "it actually took 45 minutes" or "way longer, like 2 hours"):

1. Save the insight to memory for future estimates:
   ```
   Use the memory tool: add "Duration accuracy: [task category] tasks (e.g. 'writing reports') — estimated [N]min, actually took [M]min. User tends to [take longer/be faster] than estimated for this type."
   ```

2. If there's already a duration accuracy entry for this task type, use `replace` instead of `add` to update it with the latest data.

3. Over time, these entries calibrate your estimates for this specific user. Before estimating duration for new tasks, always check memory for relevant "duration accuracy" entries.

### Label Accuracy

Similarly, if you assign a label and the user corrects it, save the preference:
```
Use the memory tool: add "Label preference: user prefers '[correct_label]' for [task type] tasks, not '[guessed_label]'."
```

## Rules

- `list_tasks`, `get_task`, `list_projects`, `list_labels`, `get_scheduled` are **read-only**
- `create_task` **MUST** always include `--duration` — estimate if the user doesn't provide one. However, `--duration` requires `--due-datetime` (a specific start time) — never set duration without a start time
- Tasks estimated at more than **120 minutes** should be broken into smaller tasks under a dedicated project
- `delete_task` **MUST** be confirmed with the user before execution
- If you estimated any of duration/priority/labels/deadline, you **MUST** confirm with the user before creating
- On first use, verify auth by running `$TODOIST list_projects` — if it fails with 401/403, guide the user through setup
- Working hours default to **08:00–22:00** — respect the user's schedule
- Todoist rate limit: 1000 requests per 15 minutes

## Troubleshooting

| Problem | Fix |
|---------|-----|
| 401 Unauthorized | Token invalid — regenerate in Todoist Settings → Integrations → Developer |
| 403 Forbidden | Token lacks required permissions |
| Empty task list | Check filter syntax or try without `--filter` |
| Rate limit hit | Wait a few minutes; Todoist allows 1000 requests per 15 min |
| Timezone mismatch | Tasks may display in UTC; the script converts to local time for scheduling |
| Google Calendar not available | Set up `google-calendar` skill (requires `google-auth`). Schedule with Todoist tasks only — this is fine, just less accurate |
| `get_scheduled` shows no gaps | Day is fully booked — suggest an alternative date |
| Duration not saved | Ensure `--duration` flag is provided (integer minutes) |

## API Reference (curl)

**Note:** Todoist migrated from REST API v2 to the unified API v1 in early 2026. The REST v2 endpoints are no longer available.

```bash
# List all tasks
curl -s -H "Authorization: Bearer $TODOIST_API_TOKEN" \
  "https://api.todoist.com/api/v1/tasks"

# Filter tasks (filter param moved to dedicated endpoint)
curl -s -H "Authorization: Bearer $TODOIST_API_TOKEN" \
  "https://api.todoist.com/api/v1/tasks/filter?query=today"

# Create a task with duration (duration is now a nested object)
# NOTE: API priority is inverted from the app — P1 (urgent) = API priority 4, P4 (normal) = API priority 1.
# The todoist_api.py script handles this conversion automatically.
curl -s -X POST -H "Authorization: Bearer $TODOIST_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "Team meeting", "due_datetime": "2026-03-16T14:00:00Z", "duration": {"amount": 60, "unit": "minute"}, "priority": 3, "labels": ["work"]}' \
  "https://api.todoist.com/api/v1/tasks"

# Complete a task
curl -s -X POST -H "Authorization: Bearer $TODOIST_API_TOKEN" \
  "https://api.todoist.com/api/v1/tasks/TASK_ID/close"

# List projects
curl -s -H "Authorization: Bearer $TODOIST_API_TOKEN" \
  "https://api.todoist.com/api/v1/projects"

# List labels
curl -s -H "Authorization: Bearer $TODOIST_API_TOKEN" \
  "https://api.todoist.com/api/v1/labels"
```

### v1 API Key Differences from REST v2

| Change | REST v2 | API v1 |
|--------|---------|--------|
| Base URL | `/rest/v2` | `/api/v1` |
| List responses | Bare JSON array | `{"results": [...], "next_cursor": ...}` |
| Task filtering | `GET /tasks?filter=...` | `GET /tasks/filter?query=...` |
| Duration in request body | `"duration": 60, "duration_unit": "minute"` | `"duration": {"amount": 60, "unit": "minute"}` |
| IDs | Numeric (e.g. `7246645180`) | Alphanumeric (e.g. `69mF7QcCj9JmXxp8`) |
| Priority | Inverted: API 4 = app P1 (urgent), API 1 = app P4 (normal) | Same inversion — `todoist_api.py` converts automatically |
