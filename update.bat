echo Updating libraries
call .venv\Scripts\activate

echo Installing dependencies... Please wait.
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

call lib\Scripts\deactivate.bat
pause