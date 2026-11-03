"""Patch retry/fallback safely into the standalone studio. No edits to V2."""
from pathlib import Path
import shutil, py_compile, json, datetime
root=Path(r"D:\STORYBOARD_AI\studio")
paths=[root/"series_studio.py",root/"engine"/"tools"/"utils.py"]
checkpoint=root/"checkpoints"/"retry_503_20261011"
checkpoint.mkdir(parents=True,exist_ok=True)
for p in paths:
    shutil.copy2(p,checkpoint/p.name)

p=root/"resilient_gemini.py"
s=p.read_text(encoding="utf-8")
s=s.replace('def call_with_retry(fn, model,', 'class TransientGeminiFailure(RuntimeError):\n    pass\n\ndef call_with_retry(fn, model,')
s=s.replace('    raise RuntimeError("Gemini temporarily unavailable after bounded retries and fallback. "',
            '    raise TransientGeminiFailure("Gemini temporarily unavailable after bounded retries and fallback. "')
p.write_text(s,encoding="utf-8")

p=root/"engine"/"tools"/"utils.py"
s=p.read_text(encoding="utf-8")
needle='from config import GEMINI_API_KEY'
assert needle in s, "utils import changed"
s=s.replace(needle,needle+'\nfrom resilient_gemini import ResilientClient',1)
needle='client = genai.Client(api_key=GEMINI_API_KEY)'
assert needle in s, "utils client creation changed"
s=s.replace(needle,'client = ResilientClient(genai.Client(api_key=GEMINI_API_KEY))',1)
p.write_text(s,encoding="utf-8")

p=root/"series_studio.py"
s=p.read_text(encoding="utf-8")
needle='from pathlib import Path'
assert needle in s
s=s.replace(needle,needle+'\nfrom resilient_gemini import ResilientClient, TransientGeminiFailure',1)
needle='client=genai.Client(api_key=key)'
assert needle in s
s=s.replace(needle,'client=ResilientClient(genai.Client(api_key=key))',1)
# Ensure wrapper handles transient retry; parser retry only for malformed JSON, not 503.
needle='''                    except Exception as exc:
                        err=exc
                        time.sleep(2*(attempt+1))'''
assert needle in s, "planner catch changed"
s=s.replace(needle,'''                    except TransientGeminiFailure as exc:
                        err=exc
                        break  # already retried with fallback: leave earlier batches untouched
                    except Exception as exc:
                        err=exc
                        if attempt<2:
                            time.sleep(2*(attempt+1))''',1)
p.write_text(s,encoding="utf-8")
for p in [root/"resilient_gemini.py",root/"series_studio.py",root/"engine"/"tools"/"utils.py"]:
    py_compile.compile(str(p),doraise=True)
print("503_RETRY_PATCH_PASS")
print("Checkpoint:",checkpoint)
