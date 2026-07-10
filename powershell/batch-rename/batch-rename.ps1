<#
.SYNOPSIS
    Interactive batch rename tool. Just run it — no arguments needed.

.DESCRIPTION
    Walks you through choosing a folder, a rename operation, and a preview
    before touching anything. Everything is done through on-screen prompts.

.EXAMPLE
    ./batch-rename-interactive.ps1
    Then just answer the questions on screen.
#>

$ErrorActionPreference = "Stop"

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

function Select-FolderDialog {
    # Try the graphical folder picker; fall back to typed path if unavailable
    try {
        Add-Type -AssemblyName System.Windows.Forms | Out-Null
        $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
        $dialog.Description = "Select the folder containing files to rename"
        $dialog.ShowNewFolderButton = $false
        $result = $dialog.ShowDialog()
        if ($result -eq [System.Windows.Forms.DialogResult]::OK) {
            return $dialog.SelectedPath
        } else {
            return $null
        }
    } catch {
        return $null
    }
}

function Get-TargetFolder {
    Write-Step "Step 1: Choose a folder"
    Write-Host "1. Open a folder picker window"
    Write-Host "2. Type a path manually"
    Write-Host "3. Use current folder ($(Get-Location))"
    $choice = Read-Prompt "Choose an option" "1"

    switch ($choice) {
        "1" {
            $picked = Select-FolderDialog
            if ($picked) {
                return $picked
            } else {
                Write-Host "No folder picker available or cancelled. Falling back to manual entry." -ForegroundColor DarkYellow
                return Read-Prompt "Enter full folder path"
            }
        }
        "2" {
            return Read-Prompt "Enter full folder path"
        }
        "3" {
            return (Get-Location).Path
        }
        default {
            return (Get-Location).Path
        }
    }
}

# ===========================================================================
# INTRO
# ===========================================================================

Write-Title "Interactive Batch Rename"
Write-Host "This tool renames files in a folder. Nothing is changed until you confirm a preview."

# ===========================================================================
# STEP 1: FOLDER
# ===========================================================================

$targetPath = Get-TargetFolder

if (-not (Test-Path $targetPath)) {
    Write-Host ""
    Write-Host "That path doesn't exist: $targetPath" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit
}

$resolvedPath = Resolve-Path $targetPath

# Store logs centrally (not inside the folder being modified), keyed by a hash
# of the folder path so each folder gets its own undo history.
$logRoot = Join-Path $env:APPDATA "BatchRenameTool\logs"
if (-not (Test-Path $logRoot)) {
    New-Item -ItemType Directory -Path $logRoot -Force | Out-Null
}

$pathHash = [System.BitConverter]::ToString(
    [System.Security.Cryptography.SHA256]::Create().ComputeHash(
        [System.Text.Encoding]::UTF8.GetBytes($resolvedPath.Path.ToLower())
    )
).Replace("-", "").Substring(0, 16)

$logFile = Join-Path $logRoot "$pathHash.json"

Write-Host ""
Write-Host "Using folder: $resolvedPath" -ForegroundColor Green

# ===========================================================================
# UNDO CHECK
# ===========================================================================

if (Test-Path $logFile) {
    Write-Step "A previous rename was found in this folder."
    $wantUndo = Read-YesNo "Undo the last rename before continuing?" $false

    if ($wantUndo) {
        $log = Get-Content $logFile -Raw | ConvertFrom-Json
        $errors = 0
        foreach ($entry in $log) {
            $currentPath = Join-Path $resolvedPath $entry.NewName
            $originalPath = Join-Path $resolvedPath $entry.OldName

            if (-not (Test-Path $currentPath)) {
                Write-Host "  SKIP (not found): $($entry.NewName)" -ForegroundColor DarkYellow
                continue
            }
            if (Test-Path $originalPath) {
                Write-Host "  SKIP (would overwrite): $($entry.OldName)" -ForegroundColor DarkYellow
                $errors++
                continue
            }
            try {
                Rename-Item -LiteralPath $currentPath -NewName $entry.OldName
                Write-Host "  Reverted: $($entry.NewName) -> $($entry.OldName)" -ForegroundColor Green
            } catch {
                Write-Host "  ERROR reverting $($entry.NewName): $_" -ForegroundColor Red
                $errors++
            }
        }
        if ($errors -eq 0) {
            Remove-Item $logFile -Force
            Write-Host "Undo complete." -ForegroundColor Green
        }
        Write-Host ""
        $continueAfterUndo = Read-YesNo "Continue with a new rename operation now?" $true
        if (-not $continueAfterUndo) { exit }
    }
}

