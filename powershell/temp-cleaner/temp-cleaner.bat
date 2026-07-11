@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0temp-cleaner.ps1" %*
