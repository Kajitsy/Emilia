@echo off
setlocal

call src\.venv\Scripts\activate
if exist requirements.txt (
    echo Installing dependencies from requirements.txt...
    pip install -r requirements.txt
) else (
    echo requirements.txt file not found. Skipping dependency installation.
)

pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller not found. Please install it.
    pip install pyinstaller
) else (
    echo PyInstaller is already installed.
)

echo Starting compilation of main.py...
@echo on
pyinstaller --noconfirm --onedir --windowed --icon ".\src\icon.ico" --uac-admin --add-data "VERSION;." --add-data "./src/.venv/Lib/site-packages/livekit/rtc/resources/livekit_ffi.dll;livekit/rtc/resources" --add-data "./src/.venv/Lib/site-packages/live2d/v3/FrameworkShaders;live2d/v3/FrameworkShaders" --collect-all "scipy" --hidden-import "urllib3.contrib.resolver.system" --hidden-import "urllib3.contrib.hface.protocols.http1" --hidden-import "urllib3.contrib.hface.protocols.http2" --hidden-import "OpenGL" ".\src\main.py"
@echo off
if exist ".\dist\main\main.exe" (
    echo Renaming main.exe to emilia.exe...
    rename ".\dist\main\main.exe" "emilia.exe"

    echo Copying icon.ico, VERSION, lang, themes and data folders to the EXE directory...
    copy ".\src\icon.ico" ".\dist\main\icon.ico"
    copy "VERSION" ".\dist\main\VERSION"
    xcopy /E /I /H /Y ".\src\lang" ".\dist\main\lang"
    xcopy /E /I /H /Y ".\src\themes" ".\dist\main\themes"
    xcopy /E /I /H /Y ".\src\data" ".\dist\main\data"

    echo Done! All files are located in .\dist\main\
) else (
    echo Failed to find main.exe for renaming.
)

pause
endlocal