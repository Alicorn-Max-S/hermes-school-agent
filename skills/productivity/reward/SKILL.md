---
name: reward
description: "Track and log rewards for completing school tasks. Trigger when user says they completed a task, want to create a task, or mentions rewarding themselves. Logs rewards to Google Sheets and predicts future rewards after enough history."
version: 1.0.0
author: Nous Research
license: MIT
metadata:
  hermes:
    tags: [Reward, School, Motivation, Google Sheets, Task]
    related_skills: [google-auth]
    school: true
    school_category: "Productivity"
---

# Reward Tracker

Track rewards for completing school tasks. Logs to Google Sheets and learns to predict rewards after 10 completed tasks.

**IMPORTANT**: All tool references (`terminal`, `clarify`, `memory`, `skill_view`) are **agent tools** — invoke them as tool calls, NOT as Python imports.

## Prerequisites

Requires Google OAuth2 setup via the `google-auth` skill:

```bash
GSETUP="python ~/.hermes/skills/productivity/google-auth/scripts/setup.py"
$GSETUP --check
```

If not authenticated, load `google-auth`: `skill_view("google-auth")`

## Helper Script

```bash
REWARD="python ~/.hermes/skills/productivity/reward/scripts/reward_store.py"
```

## First-Time Setup

On first use (or if no config exists), walk the user through setup:

1. **Check for existing config:**
   ```bash
   $REWARD config --get
   ```

2. **If no config exists**, ask the user using `clarify`:

   a. **Google Sheets document** — Ask for the Sheet URL or ID. Extract the sheet ID from the URL if needed (the part between `/d/` and `/edit`).

   b. **Reward type** — What kind of reward? Options:
      - Money (dollar amount)
      - Screen time (minutes)
      - Food/treats
      - Points (custom point system)
      - Custom (user defines their own type and unit)

   c. **Value determination method** — How should reward values be decided? Options:
      - **Random within range**: Pick a random value between a min and max based on task difficulty (e.g., easy=$1-3, medium=$3-7, hard=$7-15)
      - **Set value by class**: Fixed reward per task category/subject (e.g., Math=$5, English=$3)
      - **Custom per task**: User specifies the exact reward each time

   d. **Value parameters** — Based on the method chosen:
      - For random range: ask for min and max values per difficulty level (easy, medium, hard)
      - For set value by class: ask for the classes/subjects and their fixed reward values
      - For custom: no additional params needed

3. **Save the config:**
   ```bash
   $REWARD config --set --sheet-id "SHEET_ID" --reward-type "money" --value-method "random_range" --value-params '{"easy": [1, 3], "medium": [3, 7], "hard": [7, 15]}'
   ```

## Task Completion Flow

When the user says they completed a task or want to log one:

### Step 1: Load Config
```bash
$REWARD config --get
```
If no config, run First-Time Setup above.

### Step 2: Collect Task Details

Ask the user for:
- **Task name**: What did they complete? (e.g., "Math homework Ch. 5")
- **Description**: Brief details (e.g., "30 algebra problems on quadratic equations")
- **Subject/class**: School subject (e.g., "Math", "English", "Science")
- **Difficulty**: easy, medium, or hard (used for reward calculation)

### Step 3: Determine the Reward

Check if prediction is available:
```bash
$REWARD history --can-predict
```

**If fewer than 10 tasks logged** (can_predict = false):
- Ask the user: "What reward did you give yourself for this task?"
- The user provides the reward value

**If 10 or more tasks logged** (can_predict = true):
- Load the history summary:
  ```bash
  $REWARD history --summary
  ```
- Analyze the history to suggest a specific reward:
  - Look at similar tasks (same subject, same difficulty)
  - Calculate the average reward for that category
  - Factor in the value method from config (random range → pick within range, set value → use fixed value)
- Present the suggestion: "Based on your history, I'd suggest a reward of **$X** for this task. Does that work?"
- User confirms or overrides

### Step 4: Log the Reward

Save to local history:
```bash
$REWARD history --add --task "Task name" --description "Description" --class "Subject" --difficulty "medium" --reward 5.00 --reward-type "money"
```

Append to Google Sheets:
```bash
GAPI="python ~/.hermes/skills/productivity/google-auth/scripts/google_api.py"
$GAPI sheets append SHEET_ID "Sheet1!A:F" --values '[["2026-03-16T10:30:00", "Task name", "Description", "Subject", "5.00", "money"]]'
```

Use the actual timestamp, task details, and reward values. The sheet range should come from the saved config (default: `Sheet1!A:F`).

### Step 5: Confirm

Show a summary to the user:
- Task completed
- Reward earned
- Total tasks logged
- Running stats (if available)

## Creating a New Task

When the user says they want to **create** a task (not complete one):

1. Ask for task details (name, description, subject, difficulty)
2. If prediction is available (>=10 tasks), suggest what the reward could be
3. Tell the user: "Complete this task, then come back and tell me when you're done to log your reward!"
4. Do NOT log to Google Sheets yet — only log when the task is completed

## Prediction Logic

After 10 tasks, use the history summary to predict rewards:

1. **Group by subject and difficulty** — what's the average reward for similar tasks?
2. **Respect the value method**:
   - Random range: pick a value within the configured range for that difficulty, weighted toward the historical average
   - Set value by class: use the fixed value for that subject
   - Custom: suggest the average of past rewards for similar tasks
3. **Present confidently** — suggest a specific value, not a range. The user can always override.

## Rules

1. **Always confirm with the user** before logging a reward to Google Sheets
2. **Check auth before first use** — run `$GSETUP --check`
3. **Be encouraging** — celebrate completed tasks, motivate the student
4. **Never fabricate history** — only use actual logged data for predictions
5. **Save preferences to memory** — after setup, save the reward type and sheet ID to memory for quick reference
