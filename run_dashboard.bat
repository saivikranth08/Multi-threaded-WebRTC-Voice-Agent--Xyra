@echo off
title XYRA Dashboard
echo ==============================================
echo        Starting XYRA Dashboard Server
echo        Open http://localhost:8000 in Chrome
echo ==============================================
cd /d "D:\AI\xyra"
.venv\Scripts\python.exe run_dashboard.py
pause
