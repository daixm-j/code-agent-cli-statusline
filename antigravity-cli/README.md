# Antigravity CLI Statusline

A premium statusline for the Antigravity CLI on Windows, displaying the active model, current folder, Git branch status, context window usage, and API quotas (Gemini & Claude).

## Preview

```text
Flash Lite | 📁 code-agent-cli-statusline |  master ±2 | ctx ████░░░░ 50% | gem ██████░░ 75% | cld ████████ 100%
```

Segments (in order):

| Segment | Source | Notes |
| --- | --- | --- |
| **Model** | `model` | Displays the active model (sans prefix) and think level (e.g., `high`, `med`). |
| **Folder** | `cwd` / `current_dir` | The folder basename, prepended by a `📁` emoji. |
| **Git** | git commands | Branch name prepended by the git branch icon (``) and modified/added file count (`±N`). |
| **ctx** | `context_window` | 8-cell progress bar of the context window usage percentage. |
| **gem** | `quota` cache | 8-cell progress bar of the Gemini API quota, including reset time if `< 100%`. |
| **cld** | `quota` cache | 8-cell progress bar of the Claude API quota. |

---

## Components

1. **`statusline.py`**: The core statusline script. It parses the stdin JSON data sent by the Antigravity CLI and formats the statusline output. It asynchronously triggers `quota_fetcher.py` if the cache is older than 30 seconds.
2. **`quota_fetcher.py`**: A background script that fetches API quotas from the Google Cloud AI Companion / Gemini endpoint using Google Cloud Credentials and saves it to a cache file.
3. **`settings.snippet.json`**: A snippet of the configuration to merge into your Antigravity CLI `settings.json`.

---

## Installation

1. Copy `statusline.py` and `quota_fetcher.py` into your Antigravity CLI scratch directory:
   - Target Directory: `C:\Users\hjc\.gemini\antigravity-cli\scratch\`
2. Add/merge the statusline configuration snippet into your Antigravity CLI settings file (`C:\Users\hjc\.gemini\antigravity-cli\settings.json`):
   ```json
   {
     "statusLine": {
       "type": "command",
       "command": "python C:/Users/hjc/.gemini/antigravity-cli/scratch/statusline.py",
       "enabled": true
     }
   }
   ```
3. Restart the Antigravity CLI or start a new session.

---

## Customization

- **Colors**: Edit the ANSI color definitions (e.g., `COLOR_CYAN`, `COLOR_DIM`, etc.) at the top of `statusline.py`.
- **Bar characters**: By default, the progress bars use unicode `█` (`\u2588`) for filled blocks and `░` (`\u2591`) for empty blocks.
- **Refresh Frequency**: The script runs `quota_fetcher.py` in the background if the cache file is older than 30 seconds. This can be customized in the `get_cached_quota` function in `statusline.py`.