# ===========================================================================
# STEP 2: FILTER
# ===========================================================================

Write-Step "Step 2: Which files?"
$filterInput = Read-Prompt "File filter (e.g. *.jpg, mp4, txt, or * for all)" "*"

# Normalize common shorthand into a valid wildcard filter:
#   "mp4"      -> "*.mp4"
#   ".mp4"     -> "*.mp4"
#   "*.mp4"    -> "*.mp4"  (unchanged)
#   "*"        -> "*"      (unchanged)
$filter = $filterInput.Trim()
if ($filter -ne "*" -and -not $filter.Contains("*")) {
    if ($filter.StartsWith(".")) {
        $filter = "*$filter"
    } else {
        $filter = "*.$filter"
    }
}

if ($filter -ne $filterInput) {
    Write-Host "Using filter: $filter" -ForegroundColor DarkGray
}

$recurse = Read-YesNo "Include subfolders?" $false

$getChildParams = @{ Path = $resolvedPath; Filter = $filter; File = $true }
if ($recurse) { $getChildParams["Recurse"] = $true }

$files = Get-ChildItem @getChildParams | Sort-Object Name

if ($files.Count -eq 0) {
    Write-Host ""
    Write-Host "No files matched '$filter' in that folder." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit
}

Write-Host ""
Write-Host "Found $($files.Count) file(s)." -ForegroundColor Green

# ===========================================================================
# STEP 3: OPERATION MENU
# ===========================================================================

Write-Step "Step 3: What do you want to do?"
Write-Host "1. Find and replace text"
Write-Host "2. Add a prefix"
Write-Host "3. Add a suffix"
Write-Host "4. Add sequential numbers"
Write-Host "5. Change case (lower/upper/title)"
Write-Host "6. Combine multiple of the above"
$opChoice = Read-Prompt "Choose an option" "1"

$find = ""
$replace = ""
$useRegex = $false
$prefix = ""
$suffix = ""
$useNumber = $false
$numberStart = 1
$numberPadding = 2
$caseStyle = ""

function Prompt-FindReplace {
    $script:find = Read-Prompt "Text to find"
    $script:replace = Read-Prompt "Replace with (leave blank to remove it)" ""
    $script:useRegex = Read-YesNo "Treat 'find' as a regular expression?" $false
}

function Prompt-Prefix {
    $script:prefix = Read-Prompt "Prefix to add"
}

function Prompt-Suffix {
    $script:suffix = Read-Prompt "Suffix to add (before the file extension)"
}

function Prompt-Number {
    $script:useNumber = $true
    $script:numberStart = [int](Read-Prompt "Start number" "1")
    $script:numberPadding = [int](Read-Prompt "Digit padding (e.g. 2 = 01, 3 = 001)" "2")
}

function Prompt-Case {
    Write-Host "  a. lower case"
    Write-Host "  b. UPPER CASE"
    Write-Host "  c. Title Case"
    $c = Read-Prompt "Choose" "a"
    $script:caseStyle = switch ($c) {
        "a" { "Lower" }
        "b" { "Upper" }
        "c" { "Title" }
        default { "Lower" }
    }
}

switch ($opChoice) {
    "1" { Prompt-FindReplace }
    "2" { Prompt-Prefix }
    "3" { Prompt-Suffix }
    "4" { Prompt-Number }
    "5" { Prompt-Case }
    "6" {
        if (Read-YesNo "Include find and replace?" $false) { Prompt-FindReplace }
        if (Read-YesNo "Include a prefix?" $false) { Prompt-Prefix }
        if (Read-YesNo "Include a suffix?" $false) { Prompt-Suffix }
        if (Read-YesNo "Include sequential numbering?" $false) { Prompt-Number }
        if (Read-YesNo "Include a case change?" $false) { Prompt-Case }
    }
    default { Prompt-FindReplace }
}

