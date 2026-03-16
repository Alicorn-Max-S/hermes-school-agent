#!/usr/bin/env python3
"""Reward Tracker storage helper.

Manages local JSON persistence for reward configuration and task/reward history.

Usage:
  python reward_store.py config --get
  python reward_store.py config --set --sheet-id ID --reward-type money --value-method random_range [--value-params '{}']
  python reward_store.py history --add --task "name" --description "desc" --class "Math" --difficulty "medium" --reward 5.00 --reward-type money
  python reward_store.py history --summary
  python reward_store.py history --list
  python reward_store.py history --can-predict
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

APOLLO_HOME = Path(os.getenv("APOLLO_HOME", Path.home() / ".apollo"))
CONFIG_PATH = APOLLO_HOME / "reward_config.json"
HISTORY_PATH = APOLLO_HOME / "reward_history.json"

PREDICTION_THRESHOLD = 10


def load_config():
    """Load reward configuration."""
    if not CONFIG_PATH.exists():
        return None
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def save_config(config):
    """Save reward configuration."""
    APOLLO_HOME.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")


def load_history():
    """Load task/reward history."""
    if not HISTORY_PATH.exists():
        return []
    try:
        return json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def save_history(history):
    """Save task/reward history."""
    APOLLO_HOME.mkdir(parents=True, exist_ok=True)
    HISTORY_PATH.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")


def add_entry(task_name, description, task_class, difficulty, reward_value, reward_type):
    """Add a new task/reward entry to history."""
    history = load_history()
    entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "task_name": task_name,
        "description": description,
        "task_class": task_class,
        "difficulty": difficulty,
        "reward_value": reward_value,
        "reward_type": reward_type,
    }
    history.append(entry)
    save_history(history)
    return entry


def get_summary():
    """Generate a summary of task/reward history for prediction."""
    history = load_history()
    if not history:
        return {"count": 0, "message": "No tasks logged yet."}

    by_class = defaultdict(list)
    by_difficulty = defaultdict(list)
    by_class_difficulty = defaultdict(list)
    all_rewards = []

    for entry in history:
        val = entry.get("reward_value", 0)
        cls = entry.get("task_class", "unknown")
        diff = entry.get("difficulty", "medium")
        all_rewards.append(val)
        by_class[cls].append(val)
        by_difficulty[diff].append(val)
        by_class_difficulty[f"{cls}|{diff}"].append(val)

    def stats(values):
        if not values:
            return {"count": 0, "avg": 0, "min": 0, "max": 0}
        return {
            "count": len(values),
            "avg": round(sum(values) / len(values), 2),
            "min": min(values),
            "max": max(values),
        }

    return {
        "count": len(history),
        "can_predict": len(history) >= PREDICTION_THRESHOLD,
        "overall": stats(all_rewards),
        "by_class": {k: stats(v) for k, v in sorted(by_class.items())},
        "by_difficulty": {k: stats(v) for k, v in sorted(by_difficulty.items())},
        "by_class_and_difficulty": {k: stats(v) for k, v in sorted(by_class_difficulty.items())},
        "reward_type": history[-1].get("reward_type", "unknown") if history else "unknown",
    }


def can_predict():
    """Check if enough history exists for prediction."""
    history = load_history()
    return len(history) >= PREDICTION_THRESHOLD


def cmd_config(args):
    if args.get_config:
        config = load_config()
        if config is None:
            print(json.dumps({"configured": False, "message": "No config found. Run setup first."}, indent=2))
        else:
            config["configured"] = True
            print(json.dumps(config, indent=2))
    elif args.set_config:
        config = {
            "sheet_id": args.sheet_id,
            "sheet_range": args.sheet_range or "Sheet1!A:F",
            "reward_type": args.reward_type,
            "value_method": args.value_method,
        }
        if args.value_params:
            config["value_params"] = json.loads(args.value_params)
        save_config(config)
        print(json.dumps({"success": True, "config": config}, indent=2))
    else:
        print("Use --get or --set", file=sys.stderr)
        sys.exit(1)


def cmd_history(args):
    if args.add:
        entry = add_entry(
            task_name=args.task,
            description=args.description or "",
            task_class=args.task_class or "general",
            difficulty=args.difficulty or "medium",
            reward_value=float(args.reward),
            reward_type=args.reward_type or "money",
        )
        print(json.dumps({"success": True, "entry": entry, "total_tasks": len(load_history())}, indent=2))
    elif args.summary:
        print(json.dumps(get_summary(), indent=2))
    elif args.list:
        history = load_history()
        print(json.dumps(history, indent=2))
    elif args.can_predict:
        result = can_predict()
        count = len(load_history())
        print(json.dumps({
            "can_predict": result,
            "tasks_logged": count,
            "tasks_needed": max(0, PREDICTION_THRESHOLD - count),
        }, indent=2))
    else:
        print("Use --add, --summary, --list, or --can-predict", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Reward Tracker storage helper")
    sub = parser.add_subparsers(dest="command")

    # config subcommand
    cfg = sub.add_parser("config")
    cfg.add_argument("--get", dest="get_config", action="store_true")
    cfg.add_argument("--set", dest="set_config", action="store_true")
    cfg.add_argument("--sheet-id", default=None)
    cfg.add_argument("--sheet-range", default=None)
    cfg.add_argument("--reward-type", default="money")
    cfg.add_argument("--value-method", default="random_range")
    cfg.add_argument("--value-params", default=None)

    # history subcommand
    hist = sub.add_parser("history")
    hist.add_argument("--add", action="store_true")
    hist.add_argument("--summary", action="store_true")
    hist.add_argument("--list", action="store_true")
    hist.add_argument("--can-predict", action="store_true")
    hist.add_argument("--task", default=None)
    hist.add_argument("--description", default=None)
    hist.add_argument("--class", dest="task_class", default=None)
    hist.add_argument("--difficulty", default=None)
    hist.add_argument("--reward", default=None)
    hist.add_argument("--reward-type", default=None)

    args = parser.parse_args()
    if args.command == "config":
        cmd_config(args)
    elif args.command == "history":
        cmd_history(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
