#!/usr/bin/env python3
"""
Auto-Commit Module — Automatically commits and pushes Apollo self-modifications.

When Apollo modifies its own source code during a conversation, this module
tracks the changed files and commits+pushes them at the end of the conversation.
This ensures every self-improvement is versioned and recoverable.

Usage (called automatically by the agent loop):
    from tools.auto_commit import track_self_modification, commit_self_modifications

    # Called by file tools after each write/patch to apollo-agent repo files
    track_self_modification("/home/user/apollo-agent/tools/some_tool.py")

    # Called at end of conversation to commit+push all tracked changes
    commit_self_modifications()
"""

import logging
import os
import subprocess
import threading
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Resolve the apollo-agent repo root (directory containing this file's parent)
APOLLO_REPO_ROOT = str(Path(__file__).resolve().parent.parent)

# Thread-safe set of modified file paths within the apollo-agent repo
_modified_files_lock = threading.Lock()
_modified_files: set = set()


def _is_in_apollo_repo(path: str) -> bool:
    """Check if a file path is inside the apollo-agent repository."""
    try:
        resolved = str(Path(path).resolve())
        return resolved.startswith(APOLLO_REPO_ROOT + os.sep) or resolved == APOLLO_REPO_ROOT
    except (OSError, ValueError):
        return False


def track_self_modification(path: str) -> None:
    """Record that a file in the apollo-agent repo was modified.

    Called by write_file_tool and patch_tool after successful file operations.
    Only tracks files that are inside the apollo-agent repository.
    """
    if not path:
        return
    try:
        resolved = str(Path(path).resolve())
    except (OSError, ValueError):
        return

    if not _is_in_apollo_repo(resolved):
        return

    with _modified_files_lock:
        _modified_files.add(resolved)
    logger.debug("Tracked self-modification: %s", resolved)


def has_pending_modifications() -> bool:
    """Check if there are any tracked self-modifications waiting to be committed."""
    with _modified_files_lock:
        return len(_modified_files) > 0


def get_pending_modifications() -> list:
    """Return a copy of the currently tracked modified files."""
    with _modified_files_lock:
        return sorted(_modified_files)


def commit_self_modifications() -> dict:
    """Commit and push all tracked self-modifications.

    Called at the end of a conversation. Stages all tracked files,
    creates a commit with a descriptive message, and pushes to origin.

    Returns:
        dict with keys:
            - success (bool): Whether the commit+push succeeded
            - committed_files (list): Files that were committed
            - commit_hash (str): The short commit hash, if successful
            - error (str): Error message, if failed
    """
    with _modified_files_lock:
        files = sorted(_modified_files)
        _modified_files.clear()

    if not files:
        return {"success": True, "committed_files": [], "commit_hash": None, "error": None}

    # Make paths relative to repo root for cleaner commit messages
    rel_files = []
    for f in files:
        try:
            rel = os.path.relpath(f, APOLLO_REPO_ROOT)
            rel_files.append(rel)
        except ValueError:
            rel_files.append(f)

    result = {
        "success": False,
        "committed_files": rel_files,
        "commit_hash": None,
        "error": None,
    }

    try:
        # Check if we're actually in a git repo
        git_check = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=APOLLO_REPO_ROOT, capture_output=True, text=True, timeout=10,
        )
        if git_check.returncode != 0:
            result["error"] = "Not inside a git repository"
            return result

        # Stage the modified files
        stage_cmd = ["git", "add"] + files
        stage = subprocess.run(
            stage_cmd, cwd=APOLLO_REPO_ROOT,
            capture_output=True, text=True, timeout=30,
        )
        if stage.returncode != 0:
            result["error"] = f"git add failed: {stage.stderr.strip()}"
            return result

        # Check if there are actually staged changes (files might not have changed)
        diff_check = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=APOLLO_REPO_ROOT, capture_output=True, text=True, timeout=10,
        )
        if diff_check.returncode == 0:
            # No actual changes staged
            result["success"] = True
            result["committed_files"] = []
            result["error"] = None
            return result

        # Build commit message
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file_summary = ", ".join(rel_files[:5])
        if len(rel_files) > 5:
            file_summary += f" (+{len(rel_files) - 5} more)"

        commit_msg = (
            f"auto: Apollo self-update ({timestamp})\n\n"
            f"Apollo modified {len(rel_files)} file(s) during conversation:\n"
            + "\n".join(f"  - {f}" for f in rel_files)
        )

        # Commit
        commit = subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=APOLLO_REPO_ROOT, capture_output=True, text=True, timeout=30,
        )
        if commit.returncode != 0:
            result["error"] = f"git commit failed: {commit.stderr.strip()}"
            return result

        # Get commit hash
        hash_cmd = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=APOLLO_REPO_ROOT, capture_output=True, text=True, timeout=10,
        )
        if hash_cmd.returncode == 0:
            result["commit_hash"] = hash_cmd.stdout.strip()

        # Get current branch
        branch_cmd = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=APOLLO_REPO_ROOT, capture_output=True, text=True, timeout=10,
        )
        branch = branch_cmd.stdout.strip() if branch_cmd.returncode == 0 else "main"

        # Push with retry (exponential backoff for network errors)
        push_success = False
        for attempt in range(4):
            push = subprocess.run(
                ["git", "push", "-u", "origin", branch],
                cwd=APOLLO_REPO_ROOT, capture_output=True, text=True, timeout=60,
            )
            if push.returncode == 0:
                push_success = True
                break
            # Only retry on network-like errors
            err = push.stderr.strip().lower()
            if any(kw in err for kw in ["network", "timeout", "connection", "resolve", "ssl"]):
                import time
                wait = 2 ** (attempt + 1)  # 2, 4, 8, 16 seconds
                logger.warning("Push failed (attempt %d), retrying in %ds: %s", attempt + 1, wait, push.stderr.strip())
                time.sleep(wait)
            else:
                # Non-network error, don't retry
                break

        if not push_success:
            # Commit succeeded but push failed — not a total failure
            result["success"] = True
            result["error"] = f"Committed locally but push failed: {push.stderr.strip()}"
            logger.warning("Auto-commit push failed: %s", push.stderr.strip())
        else:
            result["success"] = True
            logger.info(
                "Auto-committed and pushed %d self-modified file(s): %s [%s]",
                len(rel_files), file_summary, result["commit_hash"],
            )

    except subprocess.TimeoutExpired:
        result["error"] = "Git operation timed out"
        logger.error("Auto-commit timed out")
    except FileNotFoundError:
        result["error"] = "git not found on PATH"
        logger.error("git executable not found")
    except Exception as e:
        result["error"] = f"Unexpected error: {e}"
        logger.error("Auto-commit failed: %s", e, exc_info=True)

    return result
