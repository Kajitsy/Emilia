#define MyAppName "Emilia"
#define MyAppVersion "3.2.1"
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
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes
LZMANumBlockThreads=2

ArchitecturesInstallIn64BitMode=x64
ArchitecturesAllowed=x64
MinVersion=10.0

SetupIconFile=".\src\icon.ico"
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
WizardStyle=modern
DisableWelcomePage=no
ShowLanguageDialog=auto

LicenseFile=LICENSE

PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: ".\dist\main\emilia.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: ".\dist\main\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs
Source: ".\src\icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: ".\src\lang\*"; DestDir: "{app}\lang"; Flags: ignoreversion recursesubdirs
Source: ".\src\data\*"; DestDir: "{app}\data"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon; Comment: "{#MyAppName}"


[Registry]
Root: HKCU; Subkey: "Software\{#MyAppName}"; ValueName: "InstallPath"; ValueData: "{app}"
Root: HKCU; Subkey: "Software\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "Version"; ValueData: "{#MyAppVersion}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "InstallDate"; ValueData: "{code:GetInstallDate}"; Flags: uninsdeletekey


[UninstallRun]
Filename: "{cmd}"; Parameters: "/C ""taskkill /im {#MyAppExeName} /f /t"

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
Type: filesandordirs; Name: "{localappdata}\{#MyAppName}"

[Code]
function GetInstallDate(Param: String): String;
begin
  Result := GetDateTimeString('dd/mm/yyyy', '-', ':');
end;