from pathlib import Path
root=Path(r"D:\STORYBOARD_AI")
src=(root/"installer.iss").read_text(encoding="utf-8-sig")
pairs={
'#define MyAppName "Storyboard AI Studio Pro"':'#define MyAppName "Storyboard AI Studio Pro - MultiGPU Candidate"',
'#define MyAppVersion "1.0"':'#define MyAppVersion "1.0.1-rc"',
'#define MySourceDir "d:\\STORYBOARD_AI\\dist\\Storyboard_AI_Studio_Pro_v1.0"':'#define MySourceDir "d:\\STORYBOARD_AI\\dist\\Storyboard_AI_Studio_Pro_MultiGPU_Candidate"',
'AppId={{5E78D41C-8452-4B42-9AE2-C935B3111001}':'AppId={{67C4C116-6B35-477A-9532-6347F44728C0}',
'OutputBaseFilename=StoryboardAI-Setup':'OutputBaseFilename=StoryboardAI-MultiGPU-Candidate-Setup'}
for a,b in pairs.items():
 if src.count(a)!=1:raise RuntimeError("MISSING ISS ENTRY:"+a)
 src=src.replace(a,b,1)
p=root/"dist"/"MultiGPU-Candidate-Installer.iss"
p.write_text(src,encoding="utf-8")
print("CANDIDATE_ISS",p)