# ===========================================================================
# BUILD PLAN
# ===========================================================================

$plan = @()
$counter = $numberStart

foreach ($file in $files) {
    $baseName = $file.BaseName
    $ext = $file.Extension
    $newBase = $baseName

    if ($find) {
        if ($useRegex) {
            $newBase = [regex]::Replace($newBase, $find, $replace)
        } else {
            $newBase = $newBase.Replace($find, $replace)
        }
    }

    if ($caseStyle) {
        switch ($caseStyle) {
            "Lower" { $newBase = $newBase.ToLower() }
            "Upper" { $newBase = $newBase.ToUpper() }
            "Title" { $newBase = (Get-Culture).TextInfo.ToTitleCase($newBase.ToLower()) }
        }
    }

    if ($prefix) { $newBase = "$prefix$newBase" }
    if ($suffix) { $newBase = "$newBase$suffix" }

    if ($useNumber) {
        $numStr = $counter.ToString().PadLeft($numberPadding, '0')
        $newBase = "$newBase-$numStr"
        $counter++
    }

    $newName = "$newBase$ext"

    $plan += [PSCustomObject]@{
        OldName = $file.Name
        NewName = $newName
        OldPath = $file.FullName
        NewPath = Join-Path $file.DirectoryName $newName
        Changed = ($file.Name -ne $newName)
    }
}

# ===========================================================================
# PREVIEW
# ===========================================================================

Write-Title "Preview"

$changed = $plan | Where-Object { $_.Changed }

if ($changed.Count -eq 0) {
    Write-Host "No filenames would change with these options." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit
}

foreach ($item in $changed) {
    Write-Host "  $($item.OldName)" -NoNewline
    Write-Host "  ->  " -ForegroundColor DarkGray -NoNewline
    Write-Host "$($item.NewName)" -ForegroundColor Green
}

Write-Host ""
Write-Host "$($changed.Count) of $($files.Count) file(s) will be renamed." -ForegroundColor Cyan

# Collision checks
$duplicates = $changed | Select-Object -ExpandProperty NewName | Group-Object | Where-Object { $_.Count -gt 1 }
if ($duplicates.Count -gt 0) {
    Write-Host ""
    Write-Host "ERROR: These operations would produce duplicate filenames:" -ForegroundColor Red
    $duplicates | ForEach-Object { Write-Host "  $($_.Name) (x$($_.Count))" -ForegroundColor Red }
    Write-Host "Aborting. Run the script again with different options." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit
}

foreach ($item in $changed) {
    if ((Test-Path $item.NewPath) -and ($item.NewPath -ne $item.OldPath)) {
        Write-Host ""
        Write-Host "ERROR: Target file already exists: $($item.NewName)" -ForegroundColor Red
        Write-Host "Aborting to avoid overwriting existing files." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit
    }
}

# ===========================================================================
# CONFIRM AND APPLY
# ===========================================================================

Write-Host ""
$confirm = Read-YesNo "Apply these changes now?" $false

if (-not $confirm) {
    Write-Host ""
    Write-Host "No changes made. Run the script again anytime." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit
}

Write-Title "Applying"

$log = @()
$errors = 0

foreach ($item in $changed) {
    try {
        Rename-Item -LiteralPath $item.OldPath -NewName $item.NewName
        Write-Host "  Renamed: $($item.OldName) -> $($item.NewName)" -ForegroundColor Green
        $log += [PSCustomObject]@{ OldName = $item.OldName; NewName = $item.NewName }
    } catch {
        Write-Host "  ERROR renaming $($item.OldName): $_" -ForegroundColor Red
        $errors++
    }
}

if ($log.Count -gt 0) {
    $log | ConvertTo-Json | Set-Content -Path $logFile
    Write-Host ""
    Write-Host "Done. $($log.Count) file(s) renamed." -ForegroundColor Cyan
    Write-Host "Run this script again in this folder to undo, if needed." -ForegroundColor DarkGray
}

if ($errors -gt 0) {
    Write-Host "$errors file(s) failed to rename." -ForegroundColor Yellow
}

Write-Host ""
Read-Host "Press Enter to exit"