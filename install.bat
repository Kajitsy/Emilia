@echo off
net session >nul 2>&1
if %errorlevel% == 0 (
    echo Please run the script NOT as an administrator. https://github.com/Kajitsy/Emilia?tab=readme-ov-file#requirements-for-launch
    pause
    exit /b
) else (
    echo Creating virtual environment...
)

python -m venv .venv
call .venv\Scripts\activate

echo Installing dependencies... Please wait.
@echo on
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
@echo off
call lib\Scripts\deactivate.bat
pause