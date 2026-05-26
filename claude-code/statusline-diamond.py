#!/usr/bin/env python3
# Claude Code statusLine - simple single-line text
# Reads JSON on stdin, prints one line with pipe-separated segments.
# Cross-platform port of statusline-diamond.ps1.

import json
import os
import subprocess
import sys
from datetime import datetime, timezone

ESC = "\x1b"
RESET = f"{ESC}[0m"
DIM = f"{ESC}[2m"
CYAN = f"{ESC}[36m"
GRAY = f"{ESC}[90m"

ICON_FOLDER = ""  # nf-fa-folder
ICON_BRANCH = ""  # nf-pl-branch


def bar(pct):
    w = 8
    pct = max(0, min(100, pct))
    filled = int(round(pct / 100.0 * w))
    filled = max(0, min(w, filled))
    return ("█" * filled) + ("░" * (w - filled))


def find_git(start_dir):
    """Walk up from start_dir to find .git/HEAD. Returns (root, branch_or_short_sha) or (None, None)."""
    if not start_dir:
        return None, None
    d = os.path.abspath(start_dir)
    while True:
        head = os.path.join(d, ".git", "HEAD")
        if os.path.isfile(head):
            try:
                with open(head, "r", encoding="utf-8", errors="replace") as f:
                    h = f.read().strip()
            except OSError:
                return d, None
            if h.startswith("ref: refs/heads/"):
                return d, h[len("ref: refs/heads/"):]
            if h:
                return d, h[:7]
            return d, None
        parent = os.path.dirname(d)
        if parent == d:
            return None, None
        d = parent


def git_changes(root):
    """Count porcelain status lines. Returns None if git fails."""
    try:
        out = subprocess.run(
            ["git", "-C", root, "--no-optional-locks", "status", "--porcelain"],
            capture_output=True,
            timeout=2,
        )
        if out.returncode != 0:
            return None
        text = out.stdout.decode("utf-8", errors="replace")
        return sum(1 for line in text.splitlines() if line.strip())
    except (OSError, subprocess.TimeoutExpired):
        return None


def from_unix(ts, fmt):
    if ts is None:
        return None
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).astimezone().strftime(fmt)
    except (ValueError, OSError, OverflowError):
        return None


def main():
    raw = sys.stdin.buffer.read()
    if not raw:
        return
    try:
        data = json.loads(raw.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        return

    workspace = data.get("workspace") or {}
    cwd = workspace.get("current_dir") or data.get("cwd") or os.getcwd()

    # Model
    model_info = data.get("model") or {}
    model = model_info.get("display_name") or "Claude"

    # Folder (basename)
    folder = os.path.basename(cwd.rstrip("\\/")) or cwd

    # Effort label
    effort_label = None
    effort = data.get("effort") or {}
    level = effort.get("level")
    if level:
        effort_label = {
            "low": "fast",
            "medium": "med",
            "high": "high",
            "xhigh": "xhigh",
            "max": "max",
        }.get(level, level)

    # Git
    git_root, git_branch = find_git(cwd)

    parts = []

    model_seg = f"{CYAN}{model}{RESET}"
    if effort_label:
        model_seg += f" {GRAY}{effort_label}{RESET}"
    parts.append(model_seg)
    parts.append(f"{ICON_FOLDER} {folder}")

    if git_branch:
        changes = git_changes(git_root)
        branch_seg = f"{CYAN}{ICON_BRANCH} {git_branch}{RESET}"
        if changes is not None and changes > 0:
            branch_seg += f" {GRAY}±{changes}{RESET}"
        parts.append(branch_seg)

    ctx_window = data.get("context_window") or {}
    ctx = ctx_window.get("used_percentage")
    if ctx is not None:
        p = int(round(ctx))
        parts.append(f"{GRAY}ctx{RESET} {bar(p)} {p}%")

    rate_limits = data.get("rate_limits") or {}

    five = (rate_limits.get("five_hour") or {})
    five_pct = five.get("used_percentage")
    if five_pct is not None:
        p = int(round(five_pct))
        seg = f"{GRAY}5h{RESET} {bar(p)} {p}%"
        r = from_unix(five.get("resets_at"), "%H:%M")
        if r:
            seg += f" {GRAY}{r}{RESET}"
        parts.append(seg)

    seven = (rate_limits.get("seven_day") or {})
    seven_pct = seven.get("used_percentage")
    if seven_pct is not None:
        p = int(round(seven_pct))
        seg = f"{GRAY}7d{RESET} {bar(p)} {p}%"
        r = from_unix(seven.get("resets_at"), "%m-%d")
        if r:
            seg += f" {GRAY}{r}{RESET}"
        parts.append(seg)

    sep = f" {RESET}|{RESET} "
    sys.stdout.buffer.write(sep.join(parts).encode("utf-8"))
    sys.stdout.buffer.flush()


if __name__ == "__main__":
    main()
