net session >nul 2>&1
if %errorlevel% == 0 (
    echo Please run the script NOT as an administrator. https://github.com/Kajitsy/Emilia?tab=readme-ov-file#requirements-for-launch
    pause
    exit /b
) else (
    echo Hello Dear User :3
)
call .venv\Scripts\activate
python main.py
call .venv\Scripts\deactivate.bat
pause