[Setup]
#define AppName "Dota2-Minify Portable"
#include "version_info.iss"

AppName={#AppName}
AppVersion={#AppVersion}
PrivilegesRequired=lowest
DefaultDirName={src}\Dota2-Minify-Portable-{#AppVersion}
DisableDirPage=yes
DisableProgramGroupPage=yes
DisableWelcomePage=yes
DisableFinishedPage=yes
Uninstallable=no
CreateUninstallRegKey=no
OutputDir=.
OutputBaseFilename=Minify-Portable-v{#AppVersion}
Compression=lzma2
SolidCompression=yes
CloseApplications=yes
AppMutex=MinifyMutex

[Files]
Source: "dist\Minify\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Run]
Filename: "{app}\Minify.exe"; Flags: nowait postinstall skipifsilent
