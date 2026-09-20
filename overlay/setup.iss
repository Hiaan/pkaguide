; Instalador nativo do PKA GUIDE Overlay (Inno Setup)
; Não usa Python nem descompacta nada na pasta Temp: instala a pasta do app direto.
#define AppName    "PKA GUIDE"
#define AppVersion "2.2.0"
#define AppExe     "PKA GUIDE.exe"

[Setup]
AppId={{8E2F1C64-9B3D-4A77-9E15-PKAGUIDE0001}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=PKA GUIDE
AppPublisherURL=https://pkaguide.vercel.app
DefaultDirName={localappdata}\{#AppName}\app
DisableDirPage=yes
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=dist
OutputBaseFilename=PKA GUIDE Setup
SetupIconFile=logo.ico
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=force
CloseApplicationsFilter=*.exe

[Languages]
Name: "pt"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Files]
Source: "dist\PKA GUIDE\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"; Comment: "Guia de itens do PokeAlliance"
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"

[Run]
Filename: "{app}\{#AppExe}"; Description: "Abrir o {#AppName} agora"; Flags: nowait postinstall skipifsilent

[InstallDelete]
; remove instalações antigas (1.x ficavam soltas fora da pasta app)
Type: files; Name: "{localappdata}\{#AppName}\{#AppExe}"
Type: filesandordirs; Name: "{localappdata}\PKA Guide Overlay"
Type: files; Name: "{autodesktop}\PKA Guide Overlay.lnk"
Type: files; Name: "{autoprograms}\PKA Guide Overlay.lnk"
