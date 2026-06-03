@echo off
REM ============================================================
REM Task Scheduler chay file nay dinh ky: sync vault Obsidian -> Supabase.
REM Vault path + Supabase key doc tu .streamlit\secrets.toml (UTF-8).
REM Khong de chuoi Unicode trong file .bat -> tranh loi ma hoa code page.
REM ============================================================
chcp 65001 >nul
cd /d "%~dp0.."
echo ===== Sync %DATE% %TIME% ===== >> "scripts\sync-log.txt"
python "scripts\run_sync.py" >> "scripts\sync-log.txt" 2>&1
echo. >> "scripts\sync-log.txt"
