@echo off
powershell -NoExit -ExecutionPolicy Bypass -Command "& .\.venv\Scripts\Activate.ps1; python main.py"
