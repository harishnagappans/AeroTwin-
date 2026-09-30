@echo off
cd /d "%~dp0"
echo Starting Aerotwin REST API Backend on http://localhost:8000 ...
start "Aerotwin REST API Backend" /min .\.venv\Scripts\python.exe backend/server.py

echo Starting Aerotwin React Dashboard Frontend on http://localhost:3000 ...
start "Aerotwin React Dashboard" /min .\.venv\Scripts\python.exe frontend/server.py

echo Done! Aerotwin system is running.

