# Claude Code statusLine — simple single-line text
# Reads JSON on stdin, prints one line with pipe-separated segments.

[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding           = [System.Text.UTF8Encoding]::new()

# Read stdin as UTF-8 explicitly. $input uses the console codepage (CP932 on
# Japanese Windows) regardless of [Console]::InputEncoding, which mangles
# multi-byte UTF-8 sequences in paths like "入退室管理ツール" and breaks JSON parsing.
$reader = [System.IO.StreamReader]::new([System.Console]::OpenStandardInput(), [System.Text.UTF8Encoding]::new($false))
$json   = $reader.ReadToEnd()
$data   = $json | ConvertFrom-Json


# Subtle ANSI colors (dim/cyan accents on default background)
$esc   = [char]27
$reset = "$esc[0m"
$dim   = "$esc[2m"
$cyan  = "$esc[36m"
$gray  = "$esc[90m"

# Nerd Font icons (Private Use Area)
$icon_folder = [char]0xF07B  # nf-fa-folder
$icon_branch = [char]0xE0A0  # nf-pl-branch

function Bar($pct) {
    $w = 8
    $filled = [int][Math]::Round($pct / 100.0 * $w)
    $filled = [Math]::Max(0, [Math]::Min($w, $filled))
    return ("█" * $filled) + ("░" * ($w - $filled))
}

# Parent console width via Win32. PowerShell sees a fake 120-col buffer when
# spawned with piped stdout, so we attach to the parent process's real console
# (Claude Code → terminal) and read GetConsoleScreenBufferInfo.
# Model
$model = $data.model.display_name
if (-not $model) { $model = "Claude" }

# Folder (basename)
$cwd = $data.workspace.current_dir
if (-not $cwd) { $cwd = $data.cwd }
if (-not $cwd) { $cwd = (Get-Location).Path }
$folder = Split-Path $cwd -Leaf
if (-not $folder) { $folder = $cwd }

# Effort level
$effort_label = $null
if ($data.effort -and $data.effort.level) {
    $effort_label = switch ($data.effort.level) {
        "low"    { "fast" }
        "medium" { "med"  }
        "high"   { "high" }
        "xhigh"  { "xhigh" }
        "max"    { "max"  }
        default  { $data.effort.level }
    }
}

# Git: walk up looking for .git/HEAD (lock-free)
$git_branch = $null
$git_root   = $null
$dir = if ($data.workspace.current_dir) { $data.workspace.current_dir } else { (Get-Location).Path }
while ($dir -and $dir -ne [System.IO.Path]::GetPathRoot($dir)) {
    $head = Join-Path $dir ".git\HEAD"
    if (Test-Path $head) {
        $git_root = $dir
        $h = (Get-Content $head -Raw -ErrorAction SilentlyContinue).Trim()
        if ($h -match '^ref: refs/heads/(.+)$') { $git_branch = $matches[1] }
        elseif ($h) { $git_branch = $h.Substring(0, [Math]::Min(7, $h.Length)) }
        break
    }
    $dir = Split-Path $dir -Parent
}

# Build segments in order: model | folder | git | ctx | 5h | 7d
$parts = @()

$model_seg = "${cyan}${model}${reset}"
if ($effort_label) { $model_seg += " ${gray}${effort_label}${reset}" }
$parts += $model_seg
$parts += "${icon_folder} ${folder}"

if ($git_branch) {
    $changes = $null
    try {
        $st = & git -C $git_root --no-optional-locks status --porcelain 2>$null
        $changes = if ($st) { @($st).Count } else { 0 }
    } catch {}
    $branch_seg = "${cyan}${icon_branch} ${git_branch}${reset}"
    if ($null -ne $changes -and $changes -gt 0) {
        $branch_seg += " ${gray}±${changes}${reset}"
    }
    $parts += $branch_seg
}

$ctx = $data.context_window.used_percentage
if ($null -ne $ctx) {
    $p = [int][Math]::Round($ctx)
    $parts += "${gray}ctx${reset} $(Bar $p) ${p}%"
}

function FromUnix($s, $fmt) {
    if ($null -eq $s) { return $null }
    return [DateTimeOffset]::FromUnixTimeSeconds([long]$s).LocalDateTime.ToString($fmt)
}

$five = $data.rate_limits.five_hour.used_percentage
if ($null -ne $five) {
    $p = [int][Math]::Round($five)
    $seg = "${gray}5h${reset} $(Bar $p) ${p}%"
    $r = FromUnix $data.rate_limits.five_hour.resets_at "HH:mm"
    if ($r) { $seg += " ${gray}${r}${reset}" }
    $parts += $seg
}

$seven = $data.rate_limits.seven_day.used_percentage
if ($null -ne $seven) {
    $p = [int][Math]::Round($seven)
    $seg = "${gray}7d${reset} $(Bar $p) ${p}%"
    $r = FromUnix $data.rate_limits.seven_day.resets_at "MM-dd"
    if ($r) { $seg += " ${gray}${r}${reset}" }
    $parts += $seg
}

# Join with default-color pipe separators
$sep = " ${reset}|${reset} "
[Console]::Write(($parts -join $sep))
