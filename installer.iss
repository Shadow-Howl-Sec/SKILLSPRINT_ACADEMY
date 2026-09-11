#define MyAppName "SkillSprint Academy"
#ifndef MyAppVersion
	#define MyAppVersion "1.1.0"
#endif
#define MyAppPublisher "SkillSprint Academy"
#define MyAppExeName "SkillSprintAcademy.exe"
#define ReleaseDir "release"

[Setup]
AppId={{D4F4A3B7-0A2E-4D0C-9D7A-8E2F2B4C7A11}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\SkillSprintAcademy
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir={#ReleaseDir}
OutputBaseFilename=SkillSprintAcademy-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile={#ReleaseDir}\SkillSprintAcademy\_internal\static\img\skill_logo.ico
UninstallDisplayIcon={app}\SkillSprintAcademy\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
ArchitecturesInstallIn64BitMode=x64compatible
ChangesAssociations=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "{#ReleaseDir}\SkillSprintAcademy\*"; DestDir: "{app}\SkillSprintAcademy"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#ReleaseDir}\bundles\*"; DestDir: "{app}\bundles"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#ReleaseDir}\scripts\*"; DestDir: "{app}\scripts"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#ReleaseDir}\README.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#ReleaseDir}\Start-SkillSprintAcademy.bat"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\SkillSprintAcademy\{#MyAppExeName}"; WorkingDir: "{app}\SkillSprintAcademy"; Comment: "{#MyAppName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\SkillSprintAcademy\{#MyAppExeName}"; WorkingDir: "{app}\SkillSprintAcademy"; Tasks: desktopicon; Comment: "{#MyAppName}"

[Run]
Filename: "{app}\SkillSprintAcademy\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; WorkingDir: "{app}\SkillSprintAcademy"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\SkillSprintAcademy"
Type: filesandordirs; Name: "{app}\bundles"
Type: filesandordirs; Name: "{app}\scripts"
