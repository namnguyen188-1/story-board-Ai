import os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from resilient_gemini import call_with_retry, TransientGeminiFailure
class Fake503(Exception):
    code=503
class Fake401(Exception):
    code=401
class Stub:
    def __init__(self,failures):
        self.failures=failures
        self.calls=[]
    def generate_content(self,*,model,**kwargs):
        self.calls.append(model)
        if model in self.failures:
            raise self.failures[model]
        return {"success":model}
f=Stub({"gemini-3.8-flash":Fake503("high demand")})
r=call_with_retry(f.generate_content,"gemini-3.8-flash",max_primary=2,max_fallback=1,
                  base_delay=0,sleeper=lambda x: None)
assert r["success"]=="gemini-3.6-flash",(r,f.calls)
assert f.calls==["gemini-3.8-flash","gemini-3.8-flash","gemini-3.6-flash"]
print("TEST_503_FALLBACK_PASS",f.calls)
f=Stub({"gemini-3.8-flash":Fake401("key invalid")})
try:
    call_with_retry(f.generate_content,"gemini-3.8-flash",base_delay=0,sleeper=lambda x: None)
except Fake401:
    pass
else:
    raise AssertionError("401 must not be retried")
assert f.calls==["gemini-3.8-flash"]
print("TEST_401_NO_RETRY_PASS")
f=Stub({"gemini-3.8-flash":Fake503("down"),"gemini-3.6-flash":Fake503("down"),"gemini-3.5-flash-lite":Fake503("down")})
try:
    call_with_retry(f.generate_content,"gemini-3.8-flash",max_primary=2,max_fallback=1,
                    base_delay=0,sleeper=lambda x: None)
except TransientGeminiFailure:
    pass
else:
    raise AssertionError("must fail after bounded retry")
assert len(f.calls)==4
print("TEST_BOUNDED_FAIL_PASS")
f=Stub({"gemini-3.8-flash":Fake503("down")})
os.environ["STORYBOARD_DISABLE_MODEL_FALLBACK"]="1"
try:
    call_with_retry(f.generate_content,"gemini-3.8-flash",max_primary=2,
                    base_delay=0,sleeper=lambda x: None)
except TransientGeminiFailure:
    pass
else:
    raise AssertionError("fallback disable failed")
assert f.calls==["gemini-3.8-flash","gemini-3.8-flash"]
del os.environ["STORYBOARD_DISABLE_MODEL_FALLBACK"]
print("TEST_FALLBACK_DISABLED_PASS")
print("ALL_RETRY_UNIT_TESTS_PASS")

class Fake429(Exception):
    code=429
f=Stub({name:Fake429("You exceeded your current quota for this model")
        for name in ("gemini-nano-banana-2.1","gemini-3.1-flash-image","gemini-3.1-flash-lite-image")})
try:
    call_with_retry(f.generate_content,"gemini-nano-banana-2.1",
                    max_primary=3,max_fallback=2,base_delay=0,sleeper=lambda x:None)
except TransientGeminiFailure as exc:
    assert "429" in str(exc),str(exc)
else:
    raise AssertionError("429 must fail cleanly after compatible fallbacks")
assert f.calls==["gemini-nano-banana-2.1","gemini-3.1-flash-image","gemini-3.1-flash-lite-image"],f.calls
print("TEST_HARD_QUOTA_THROTTLING_PASS")
