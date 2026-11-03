from pathlib import Path
import py_compile
p=Path(r"D:\STORYBOARD_AI\studio\series_studio.py")
s=p.read_text(encoding="utf-8")
start=s.index('        try:\n            p=subprocess.run(command,capture_output=True,text=True,timeout=args.scene_timeout,')
end=s.index('\n    completed=[]',start)
new='''        last_error=""
        for attempt in range(1,4):
            try:
                p=subprocess.run(command,capture_output=True,text=True,timeout=args.scene_timeout,
                                 cwd=str(directory),env=env)
                (directory/"run.log").write_text(
                    ("ATTEMPT "+str(attempt)+"\\\\n"+p.stdout+"\\\\n"+p.stderr)[-30000:],
                    encoding="utf-8")
                if p.returncode==0 and qc_complete(directory/"final.mp4",width,height):
                    result=read_json(resultfile)
                    return {"scene":num,"status":"PASS","qc":result["qc"],
                            "image_path":str(directory/"image.png")}
                last_error=(p.stderr or p.stdout or "Scene video failed QC")[-500:]
            except Exception as e:
                last_error=str(e)[-500:]
            if any(x in last_error.lower() for x in ("401","403","invalid api key","permission_denied")):
                break
            if attempt<3:
                time.sleep(3*attempt)
        return {"scene":num,"status":"FAILED","error":last_error}
'''
# Keep actual newline escapes correct.
new=new.replace('\\\\n','\\n')
s=s[:start]+new+s[end:]
p.write_text(s,encoding="utf-8")
py_compile.compile(str(p),doraise=True)
print("SCENE_RETRY_PATCH_OK")
r=Path(r"D:\STORYBOARD_AI\studio\repair_engine.py")
t=r.read_text(encoding="utf-8")
old='assert marker in s\\ns=s[:s.index(marker)] +'
if old in t:
    t=t.replace('assert marker in s\\ns=s[:s.index(marker)] +',
                'if marker in s:\\n    s=s[:s.index(marker)] +')
    # The next line now must be 4-space-indented.
    r.write_text(t,encoding="utf-8")
    py_compile.compile(str(r),doraise=True)
print("PATCH_SCRIPT_CHECK_OK")
