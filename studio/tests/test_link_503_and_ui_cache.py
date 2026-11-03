from pathlib import Path
import sys,shutil,datetime
r=Path(r"D:\STORYBOARD_AI\studio")
p=r/"web"/"index.html"
cp=r/"checkpoints"/("multigenre_ui_cache_"+datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
cp.mkdir(parents=True,exist_ok=True)
shutil.copy2(p,cp/p.name)
s=p.read_text(encoding="utf-8")
if '<script src="app.js"></script>' in s:
    s=s.replace('<script src="app.js"></script>',
                '<script src="app.js?v=20261012_multigenre_v2"></script>',1)
elif 'app.js?v=20261012_multigenre_v2' not in s:
    raise RuntimeError("Unknown frontend script entrypoint")
p.write_text(s,encoding="utf-8")
sys.path.insert(0,str(r))
from studio_input_modes import analyze_reference
class Unavailable:
    def generate_content(self,**kwargs):
        raise RuntimeError("503 Service Unavailable")
class FakeClient: models=Unavailable()
try:
    analyze_reference(FakeClient(),"gemini-3.8-flash","https://youtu.be/9hE5-98ZeCg")
except RuntimeError as exc:
    assert "VIDEO_REFERENCE_SERVICE_UNAVAILABLE" in str(exc),str(exc)
    assert "tự bịa" in str(exc)
    print("YOUTUBE_503_USER_FRIENDLY_NO_FAKE_ANALYSIS_PASS",flush=True)
else:
    raise AssertionError("503 must not convert into fabricated analysis")
assert 'id="inGenre"' in s and 'id="inVisualStyle"' in s
assert 'id="inInputMode"' in s and 'id="inReferenceUrl"' in s
print("MULTIGENRE_DESKTOP_UI_FIELDS_AND_CACHE_PASS",flush=True)
