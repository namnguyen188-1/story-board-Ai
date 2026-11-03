from pathlib import Path
import subprocess,json,hashlib,os,ast
root=Path(r"D:\STORYBOARD_AI")
stage=root/"dist"/"Storyboard_AI_Studio_Pro_Transfer_Test_20261015"
src=(root/"dist"/"TransferTest-FULL-Installer.iss").read_text(encoding="utf-8")
assert src.count('OutputBaseFilename=StoryboardAI-TransferTest-FULL-Setup')==1
src=src.replace('OutputBaseFilename=StoryboardAI-TransferTest-FULL-Setup',
                'OutputBaseFilename=StoryboardAI-AutoSetup-TransferTest-Setup')
src=src.replace('AppName={#MyAppName}','AppName={#MyAppName}')
src=src.replace('#define MyAppVersion "1.1.0"','#define MyAppVersion "1.2.0"')
src=src.replace('#define MyAppName "Storyboard AI Studio Pro - Transfer Test"',
                '#define MyAppName "Storyboard AI Studio Pro - Auto Setup Test"')
src=src.replace('AppId={{A54F0C82-760E-4696-AB3B-C9417BC34C2D}',
                'AppId={{9C3F4A84-D9F5-4A0A-9762-F0273C95651C}')
src=src.replace('DefaultDirName={localappdata}\\Programs\\StoryboardAI-TransferTest',
                'DefaultDirName={localappdata}\\Programs\\StoryboardAI-AutoSetup-Test')
src=src.replace('[Languages]','[Languages]')
# Windows Start Menu entry opens bootstrap wizard after the app is closed.
needle='Name: "{autoprograms}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"'
assert src.count(needle)==1
src=src.replace(needle,needle+'\nName: "{autoprograms}\\Storyboard AI - Kiem tra va cai GPU"; Filename: "{app}\\{#MyAppExeName}"; Parameters: "--setup"')
# Don't set up a second application until the user explicitly selects the install mode.
# This cache allows customer-side repair without access to the original USB.
src += """
[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  CacheDir, FromFile, CacheFile, Checksum: string;
begin
  if CurStep = ssPostInstall then
  begin
    CacheDir := ExpandConstant('{localappdata}\\StoryboardAI-TransferTest\\repair');
    if ForceDirectories(CacheDir) then
    begin
      FromFile := ExpandConstant('{srcexe}');
      CacheFile := CacheDir + '\\setup.exe';
      if FileCopy(FromFile, CacheFile, False) then
      begin
        Checksum := GetSHA256OfFile(CacheFile);
        SaveStringToFile(CacheFile + '.sha256', Checksum, False);
      end;
    end;
  end;
end;
"""
out=root/"dist"/"AutoSetup-TransferTest-Installer.iss"
out.write_text(src,encoding="utf-8")
print("NEW_INSTALLER",out)
# Packaged runtime only, no private tokens, licensed model weights not bundled.
note=stage/"MODEL_LICENSE_AND_GPU_NOTES.txt"
note.write_text(
"Storyboard AI Auto-Setup TEST\\n"
"GPU runtime: Official Comfy-Org/ComfyUI GitHub releases selected for Nvidia/AMD/Intel.\\n"
"GPU model (only after customer consent): Stability AI SDXL 1.0 Base,\\n"
"https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0\\n"
"License: CreativeML Open RAIL++-M. Customers must review its conditions.\\n"
"GPU backend download and model may exceed 20GB disk use and require many GB of network traffic.\\n"
"No AMD/Intel hardware or large downloads validated yet. No auto GPU-driver installation.\\n"
"Cloud MCP/API can operate without local GPU setup but requires customer credentials.\\n"
"Missing core blocks startup; cached original installer is used for repair.\\n",
encoding="utf-8")
print("NOTES_WRITTEN",note)
