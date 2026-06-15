@echo off
title XYRA Voice Agent Daemon
echo ==============================================
echo        Starting XYRA Voice Agent Worker
echo ==============================================
cd /d "D:\AI\xyra"
set PYTHONPATH=D:\AI\xyra
.venv\Scripts\python.exe -m xyra.agent dev
pause
