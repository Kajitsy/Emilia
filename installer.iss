#define MyAppName "Emilia"
#define MyAppVersion "3.0.3"
#define MyAppPublisher "Kajitsy"
#define MyAppURL "https://github.com/Kajitsy/Emilia"
#define MyAppExeName "emilia.exe"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
VersionInfoVersion={#MyAppVersion}
AppVerName={#MyAppName}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={pf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=.\
OutputBaseFilename={#MyAppName}Setup
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
ArchitecturesAllowed=x64
MinVersion=10.0
LicenseFile=LICENSE
SetupIconFile=".\icon.ico"
UninstallDisplayIcon={app}\{#MyAppExeName}

[Files]
Source: ".\dist\main\emilia.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: ".\icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: ".\dist\main\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs
Source: ".\lang\*"; DestDir: "{app}\lang"; Flags: ignoreversion recursesubdirs
Source: ".\data\*"; DestDir: "{app}\data"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

[Registry]
Root: HKCU; Subkey: "Software\{#MyAppName}"; ValueName: "InstallPath"; ValueData: "{app}"

[UninstallRun]
Filename: "{cmd}"; Parameters: "/C ""taskkill /im {#MyAppExeName} /f /t"

[UninstallDelete]
Type: filesandordirs; Name: "{app}\*"
Type: filesandordirs; Name: "{app}"
