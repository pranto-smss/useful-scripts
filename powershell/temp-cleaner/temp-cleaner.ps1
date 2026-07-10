<#
.SYNOPSIS
    Interactive temp file cleaner. Preview before deleting -- nothing touched until you confirm.

.DESCRIPTION
    Cleans Windows temp folders, caches, and crash dumps with an age-based filter.
    Shows a full preview of what would be deleted and how much space would be freed.
    Skips locked/in-use files automatically. No admin needed for user-only cleanup.

.EXAMPLE
    ./temp-cleaner.ps1
    Then just answer the questions on screen.
#>

$ErrorActionPreference = "Continue"

# ===========================================================================
# HELPERS
# ===========================================================================

function Write-Title($text) {
    Write-Host ""
    Write-Host "=== $text ===" -ForegroundColor Cyan
}

function Write-Step($text) {
    Write-Host ""
    Write-Host $text -ForegroundColor Yellow
}

function Read-Prompt($message, $default = $null) {
    if ($default) {
        $input = Read-Host "$message [$default]"
        if ([string]::IsNullOrWhiteSpace($input)) { return $default }
        return $input
    } else {
        return Read-Host $message
    }
}

function Read-YesNo($message, $defaultYes = $true) {
    $suffix = if ($defaultYes) { "[Y/n]" } else { "[y/N]" }
    $input = Read-Host "$message $suffix"
    if ([string]::IsNullOrWhiteSpace($input)) { return $defaultYes }
    return $input.Trim().ToLower() -in @("y", "yes")
}

function Format-FileSize($bytes) {
    if ($null -eq $bytes -or $bytes -eq 0) { return "0 B" }
    if ($bytes -ge 1GB) { return "{0:N2} GB" -f ($bytes / 1GB) }
    if ($bytes -ge 1MB) { return "{0:N2} MB" -f ($bytes / 1MB) }
    if ($bytes -ge 1KB) { return "{0:N2} KB" -f ($bytes / 1KB) }
    return "$bytes B"
}

function Get-FolderSize($path) {
    if (-not (Test-Path $path)) { return 0 }
    $files = Get-ChildItem -Path $path -File -Recurse -Force -ErrorAction SilentlyContinue
    return ($files | Measure-Object -Property Length -Sum).Sum
}

function Get-TargetFiles($path, $daysOld) {
    if (-not (Test-Path $path)) { return @() }
    $cutoff = (Get-Date).AddDays(-$daysOld)
    $files = @()
    try {
        $files = @(Get-ChildItem -Path $path -File -Recurse -Force -ErrorAction Stop |
            Where-Object { $_.LastWriteTime -lt $cutoff })
    } catch {
        $folders = @($path)
        try {
            $folders += @(Get-ChildItem -Path $path -Directory -Force -ErrorAction Stop |
                Select-Object -ExpandProperty FullName)
        } catch {}
        foreach ($folder in $folders) {
            try {
                $files += @(Get-ChildItem -Path $folder -File -Force -ErrorAction Stop |
                    Where-Object { $_.LastWriteTime -lt $cutoff })
            } catch {}
        }
    }
    return $files
}

function Get-AllFiles($path) {
    if (-not (Test-Path $path)) { return @() }
    $files = @()
    try {
        $files = @(Get-ChildItem -Path $path -File -Recurse -Force -ErrorAction Stop)
    } catch {
        $folders = @($path)
        try {
            $folders += @(Get-ChildItem -Path $path -Directory -Force -ErrorAction Stop |
                Select-Object -ExpandProperty FullName)
        } catch {}
        foreach ($folder in $folders) {
            try { $files += @(Get-ChildItem -Path $folder -File -Force -ErrorAction Stop) } catch {}
        }
    }
    return $files
}

function Get-CleanupTargets($mode) {
    $targets = @()

    # User temp -- always included
    $targets += [PSCustomObject]@{
        Name = "User Temp"
        Path = $env:TEMP
        RequiresAdmin = $false
    }

    if ($mode -ge 2) {
        # System temp
        $targets += [PSCustomObject]@{
            Name = "System Temp"
            Path = "$env:WINDIR\Temp"
            RequiresAdmin = $true
        }
        # Windows Update cache
        $targets += [PSCustomObject]@{
            Name = "Windows Update Cache"
            Path = "$env:WINDIR\SoftwareDistribution\Download"
            RequiresAdmin = $true
        }
    }

    if ($mode -ge 3) {
        # Thumbnail cache
        $targets += [PSCustomObject]@{
            Name = "Thumbnail Cache"
            Path = "$env:LOCALAPPDATA\Microsoft\Windows\Explorer"
            RequiresAdmin = $false
            Filter = "thumbcache*.db"
        }
        # Crash dumps
        $targets += [PSCustomObject]@{
            Name = "Crash Dumps"
            Path = "$env:LOCALAPPDATA\CrashDumps"
            RequiresAdmin = $false
        }
        # Windows Error Reporting
        $targets += [PSCustomObject]@{
            Name = "Windows Error Reporting"
            Path = "$env:LOCALAPPDATA\Microsoft\Windows\WER"
            RequiresAdmin = $false
        }
    }

    return $targets
}

# ===========================================================================
# INTRO
# ===========================================================================

Write-Title "Temp File Cleaner"
Write-Host "Clean Windows temp files, caches, and crash dumps."
Write-Host "Nothing is deleted until you confirm a preview."

# ===========================================================================
# STEP 1: CLEANUP MODE
# ===========================================================================

Write-Step "Step 1: Choose cleanup level"
Write-Host "1. User temp only (safe, no admin needed)"
Write-Host "2. User + System temp (includes Windows Update cache)"
Write-Host "3. Full cleanup (temp + thumbnails + dumps + WER)"
$mode = [int](Read-Prompt "Choose an option" "1")

