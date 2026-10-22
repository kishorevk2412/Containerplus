@echo off
title ContainerPulse DevOps Platform
echo ===================================================
echo Starting ContainerPulse Web App on port 5000...
echo ===================================================
cd /d "%~dp0app"
py app.py
pause
