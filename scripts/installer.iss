[Setup]
#define AppName "Dota2-Minify"
#include "version_info.iss"

AppName={#AppName}
AppVersion={#AppVersion}

; "PrivilegesRequired=lowest" ensures the installer doesn't require admin rights
; and defaults to a user-writable folder (Local AppData).
PrivilegesRequired=lowest
DefaultDirName={localappdata}\{#AppName}
DefaultGroupName={#AppName}
UninstallDisplayIcon={app}\Minify.exe
Compression=lzma2
SolidCompression=yes
OutputDir=.
OutputBaseFilename=Minify-Setup-{#AppVersion}
; Ensure the app is closed before installing/updating
CloseApplications=yes
AppMutex=MinifyMutex
; Suppress the Start Menu folder page
DisableProgramGroupPage=yes
AllowNoIcons=yes

; Version Info (FFI) for the setup executable itself
VersionInfoVersion={#NumericVersion}
VersionInfoDescription={#AppName} Setup
VersionInfoProductName={#AppName}
VersionInfoProductVersion={#NumericVersion}
VersionInfoCopyright=Copyright (C) 2026 Egezenn

[UninstallDelete]
; Clean up runtime-generated folders on uninstall
Type: filesandordirs; Name: "{app}\config"
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\mods"
Type: filesandordirs; Name: "{app}\mods_old_*"
; Also clean up build directories if somehow leftover
Type: filesandordirs; Name: "{app}\vpk_build"
Type: filesandordirs; Name: "{app}\vpk_replace"
Type: filesandordirs; Name: "{app}\vpk_merge"
; Clean up runtime-downloaded binaries and libraries
Type: files; Name: "{app}\Source2Viewer-CLI.exe"
Type: files; Name: "{app}\rg.exe"
Type: files; Name: "{app}\*.dll"

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  OldModsPath, BackupPath, Timestamp: string;
begin
  if CurStep = ssInstall then
  begin
    OldModsPath := ExpandConstant('{app}\mods');
    if DirExists(OldModsPath) then
    begin
      Timestamp := GetDateTimeString('yyyymmdd_hhnnss', #0, #0);
      BackupPath := ExpandConstant('{app}\mods_old_') + Timestamp;
      Log('Moving old mods to: ' + BackupPath);
      if RenameFile(OldModsPath, BackupPath) then
      begin
        Log('Move successful.');
      end
      else
      begin
        // If rename fails, we fallback to deleting as a last resort
        // to keep the installation 'pristine'
        Log('Move failed, deleting old mods as fallback.');
        DelTree(OldModsPath, True, True, True);
      end;
    end;
  end;
end;

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "startmenuicon"; Description: "Create a &Start Menu shortcut"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\Minify\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Preserve config and mods on update if needed
; Inno Setup handles this by default (won't overwrite if newer/same unless specified)

[Icons]
; Create a folder in the Start Menu and put the shortcut inside it if the task is selected
Name: "{autoprograms}\{#AppName}\{#AppName}"; Filename: "{app}\Minify.exe"; Tasks: startmenuicon
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\Minify.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Minify.exe"; Description: "{cm:LaunchProgram,Dota2-Minify}"; Flags: nowait postinstall skipifsilent
