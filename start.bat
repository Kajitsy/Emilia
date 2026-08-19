@echo off
net session >nul 2>&1
if %errorlevel% == 0 (
    echo Please run the script NOT as an administrator. https://github.com/Kajitsy/Emilia?tab=readme-ov-file#requirements-for-launch
    pause
    exit /b
) else (
    echo Hello Dear User :3
)
cd src
@echo on
call .venv\Scripts\activate
python main.py
@echo off
call .venv\Scripts\deactivate.bat
pause