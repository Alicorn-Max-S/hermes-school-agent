---
name: todoist
description: Todoist task management with intelligent scheduling, duration estimation, automatic labeling, and time tracking for accuracy improvement.
version: 1.0.0
author: community
license: MIT
prerequisites:
  env_vars: [TODOIST_API_TOKEN]
metadata:
  hermes:
    tags: [Todoist, Tasks, Productivity, Scheduling, Time Management, Calendar]
---

# Todoist — Intelligent Task Management & Scheduling

Create, manage, and intelligently schedule Todoist tasks. Automatically estimates duration, priority, and labels. Tracks actual task duration to improve future estimates.

## Scripts

- `scripts/todoist_api.py` — Python CLI for Todoist API calls

## Setup

1. Open [Todoist web app](https://app.todoist.com)
2. Go to **Settings → Integrations → Developer**
3. Copy your **API token**
4. Add to `~/.hermes/.env`:

```
TODOIST_API_TOKEN=your_token_here
```

**Optional — Google Calendar:** If the `google-workspace` skill is set up, scheduling will also check Google Calendar events to avoid double-booking. This is strongly recommended but not required.

## Usage

```bash
TODOIST="python ~/.hermes/skills/productivity/todoist/scripts/todoist_api.py"

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

# Create a task with all fields
$TODOIST create_task --content "Write research paper intro" --due-datetime "2026-03-16T10:00:00Z" --duration 120 --priority 3 --labels "school,writing" --deadline "2026-03-20"

# Create a task with natural language due date
$TODOIST create_task --content "Team meeting" --due-string "tomorrow at 2pm" --duration 60

# Update a task
$TODOIST update_task 1234567890 --duration 90 --priority 4

# Mark a task as complete
$TODOIST complete_task 1234567890

# Delete a task (ALWAYS confirm with user first)
$TODOIST delete_task 1234567890

# List all projects
$TODOIST list_projects

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

### Step 2: Estimate Missing Fields

For any field NOT explicitly provided by the user, estimate it:

**Duration** — Estimate from the task title/description:
- Quick tasks (reply to email, review a doc, make a call, quick errand): **15 min**
- Medium tasks (write a short report, attend a meeting, short assignment, workout): **30–60 min**
- Complex tasks (coding project, research, essay writing, studying a chapter): **90–120 min**
- Deep work (major project milestone, exam prep, thesis writing, full study session): **120–240 min**

**IMPORTANT:** A task can only have a duration if it also has a specific start time (`--due-datetime`). Do NOT set `--duration` on tasks that only have a date (`--due-date`) or natural language due (`--due-string` without a time). If the user provides a duration but no start time, you must also find and assign a start time (see Step 4) before creating the task.

Before estimating, check your memory for past duration corrections. Search for entries containing "duration accuracy" — these record how long similar tasks actually took in the past. Adjust your estimate based on this user-specific data.

**Breaking Up Large Tasks** — If a task would take more than **240 minutes** (4 hours), break it into smaller subtasks instead of creating one giant task. For example, "Write research paper" should become separate tasks like "Write introduction", "Write methodology section", "Write results & analysis", etc. Each subtask should have its own duration, priority, and scheduling. Present the breakdown to the user for confirmation before creating.

**Priority** — Infer from urgency and importance cues:
- 1 (normal): Routine tasks, no deadline pressure
- 2 (medium): Somewhat important, soft deadline
- 3 (high): Important with a clear deadline approaching
- 4 (urgent): Overdue, due today, or explicitly urgent

**Labels** — First run `$TODOIST list_labels` to see the user's existing labels. Reuse existing labels whenever they fit. Infer label from context:
- Academic/homework/studying → look for "school", "homework", "study" labels
- Work/professional → look for "work", "meeting" labels
- Personal/errands → look for "personal", "errands" labels
- Health/exercise → look for "health", "fitness" labels

If no matching label exists, **create a new one** — don't skip labeling just because the label doesn't exist yet. Simply include the new label name in `--labels` and Todoist will create it automatically.

**Projects** — Run `$TODOIST list_projects` to see existing projects. Assign tasks to the most relevant project. If no suitable project exists, you can create a new one. Organizing tasks into projects helps the user keep related work together (e.g. a "School" project for all academic tasks, a "Home" project for chores).

**Deadline** — Only set if the user explicitly mentions a deadline ("due Friday", "by end of week", "submit by March 20"). Do NOT set a deadline if none is mentioned.

### Step 3: Confirm Guessed Fields

If you estimated ANY field (duration, priority, labels, or deadline) rather than the user explicitly providing it, you MUST present a summary and ask for confirmation before creating:

```
Here's what I'll create:
- Task: "Write research paper intro"
- Duration: 120 min (estimated — complex writing task)
- Priority: 3/High (estimated — academic deadline approaching)
- Labels: school (estimated — matches your existing label)
- Deadline: 2026-03-20 (from "by next Friday")
- Scheduled: 2026-03-16 10:00–12:00 (first available 2h gap)

Want me to adjust anything before creating this task?
```

Wait for the user to confirm or request changes before proceeding.

### Step 4: Find a Time Slot

1. Run `$TODOIST get_scheduled DATE` for the target date to see existing tasks and available gaps.

2. **Also check Google Calendar** (if the google-workspace skill is set up):
   ```bash
   GAPI="python ~/.hermes/skills/productivity/google-workspace/scripts/google_api.py"
   $GAPI calendar list --start 2026-03-16T00:00:00Z --end 2026-03-16T23:59:59Z
   ```
   This captures meetings and calendar events not tracked in Todoist. Treat calendar events as busy time when looking for gaps.

3. Merge Todoist tasks and Google Calendar events into a combined view of busy time.

4. Find a gap in `available_gaps` that fits the duration. Prefer earlier gaps (morning) for deep work and later gaps for lighter tasks.

5. If no gap is large enough on the requested date:
   - Inform the user: "No available gap on DATE for a Xmin task."
   - Suggest the next date with availability.
   - Ask if they want to override and schedule anyway.

6. If Google Calendar is not set up, schedule using Todoist tasks only — do not error.

### Step 5: Create the Task

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
- Tasks estimated at more than **240 minutes** should be broken into smaller subtasks
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
| Google Calendar not available | Schedule with Todoist tasks only — this is fine, just less accurate |
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
