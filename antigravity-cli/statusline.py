import sys
import os
import json
import re
import time
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

def parse_reset_time(iso_str):
    if not iso_str:
        return ""
    try:
        if iso_str.endswith("Z"):
            iso_str = iso_str[:-1] + "+00:00"
        from datetime import datetime
        dt = datetime.fromisoformat(iso_str)
        local_dt = dt.astimezone()
        return local_dt.strftime("%H:%M")
    except Exception:
        return ""

def get_cached_quota():
    cache_path = r"C:\Users\hjc\.gemini\antigravity-cli\scratch\quota_cache.json"
    exists = os.path.exists(cache_path)
    age = time.time() - os.path.getmtime(cache_path) if exists else 999999
    
    if not exists or age > 30:
        try:
            fetcher_path = r"C:\Users\hjc\.gemini\antigravity-cli\scratch\quota_fetcher.py"
            subprocess.Popen([sys.executable, fetcher_path], creationflags=0x08000000, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
            
    if exists:
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("quota", {})
        except Exception:
            pass
    return {}

def match_model_quota(model_name, quota_data):
    buckets = quota_data.get("buckets", [])
    if not buckets:
        return None, ""
        
    name_lower = model_name.lower()
    is_pro = "pro" in name_lower
    is_flash = "flash" in name_lower or "lite" in name_lower
    
    best_bucket = None
    best_score = -1
    
    for bucket in buckets:
        model_id = bucket.get("modelId", "").lower()
        if not model_id:
            continue
            
        score = 0
        if "gemini" in name_lower and "gemini" in model_id:
            score += 1
        elif "claude" in name_lower and "claude" in model_id:
            score += 1
            
        if is_pro and "pro" in model_id:
            score += 2
        elif is_flash and ("flash" in model_id or "lite" in model_id):
            score += 2
            
        for word in name_lower.split():
            if any(c.isdigit() for c in word):
                clean_ver = "".join(c for c in word if c.isdigit() or c == ".")
                if clean_ver and clean_ver in model_id:
                    score += 5
                    
        if score < 5:
            if "3" in name_lower and "3" in model_id:
                score += 3
            elif "2" in name_lower and "2" in model_id:
                score += 3
                
        if score > best_score:
            best_score = score
            best_bucket = bucket
            
    if best_bucket:
        remaining_fraction = best_bucket.get("remainingFraction", 1.0)
        pct = int(round(remaining_fraction * 100))
        reset_time_str = best_bucket.get("resetTime", "")
        reset_time = parse_reset_time(reset_time_str) if pct < 100 else ""
        return pct, reset_time
        
    return None, ""

def estimate_quotas(model_name):
    gemini_pct = 100
    claude_pct = 100
    gemini_reset = ""
    claude_reset = ""
    
    quota_data = get_cached_quota()
    
    model_lower = model_name.lower()
    is_gemini = "gemini" in model_lower or "flash" in model_lower or "pro" in model_lower
    is_claude = "claude" in model_lower or "sonnet" in model_lower or "opus" in model_lower
    
    if not is_gemini and not is_claude:
        is_gemini = True
        
    if is_gemini:
        pct, reset = match_model_quota(model_name, quota_data)
        if pct is not None:
            gemini_pct = pct
            gemini_reset = reset
        claude_pct = 100
    elif is_claude:
        claude_pct = 100
        # For Claude, show Gemini's default flash/lite quota on the gemini bar
        pct, reset = match_model_quota("gemini-3.1-flash-lite", quota_data)
        if pct is not None:
            gemini_pct = pct
            gemini_reset = reset
            
    return gemini_pct, gemini_reset, claude_pct, claude_reset

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
        
        # 5. Model Quota progress bars
        gemini_pct, gemini_reset, claude_pct, claude_reset = estimate_quotas(display_name)
        
        gemini_bar = get_progress_bar(gemini_pct)
        claude_bar = get_progress_bar(claude_pct)
        
        gem_part = f"{COLOR_DIM}gem {gemini_bar} {COLOR_LIGHT}{gemini_pct}%"
        if gemini_reset:
            gem_part += f" {COLOR_DIM}{gemini_reset}"
        gem_part += COLOR_RESET
        
        cld_part = f"{COLOR_DIM}cld {claude_bar} {COLOR_LIGHT}{claude_pct}%"
        if claude_reset:
            cld_part += f" {COLOR_DIM}{claude_reset}"
        cld_part += COLOR_RESET
            
        # Combine status line parts
        sep = f" {COLOR_DIM}|{COLOR_RESET} "
        parts = [model_part, folder_part]
        if git_part:
            parts.append(git_part)
        parts.extend([ctx_part, gem_part, cld_part])
            
        status_line = sep.join(parts)
        
        # Write directly to standard output as UTF-8 bytes
        sys.stdout.buffer.write(status_line.encode("utf-8"))
        sys.stdout.buffer.flush()
        
    except Exception as e:
        # Fallback to standard simple line on error
        sys.stdout.write(f"statusline error: {str(e)}")

if __name__ == "__main__":
    main()
