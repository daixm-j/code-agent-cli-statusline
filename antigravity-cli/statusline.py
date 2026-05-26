import sys
import os
import json
import re
import subprocess

# ANSI 256 colors
COLOR_CYAN = "\033[38;5;80m"    # Premium soft cyan
COLOR_DIM = "\033[38;5;244m"    # Muted slate gray
COLOR_LIGHT = "\033[38;5;251m"  # Off-white / light gray
COLOR_GIT_ICON = "\033[38;5;209m"# Git brand orange
COLOR_RESET = "\033[0m"

def get_progress_bar(percentage, total_chars=8):
    pct = max(0, min(100, percentage))
    filled_chars = int(round((pct / 100.0) * total_chars))
    filled_str = "█" * filled_chars
    empty_str = "░" * (total_chars - filled_chars)
    return f"{COLOR_LIGHT}{filled_str}{COLOR_DIM}{empty_str}"

def get_git_info(cwd_path):
    if not cwd_path or not os.path.isdir(cwd_path):
        return None, 0
    try:
        # Get current branch
        branch = subprocess.check_output(
            ["git", "branch", "--show-current"], 
            cwd=cwd_path, 
            stderr=subprocess.DEVNULL
        ).decode("utf-8", errors="ignore").strip()
        
        if not branch:
            # Try symbolic-ref
            branch = subprocess.check_output(
                ["git", "symbolic-ref", "--short", "HEAD"], 
                cwd=cwd_path, 
                stderr=subprocess.DEVNULL
            ).decode("utf-8", errors="ignore").strip()
        
        if not branch:
            return None, 0
            
        # Get changes count
        status_output = subprocess.check_output(
            ["git", "status", "--porcelain"], 
            cwd=cwd_path, 
            stderr=subprocess.DEVNULL
        ).decode("utf-8", errors="ignore")
        
        changes = len([line for line in status_output.splitlines() if line.strip()])
        return branch, changes
    except Exception:
        return None, 0



def main():
    try:
        # Read raw stdin bytes and decode with replacement
        raw_data = sys.stdin.buffer.read()
        if not raw_data:
            return
        
        # Write to latest_stdin.json to inspect fields
        try:
            with open(r"C:\Users\hjc\.gemini\antigravity-cli\scratch\latest_stdin.json", "wb") as f:
                f.write(raw_data)
        except Exception:
            pass
        
        data = json.loads(raw_data.decode("utf-8", errors="replace"))
        
        # 1. Model + Think Level
        model_info = data.get("model", {})
        display_name = model_info.get("display_name", "") or model_info.get("id", "Unknown")
        
        # Strip "Gemini " prefix if present
        if display_name.startswith("Gemini "):
            display_name = display_name[7:]
            
        think_level = ""
        match = re.search(r"\(([^)]+)\)", display_name)
        if match:
            think_level = match.group(1).lower()
            display_name = re.sub(r"\s*\([^)]+\)", "", display_name).strip()
            
        is_gemini_model = "gemini" in display_name.lower() or "flash" in display_name.lower() or "pro" in display_name.lower() or any(x in display_name.lower() for x in ["3.5", "3.1", "3.0", "2.5"])
        
        # Map think levels for clean display
        if think_level == "high":
            if is_gemini_model:
                think_level = "high"
            else:
                think_level = "xhigh"
        elif think_level == "medium":
            think_level = "med"
            
        model_part = f"{COLOR_CYAN}{display_name}"
        if think_level:
            model_part += f" {COLOR_DIM}{think_level}"
        model_part += COLOR_RESET
        
        # 2. Folder name
        cwd = data.get("cwd", "") or data.get("workspace", {}).get("current_dir", "")
        folder_name = os.path.basename(cwd) if cwd else "unknown"
        folder_part = f"{COLOR_LIGHT}📁 {folder_name}{COLOR_RESET}"
        
        # 3. Git repository info
        git_branch, git_changes = get_git_info(cwd)
        if git_branch:
            git_part = f"{COLOR_GIT_ICON} {COLOR_CYAN}{git_branch}"
            if git_changes > 0:
                git_part += f" {COLOR_DIM}±{git_changes}"
            git_part += COLOR_RESET
        else:
            git_part = ""
        
        # 4. Context usage progress bar
        context_window = data.get("context_window", {}) or {}
        used_percentage = context_window.get("used_percentage", 0.0)
        ctx_pct = int(round(used_percentage))
        ctx_bar = get_progress_bar(ctx_pct)
        ctx_part = f"{COLOR_DIM}ctx {ctx_bar} {COLOR_LIGHT}{ctx_pct}%{COLOR_RESET}"
        
        # Combine status line parts
        sep = f" {COLOR_DIM}|{COLOR_RESET} "
        parts = [model_part, folder_part]
        if git_part:
            parts.append(git_part)
        parts.append(ctx_part)
            
        status_line = sep.join(parts)
        
        # Write directly to standard output as UTF-8 bytes
        sys.stdout.buffer.write(status_line.encode("utf-8"))
        sys.stdout.buffer.flush()
        
    except Exception as e:
        # Fallback to standard simple line on error
        sys.stdout.write(f"statusline error: {str(e)}")

if __name__ == "__main__":
    main()
