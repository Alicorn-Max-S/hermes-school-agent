#!/usr/bin/env python3
"""Todoist API CLI for Apollo Agent.

A thin CLI wrapper around the Todoist API v1 (unified API).
Authenticates using a personal API token from environment variables.

Usage:
  python todoist_api.py list_tasks [--filter FILTER] [--project-id ID] [--label LABEL]
  python todoist_api.py get_task TASK_ID
  python todoist_api.py create_task --content "Task" [--description "..."] [--due-datetime ISO] [--due-string STR] [--due-date DATE] [--duration MINS] [--project-id ID] [--priority 1-4] [--labels "a,b"] [--deadline DATE]
  python todoist_api.py update_task TASK_ID [--content "..."] [--due-datetime ISO] [--duration MINS] ...
  python todoist_api.py complete_task TASK_ID
  python todoist_api.py delete_task TASK_ID
  python todoist_api.py list_projects
  python todoist_api.py create_project --name "Project Name" [--color COLOR] [--parent-id ID]
  python todoist_api.py list_labels
  python todoist_api.py get_scheduled DATE [--working-hours "08:00-22:00"]
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone

import requests


BASE_URL = "https://api.todoist.com/api/v1"


def _load_apollo_env_value(key: str) -> str:
    """Load a value from ~/.apollo/.env if not already in os.environ."""
    val = os.environ.get(key, "")
    if val:
        return val
    env_path = os.path.join(
        os.environ.get("APOLLO_HOME", os.path.join(os.path.expanduser("~"), ".apollo")),
        ".env",
    )
    try:
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    if k.strip() == key:
                        return v.strip().strip("\"'")
    except FileNotFoundError:
        pass
    return ""


TODOIST_API_TOKEN = _load_apollo_env_value("TODOIST_API_TOKEN")


def _check_config():
    """Validate required environment variables are set."""
    if not TODOIST_API_TOKEN:
        print(
            "Missing required environment variable: TODOIST_API_TOKEN\n"
            "Set it in ~/.apollo/.env or export it in your shell.\n"
            "See the todoist skill SKILL.md for setup instructions.",
            file=sys.stderr,
        )
        sys.exit(1)


def _headers():
    return {
        "Authorization": f"Bearer {TODOIST_API_TOKEN}",
        "Content-Type": "application/json",
    }


# =========================================================================
# Response helpers
# =========================================================================


def _unwrap_list(resp):
    """Unwrap a paginated v1 API response.

    The v1 API wraps list responses in {"results": [...], "next_cursor": ...}.
    This helper extracts the results array.  For non-paginated (single-object)
    responses, use resp.json() directly.
    """
    data = resp.json()
    if isinstance(data, dict) and "results" in data:
        return data["results"]
    # Fallback for unexpected shapes
    return data


# =========================================================================
# Helpers
# =========================================================================


def _parse_working_hours(wh_str: str):
    """Parse 'HH:MM-HH:MM' into (start_hour, start_min, end_hour, end_min)."""
    start, end = wh_str.split("-")
    sh, sm = int(start.split(":")[0]), int(start.split(":")[1])
    eh, em = int(end.split(":")[0]), int(end.split(":")[1])
    return sh, sm, eh, em


def _time_to_minutes(h, m):
    """Convert hours and minutes to total minutes since midnight."""
    return h * 60 + m


def _minutes_to_time(mins):
    """Convert total minutes since midnight to 'HH:MM' string."""
    return f"{mins // 60:02d}:{mins % 60:02d}"


def _user_to_api_priority(user_priority: int) -> int:
    """Convert user-facing priority (P1=urgent .. P4=normal) to API value.

    The Todoist API uses an inverted scale:
      App P1 (most urgent) = API priority 4
      App P2               = API priority 3
      App P3               = API priority 2
      App P4 (default)     = API priority 1
    """
    return 5 - user_priority


def _api_to_user_priority(api_priority: int) -> int:
    """Convert API priority value to user-facing priority (P1=urgent .. P4=normal)."""
    return 5 - api_priority


def _task_summary(task):
    """Extract a compact summary from a Todoist task object."""
    due = task.get("due") or {}
    duration = task.get("duration") or {}
    return {
        "id": task["id"],
        "content": task.get("content", ""),
        "description": task.get("description", ""),
        "due": {
            "date": due.get("date", ""),
            "datetime": due.get("datetime", ""),
            "string": due.get("string", ""),
            "timezone": due.get("timezone", ""),
            "is_recurring": due.get("is_recurring", False),
        } if due else None,
        "duration": {
            "amount": duration.get("amount"),
            "unit": duration.get("unit", "minute"),
        } if duration else None,
        "priority": _api_to_user_priority(task.get("priority", 1)),
        "project_id": task.get("project_id", ""),
        "labels": task.get("labels", []),
        "url": task.get("url", ""),
    }


# =========================================================================
# Commands
# =========================================================================


def list_tasks(args):
    """List active tasks with optional filtering.

    In API v1 the ``filter`` parameter was removed from GET /tasks.
    Filtered queries now use the dedicated GET /tasks/filter endpoint.
    """
    _check_config()
    try:
        if args.filter:
            # v1 uses a dedicated filter endpoint
            params = {"query": args.filter}
            resp = requests.get(f"{BASE_URL}/tasks/filter",
                                headers=_headers(), params=params, timeout=30)
        else:
            params = {}
            if args.project_id:
                params["project_id"] = args.project_id
            if args.label:
                params["label"] = args.label
            resp = requests.get(f"{BASE_URL}/tasks", headers=_headers(),
                                params=params, timeout=30)
        resp.raise_for_status()
    except requests.HTTPError as e:
        print(f"API error: {e.response.status_code} {e.response.text}",
              file=sys.stderr)
        sys.exit(1)
    tasks = _unwrap_list(resp)
    output = [_task_summary(t) for t in tasks]
    print(json.dumps(output, indent=2))


def get_task(args):
    """Get details for a single task."""
    _check_config()
    try:
        resp = requests.get(f"{BASE_URL}/tasks/{args.task_id}",
                            headers=_headers(), timeout=30)
        resp.raise_for_status()
    except requests.HTTPError as e:
        print(f"API error: {e.response.status_code} {e.response.text}",
              file=sys.stderr)
        sys.exit(1)
    print(json.dumps(_task_summary(resp.json()), indent=2))


def create_task(args):
    """Create a new task."""
    _check_config()
    body = {"content": args.content}
    if args.description:
        body["description"] = args.description
    if args.due_datetime:
        body["due_datetime"] = args.due_datetime
    elif args.due_string:
        body["due_string"] = args.due_string
    elif args.due_date:
        body["due_date"] = args.due_date
    if args.duration is not None:
        body["duration"] = {"amount": args.duration, "unit": "minute"}
    if args.project_id:
        body["project_id"] = args.project_id
    if args.priority is not None:
        body["priority"] = _user_to_api_priority(args.priority)
    if args.labels:
        body["labels"] = [l.strip() for l in args.labels.split(",")]
    if args.deadline:
        body["deadline"] = {"date": args.deadline}
    try:
        resp = requests.post(f"{BASE_URL}/tasks", headers=_headers(),
                             json=body, timeout=30)
        resp.raise_for_status()
    except requests.HTTPError as e:
        print(f"API error: {e.response.status_code} {e.response.text}",
              file=sys.stderr)
        sys.exit(1)
    print(json.dumps(_task_summary(resp.json()), indent=2))


def update_task(args):
    """Update an existing task."""
    _check_config()
    body = {}
    if args.content is not None:
        body["content"] = args.content
    if args.description is not None:
        body["description"] = args.description
    if args.due_datetime is not None:
        body["due_datetime"] = args.due_datetime
    elif args.due_string is not None:
        body["due_string"] = args.due_string
    elif args.due_date is not None:
        body["due_date"] = args.due_date
    if args.duration is not None:
        body["duration"] = {"amount": args.duration, "unit": "minute"}
    if args.project_id is not None:
        body["project_id"] = args.project_id
    if args.priority is not None:
        body["priority"] = _user_to_api_priority(args.priority)
    if args.labels is not None:
        body["labels"] = [l.strip() for l in args.labels.split(",")]
    if args.deadline is not None:
        body["deadline"] = {"date": args.deadline}
    if not body:
        print(json.dumps({"error": "No fields to update"}))
        sys.exit(1)
    try:
        resp = requests.post(f"{BASE_URL}/tasks/{args.task_id}",
                             headers=_headers(), json=body, timeout=30)
        resp.raise_for_status()
    except requests.HTTPError as e:
        print(f"API error: {e.response.status_code} {e.response.text}",
              file=sys.stderr)
        sys.exit(1)
    print(json.dumps(_task_summary(resp.json()), indent=2))


def complete_task(args):
    """Mark a task as complete."""
    _check_config()
    try:
        resp = requests.post(f"{BASE_URL}/tasks/{args.task_id}/close",
                             headers=_headers(), timeout=30)
        resp.raise_for_status()
    except requests.HTTPError as e:
        print(f"API error: {e.response.status_code} {e.response.text}",
              file=sys.stderr)
        sys.exit(1)
    print(json.dumps({"success": True, "task_id": args.task_id}))


def delete_task(args):
    """Delete a task."""
    _check_config()
    try:
        resp = requests.delete(f"{BASE_URL}/tasks/{args.task_id}",
                               headers=_headers(), timeout=30)
        resp.raise_for_status()
    except requests.HTTPError as e:
        print(f"API error: {e.response.status_code} {e.response.text}",
              file=sys.stderr)
        sys.exit(1)
    print(json.dumps({"success": True, "task_id": args.task_id, "deleted": True}))


def list_projects(args):
    """List all projects."""
    _check_config()
    try:
        resp = requests.get(f"{BASE_URL}/projects", headers=_headers(),
                            timeout=30)
        resp.raise_for_status()
    except requests.HTTPError as e:
        print(f"API error: {e.response.status_code} {e.response.text}",
              file=sys.stderr)
        sys.exit(1)
    projects = _unwrap_list(resp)
    output = [
        {
            "id": p["id"],
            "name": p.get("name", ""),
            "color": p.get("color", ""),
            "is_inbox_project": p.get("is_inbox_project", False),
            "is_favorite": p.get("is_favorite", False),
            "order": p.get("order", 0),
        }
        for p in projects
    ]
    print(json.dumps(output, indent=2))


def create_project(args):
    """Create a new project."""
    _check_config()
    body = {"name": args.name}
    if args.color:
        body["color"] = args.color
    if args.parent_id:
        body["parent_id"] = args.parent_id
    if args.is_favorite:
        body["is_favorite"] = True
    try:
        resp = requests.post(f"{BASE_URL}/projects", headers=_headers(),
                             json=body, timeout=30)
        resp.raise_for_status()
    except requests.HTTPError as e:
        print(f"API error: {e.response.status_code} {e.response.text}",
              file=sys.stderr)
        sys.exit(1)
    project = resp.json()
    print(json.dumps({
        "id": project["id"],
        "name": project.get("name", ""),
        "color": project.get("color", ""),
        "is_inbox_project": project.get("is_inbox_project", False),
        "is_favorite": project.get("is_favorite", False),
        "order": project.get("order", 0),
    }, indent=2))


def list_labels(args):
    """List all user labels."""
    _check_config()
    try:
        resp = requests.get(f"{BASE_URL}/labels", headers=_headers(),
                            timeout=30)
        resp.raise_for_status()
    except requests.HTTPError as e:
        print(f"API error: {e.response.status_code} {e.response.text}",
              file=sys.stderr)
        sys.exit(1)
    labels = _unwrap_list(resp)
    output = [
        {
            "id": l["id"],
            "name": l.get("name", ""),
            "color": l.get("color", ""),
            "order": l.get("order", 0),
            "is_favorite": l.get("is_favorite", False),
        }
        for l in labels
    ]
    print(json.dumps(output, indent=2))


def get_scheduled(args):
    """Get tasks scheduled for a date and compute available time gaps.

    Fetches all active tasks, filters to those due on the specified date,
    separates them into scheduled (have datetime + duration) and unscheduled
    (date only), then computes available gaps within working hours.
    """
    _check_config()
    target_date = args.date  # YYYY-MM-DD
    sh, sm, eh, em = _parse_working_hours(args.working_hours)
    work_start = _time_to_minutes(sh, sm)
    work_end = _time_to_minutes(eh, em)

    # Fetch tasks due on this date using the v1 filter endpoint
    params = {"query": f"due: {target_date}"}
    try:
        resp = requests.get(f"{BASE_URL}/tasks/filter", headers=_headers(),
                            params=params, timeout=30)
        resp.raise_for_status()
    except requests.HTTPError as e:
        print(f"API error: {e.response.status_code} {e.response.text}",
              file=sys.stderr)
        sys.exit(1)

    tasks = _unwrap_list(resp)

    scheduled = []
    unscheduled = []

    for task in tasks:
        due = task.get("due") or {}
        due_dt_str = due.get("datetime", "")
        duration_obj = task.get("duration") or {}
        duration_mins = duration_obj.get("amount", 30) if duration_obj else 30
        if duration_obj and duration_obj.get("unit") == "day":
            duration_mins = duration_obj["amount"] * 24 * 60

        if due_dt_str:
            # Parse the datetime to extract local time
            try:
                dt = datetime.fromisoformat(due_dt_str.replace("Z", "+00:00"))
                # Convert to local time
                local_dt = dt.astimezone()
                start_mins = _time_to_minutes(local_dt.hour, local_dt.minute)
                end_mins = start_mins + duration_mins
                scheduled.append({
                    "id": task["id"],
                    "content": task.get("content", ""),
                    "start": _minutes_to_time(start_mins),
                    "end": _minutes_to_time(min(end_mins, 24 * 60 - 1)),
                    "duration_minutes": duration_mins,
                    "priority": _api_to_user_priority(task.get("priority", 1)),
                    "labels": task.get("labels", []),
                    "_start_mins": start_mins,
                    "_end_mins": end_mins,
                })
            except (ValueError, TypeError):
                unscheduled.append({
                    "id": task["id"],
                    "content": task.get("content", ""),
                    "due_date": due.get("date", target_date),
                })
        else:
            unscheduled.append({
                "id": task["id"],
                "content": task.get("content", ""),
                "due_date": due.get("date", target_date),
            })

    # Sort scheduled tasks by start time
    scheduled.sort(key=lambda t: t["_start_mins"])

    # Compute gaps within working hours
    gaps = []
    cursor = work_start
    for task in scheduled:
        task_start = task["_start_mins"]
        task_end = task["_end_mins"]
        # Only consider tasks that overlap with working hours
        if task_end <= work_start or task_start >= work_end:
            continue
        effective_start = max(task_start, work_start)
        effective_end = min(task_end, work_end)
        if effective_start > cursor:
            gap_mins = effective_start - cursor
            gaps.append({
                "start": _minutes_to_time(cursor),
                "end": _minutes_to_time(effective_start),
                "duration_minutes": gap_mins,
            })
        cursor = max(cursor, effective_end)

    # Final gap after last task
    if cursor < work_end:
        gaps.append({
            "start": _minutes_to_time(cursor),
            "end": _minutes_to_time(work_end),
            "duration_minutes": work_end - cursor,
        })

    # Clean up internal keys from scheduled tasks
    for task in scheduled:
        del task["_start_mins"]
        del task["_end_mins"]

    total_scheduled = sum(t["duration_minutes"] for t in scheduled)
    total_available = sum(g["duration_minutes"] for g in gaps)

    output = {
        "date": target_date,
        "working_hours": {
            "start": _minutes_to_time(work_start),
            "end": _minutes_to_time(work_end),
        },
        "scheduled_tasks": scheduled,
        "unscheduled_tasks": unscheduled,
        "available_gaps": gaps,
        "total_scheduled_minutes": total_scheduled,
        "total_available_minutes": total_available,
    }
    print(json.dumps(output, indent=2))


# =========================================================================
# CLI parser
# =========================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Todoist API CLI for Apollo Agent"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # --- list_tasks ---
    p = sub.add_parser("list_tasks", help="List active tasks")
    p.add_argument("--filter", default="", help="Todoist filter string")
    p.add_argument("--project-id", default=None, help="Filter by project ID")
    p.add_argument("--label", default=None, help="Filter by label")
    p.set_defaults(func=list_tasks)

    # --- get_task ---
    p = sub.add_parser("get_task", help="Get a single task's details")
    p.add_argument("task_id", help="Todoist task ID")
    p.set_defaults(func=get_task)

    # --- create_task ---
    p = sub.add_parser("create_task", help="Create a new task")
    p.add_argument("--content", required=True, help="Task content/title")
    p.add_argument("--description", default="", help="Task description")
    p.add_argument("--due-datetime", default=None,
                    help="Due datetime (ISO 8601, e.g. 2026-03-15T14:00:00Z)")
    p.add_argument("--due-string", default=None,
                    help="Natural language due string (e.g. 'tomorrow at 2pm')")
    p.add_argument("--due-date", default=None, help="Due date (YYYY-MM-DD)")
    p.add_argument("--duration", type=int, default=None,
                    help="Duration in minutes")
    p.add_argument("--project-id", default=None, help="Project ID")
    p.add_argument("--priority", type=int, default=None,
                    help="Priority 1-4 (1=most urgent, matches Todoist P1-P4)")
    p.add_argument("--labels", default=None,
                    help="Comma-separated labels")
    p.add_argument("--deadline", default=None,
                    help="Deadline date (YYYY-MM-DD)")
    p.set_defaults(func=create_task)

    # --- update_task ---
    p = sub.add_parser("update_task", help="Update an existing task")
    p.add_argument("task_id", help="Task ID to update")
    p.add_argument("--content", default=None)
    p.add_argument("--description", default=None)
    p.add_argument("--due-datetime", default=None)
    p.add_argument("--due-string", default=None)
    p.add_argument("--due-date", default=None)
    p.add_argument("--duration", type=int, default=None)
    p.add_argument("--project-id", default=None)
    p.add_argument("--priority", type=int, default=None)
    p.add_argument("--labels", default=None)
    p.add_argument("--deadline", default=None)
    p.set_defaults(func=update_task)

    # --- complete_task ---
    p = sub.add_parser("complete_task", help="Mark a task as complete")
    p.add_argument("task_id", help="Task ID to complete")
    p.set_defaults(func=complete_task)

    # --- delete_task ---
    p = sub.add_parser("delete_task", help="Delete a task")
    p.add_argument("task_id", help="Task ID to delete")
    p.set_defaults(func=delete_task)

    # --- list_projects ---
    p = sub.add_parser("list_projects", help="List all projects")
    p.set_defaults(func=list_projects)

    # --- create_project ---
    p = sub.add_parser("create_project", help="Create a new project")
    p.add_argument("--name", required=True, help="Project name")
    p.add_argument("--color", default=None, help="Project color")
    p.add_argument("--parent-id", default=None, help="Parent project ID")
    p.add_argument("--is-favorite", action="store_true", help="Mark as favorite")
    p.set_defaults(func=create_project)

    # --- list_labels ---
    p = sub.add_parser("list_labels", help="List all user labels")
    p.set_defaults(func=list_labels)

    # --- get_scheduled ---
    p = sub.add_parser("get_scheduled",
                        help="Get tasks for a date with available time gaps")
    p.add_argument("date", help="Date to check (YYYY-MM-DD)")
    p.add_argument("--working-hours", default="08:00-22:00",
                    help="Working hours range (default: 08:00-22:00)")
    p.set_defaults(func=get_scheduled)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
