; Storyboard AI Studio Pro - Professional Inno Setup Script
; Creates a native, commercial Windows Installer (StoryboardAI-Setup.exe)
; Self-contained with Embedded Python 3.11, FFmpeg, Node.js, and Studio Desktop.

#define MyAppName "Storyboard AI Studio Pro"
#define MyAppVersion "1.0"
#define MyAppPublisher "Storyboard AI Team"
#define MyAppURL "https://storyboardai.store"
#define MyAppExeName "Storyboard_AI_Studio.exe"
#define MySourceDir "d:\STORYBOARD_AI\dist\Storyboard_AI_Studio_Pro_v1.0"

[Setup]
AppId={{5E78D41C-8452-4B42-9AE2-C935B3111001}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
DefaultGroupName={#MyAppName}
OutputDir=d:\STORYBOARD_AI\dist
OutputBaseFilename=StoryboardAI-Setup
;SetupIconFile=d:\STORYBOARD_AI\studio\web\assets\storyboard_ai_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "{#MySourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up runtime on uninstall but preserve user productions
Type: files; Name: "{app}\studio\runtime\python\*"
Type: dirifempty; Name: "{app}\studio\runtime\python"
