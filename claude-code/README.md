# diamond — Claude Code statusline

A single-line PowerShell statusline for [Claude Code](https://claude.com/claude-code) on Windows. Renders model, effort, folder, git branch + dirty count, and context / 5h / 7d usage bars, separated by pipes.

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
| 5h | `rate_limits.five_hour` | bar + percent + reset clock (`HH:mm`) |
| 7d | `rate_limits.seven_day` | bar + percent + reset date (`MM-dd`) |

## Requirements

- PowerShell 7+ (`pwsh`) on PATH
- A Nerd Font in your terminal (for the folder/branch glyphs) — without one, those two characters will show as tofu
- `git` on PATH (only needed for the `±N` dirty count; branch detection itself just reads `.git/HEAD`)

## Install

1. Copy `statusline-diamond.ps1` somewhere stable. The reference path used below is `C:/Users/hjc/.claude/statusline-diamond.ps1` — change it to wherever you put the file.
2. Merge `settings.snippet.json` into your Claude Code settings file (`%USERPROFILE%\.claude\settings.json`):

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

UTF-8 is forced on both stdin and stdout because PowerShell otherwise uses the console codepage (e.g. CP932 on Japanese Windows), which corrupts multi-byte paths and breaks `ConvertFrom-Json`.

Git status uses `git --no-optional-locks` so it never contends with concurrent git operations in the same repo.

## Customizing

- **Colors**: edit the `$cyan` / `$gray` ANSI escape variables at the top.
- **Bar width**: change `$w = 8` inside `function Bar`.
- **Drop a segment**: comment out the corresponding `$parts += …` block.
- **Effort labels**: tweak the `switch` block under `# Effort level`.
