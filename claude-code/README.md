# diamond — Claude Code statusline

A single-line statusline for [Claude Code](https://claude.com/claude-code). Renders model, effort, folder, git branch + dirty count, and context / 5h / 7d usage bars, separated by pipes.

Two equivalent implementations are provided:

- `statusline-diamond.py` — cross-platform (Linux, macOS, Windows). Requires Python 3.
- `statusline-diamond.ps1` — Windows-flavored. Requires PowerShell 7+ (`pwsh`).

## Preview

```
Claude Opus 4.7 xhigh |  code-agent-cli-statusline |  master ±2 | ctx ██░░░░░░ 22% | 5h ███░░░░░ 37% 14:00 | 7d █░░░░░░░ 12% 05-30
```

Segments (in order):

| Segment | Source | Notes |
| --- | --- | --- |
| Model | `model.display_name` | Cyan; falls back to `Claude` |
| Effort | `effort.level` | `low → fast`, `medium → med`, otherwise raw label |
| Folder | `workspace.current_dir` basename |  nf-fa-folder icon |
| Git | walks up to find `.git/HEAD` |  nf-pl-branch icon, `±N` from `git status --porcelain` |
| ctx | `context_window.used_percentage` | 8-cell bar + percent |
| 5h | `rate_limits.five_hour` | bar + percent + reset clock (`HH:mm`, local time) |
| 7d | `rate_limits.seven_day` | bar + percent + reset date (`MM-dd`, local time) |

## Requirements

- Python 3.7+ (for the `.py` version) **or** PowerShell 7+ (for the `.ps1` version)
- A Nerd Font in your terminal (for the folder/branch glyphs) — without one, those two characters will show as tofu
- `git` on PATH (only needed for the `±N` dirty count; branch detection itself just reads `.git/HEAD`)

## Install

1. Copy the script you want to use somewhere stable. The reference path below is `~/.claude/statusline-diamond.py` (Linux/macOS) or `C:/Users/<you>/.claude/statusline-diamond.ps1` (Windows) — change to wherever you put the file.
2. Merge `settings.snippet.json` into your Claude Code settings file (`~/.claude/settings.json`, or `%USERPROFILE%\.claude\settings.json` on Windows).

   **Python (cross-platform):**

   ```json
   {
     "statusLine": {
       "type": "command",
       "command": "python3 ~/.claude/statusline-diamond.py"
     }
   }
   ```

   On Windows replace `python3` with `python` (or the full path to your interpreter) and use a Windows path. On Linux/macOS you can also add a shebang and `chmod +x` and invoke the script directly.

   **PowerShell (Windows):**

   ```json
   {
     "statusLine": {
       "type": "command",
       "command": "pwsh -NoProfile -NonInteractive -File C:/Users/hjc/.claude/statusline-diamond.ps1"
     }
   }
   ```

3. Restart Claude Code (or start a new session). The statusline updates each turn.

## How it works

Claude Code spawns the `command` once per refresh and pipes a JSON status payload to its stdin. The script reads that JSON, picks out the fields it cares about, and writes a single styled line to stdout. No external state, no background process.

stdin and stdout are both read/written as raw UTF-8 bytes. The PowerShell version forces this explicitly because PowerShell otherwise uses the console codepage (e.g. CP932 on Japanese Windows), which corrupts multi-byte paths and breaks `ConvertFrom-Json`. The Python version uses `sys.stdin.buffer` / `sys.stdout.buffer` for the same reason.

Git status uses `git --no-optional-locks` so it never contends with concurrent git operations in the same repo.

## Customizing

- **Colors**: edit the `CYAN` / `GRAY` ANSI escape constants near the top of either script.
- **Bar width**: change `w = 8` inside `bar()` (Python) or `$w = 8` inside `function Bar` (PowerShell).
- **Drop a segment**: comment out the corresponding `parts.append(...)` / `$parts += …` block.
- **Effort labels**: tweak the mapping under `# Effort label` / `# Effort level`.
