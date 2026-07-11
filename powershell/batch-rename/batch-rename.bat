@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0batch-rename.ps1" %*
