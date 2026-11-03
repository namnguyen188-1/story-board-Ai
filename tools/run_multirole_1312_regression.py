import subprocess,sys,json,time
exe="D:/STORYBOARD_AI/studio/runtime/python/python.exe"
root="D:/STORYBOARD_AI/studio/tests"
suites=["test_drama_asset_first_20261031.py","test_drama_six_scene_continuity_20261031.py",
"test_reference_voice_guards_20261031.py","test_extra_reference_guards_20261031.py",
"test_native_audio_subtitle_sync.py","test_muse_cli_provider.py",
"test_muse_gateway_worker.py","test_muse_skill_input.py","test_muse_video_integration.py",
"test_native_muse_audio_merge.py"]
results=[]
for f in suites:
 st=time.time()
 interpreter="D:/STORYBOARD_AI/studio/runtime/muse/python/python.exe" if f=="test_muse_gateway_worker.py" else exe
 p=subprocess.run([interpreter,"-m","unittest","discover","-s",root,"-p",f,"-v"],
                  capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=95)
 lines=(p.stdout+"\n"+p.stderr).strip().splitlines()
 print("SUITE",f,"RC",p.returncode,"LAST",lines[-3:] if lines else [],flush=True)
 results.append({"suite":f,"exit_code":p.returncode,"duration":round(time.time()-st,2),"tail":lines[-16:]})
 if p.returncode:print("FIRST_REGRESSION_FAILURE",f,"\n".join(lines[-32:]),flush=True)
out="D:/STORYBOARD_AI/tools/multirole_1312_regressions.json"
open(out,"w",encoding="utf-8").write(json.dumps(results,ensure_ascii=False,indent=2))
print("REGRESSION_RESULT",sum(x["exit_code"]==0 for x in results),"/",len(results),flush=True)