if ($mode -notin 1, 2, 3) { $mode = 1 }

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if ($mode -ge 2 -and -not $isAdmin) {
    Write-Host ""
    Write-Host "System cleanup requires Administrator. Falling back to User temp only." -ForegroundColor Yellow
    $mode = 1
}

# ===========================================================================
# STEP 2: AGE FILTER
# ===========================================================================

Write-Step "Step 2: Age filter"
Write-Host "Only files older than N days will be deleted."
Write-Host "Recent files (created/modified within N days) are kept."
$daysOld = [int](Read-Prompt "Delete files older than how many days?" "7")

if ($daysOld -lt 1) { $daysOld = 1 }

# ===========================================================================
# SCAN TARGETS
# ===========================================================================

$targets = Get-CleanupTargets -mode $mode
$scanResults = @()

Write-Step "Scanning..."

foreach ($target in $targets) {
    if (-not (Test-Path $target.Path)) {
        Write-Host "  SKIP (not found): $($target.Name) -- $($target.Path)" -ForegroundColor DarkGray
        continue
    }

    # Show total file count so user knows the folder is not empty
    $allFiles = @(Get-AllFiles -path $target.Path)
    $allCount = $allFiles.Count
    $allSize = ($allFiles | Measure-Object -Property Length -Sum).Sum
    Write-Host "  $($target.Name): $allCount file(s) total -- $(Format-FileSize $allSize)" -ForegroundColor DarkGray

    $files = Get-TargetFiles -path $target.Path -daysOld $daysOld
    if ($target.Filter) {
        $files = @($files | Where-Object { $_.Name -like $target.Filter })
    }

    $totalSize = ($files | Measure-Object -Property Length -Sum).Sum
    $count = $files.Count

    $scanResults += [PSCustomObject]@{
        Name = $target.Name
        Path = $target.Path
        Files = $files
        Count = $count
        Size = $totalSize
    }

    $sizeStr = Format-FileSize $totalSize
    if ($count -gt 0) {
        Write-Host "    -> $count file(s) older than $daysOld day(s) -- $sizeStr" -ForegroundColor Green
    } else {
        Write-Host "    -> all files are newer than $daysOld day(s)" -ForegroundColor DarkGray
    }
}

# ===========================================================================
# PREVIEW
# ===========================================================================

Write-Title "Preview"

$totalFiles = ($scanResults | Measure-Object -Property Count -Sum).Sum
$totalSize = ($scanResults | Measure-Object -Property Size -Sum).Sum

if ($totalFiles -eq 0) {
    Write-Host "Nothing to clean. All temp folders are already tidy." -ForegroundColor Green
    Read-Host "Press Enter to exit"
    exit
}

# Show top files by size
$allFiles = $scanResults | ForEach-Object { $_.Files } | Sort-Object Length -Descending | Select-Object -First 15

Write-Host "Largest files that would be deleted:" -ForegroundColor Cyan
foreach ($file in $allFiles) {
    $size = Format-FileSize $file.Length
    $age = ((Get-Date) - $file.LastWriteTime).Days
    Write-Host "  $size" -NoNewline
    Write-Host "  $age days old  " -ForegroundColor DarkGray -NoNewline
    Write-Host $file.FullName -ForegroundColor DarkGray
}

if ($totalFiles -gt 15) {
    Write-Host "  ... and $($totalFiles - 15) more file(s)" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "  Total files:  $totalFiles" -ForegroundColor Cyan
Write-Host "  Total size:   $(Format-FileSize $totalSize)" -ForegroundColor Cyan
Write-Host "  Age filter:   older than $daysOld day(s)" -ForegroundColor Cyan

# ===========================================================================
# CONFIRM AND APPLY
# ===========================================================================

Write-Host ""
$confirm = Read-YesNo "Delete these files now?" $false

if (-not $confirm) {
    Write-Host ""
    Write-Host "No files deleted. Run the script again anytime." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit
}

Write-Title "Cleaning"

$deleted = 0
$skipped = 0
$freed = 0

foreach ($result in $scanResults) {
    if ($result.Count -eq 0) { continue }

    Write-Host ""
    Write-Host "  $($result.Name)..." -ForegroundColor Yellow

    foreach ($file in $result.Files) {
        try {
            $size = $file.Length
            Remove-Item -LiteralPath $file.FullName -Force -ErrorAction Stop
            $deleted++
            $freed += $size
            Write-Host "    Deleted: $($file.Name)" -ForegroundColor Green
        } catch {
            $skipped++
            Write-Host "    Skipped (in use): $($file.Name)" -ForegroundColor DarkYellow
        }
    }

    # Remove empty directories left behind (top-level only)
    try {
        $dirs = Get-ChildItem -Path $result.Path -Directory -Force -ErrorAction Stop |
            Where-Object { (Get-ChildItem $_.FullName -Force -ErrorAction SilentlyContinue).Count -eq 0 }
        foreach ($dir in $dirs) {
            try { Remove-Item -LiteralPath $dir.FullName -Force -ErrorAction Stop } catch {}
        }
    } catch {}
}

# ===========================================================================
# SUMMARY
# ===========================================================================

Write-Title "Done"
Write-Host "  Files deleted:  $deleted" -ForegroundColor Green
if ($skipped -gt 0) {
    Write-Host "  Files skipped:  $skipped (locked or in use)" -ForegroundColor Yellow
}
Write-Host "  Space freed:    $(Format-FileSize $freed)" -ForegroundColor Green
Write-Host ""
Write-Host "Tip: Run again with -DaysOld 3 for a more aggressive cleanup." -ForegroundColor DarkGray

Write-Host ""
Read-Host "Press Enter to exit"
