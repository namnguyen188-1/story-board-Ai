"""Update stoic preset in thumbnail_studio.py and seo_packager.py to be an authentic classical sculpted statue."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent

# 1. Update studio/thumbnail_studio.py
ts_p = ROOT / "studio" / "thumbnail_studio.py"
ts_text = ts_p.read_text(encoding="utf-8")

old_prompt_pat = r'"subject_prompt":\s*\([\s\S]*?"never lifeless stone statue[\s\S]*?\),'
new_prompt = """"subject_prompt": (
            "Monumental heroic classical sculpted marble and antique bronze statue of a Stoic philosopher god ({char_desc}), "
            "deeply chiseled stone anatomy, massive sculpted bare shoulder and pectoral chest, thick muscular neck, deeply carved curly stone beard and hair, sculpted classical statue eyes, "
            "wearing a vibrant royal crimson red draped toga (chlamys) over one shoulder, warm golden firelight rim lighting outlining sculpted rock muscles, "
            "magnificent illuminated ancient Athens Acropolis and Parthenon on distant rocky hill in deep starry night sky with glowing emerald teal aurora borealis and floating golden embers, "
            "sculpture strictly occupying 50% on the RIGHT half facing towards the left, leaving the entire LEFT 50% open deep twilight atmospheric sky for bold typography, "
            "chest-up low-angle framing, never full body, never standing on distant pedestal, photorealistic 8k render of a majestic monumental classical sculpture, cinematic lighting, no text, no watermark."
        ),"""

ts_text, c1 = re.subn(old_prompt_pat, new_prompt, ts_text, count=1)
print(f"Updated thumbnail_studio.py stoic preset: {c1}")

# Set accent_color to yellow by default for Valor Estoico style (Yellow / White / Yellow)
old_acc = '"accent_color": (229, 9, 20),'
new_acc = '"accent_color": (255, 230, 0),'
if old_acc in ts_text:
    ts_text = ts_text.replace(old_acc, new_acc, 1)
    print("Updated stoic accent color to Solar Yellow")

ts_p.write_text(ts_text, encoding="utf-8")

# 2. Update studio/seo_packager.py fallback prompt
sp_p = ROOT / "studio" / "seo_packager.py"
sp_text = sp_p.read_text(encoding="utf-8")

old_sp_pat = r'prompt\s*=\s*\(\s*f"Monumental heroic chest-up bust portrait[\s\S]*?no watermark\."\s*\)'
new_sp_prompt = """prompt = (
                f"Monumental heroic classical sculpted marble and bronze statue of a Stoic philosopher god ({char_desc}), "
                "deeply chiseled stone anatomy, massive sculpted bare shoulder and pectoral chest, thick muscular neck, deeply carved curly stone beard, sculpted classical statue eyes, "
                "wearing a vibrant royal crimson red draped toga (chlamys) over one shoulder, warm golden rim lighting outlining sculpted rock muscles, "
                "magnificent illuminated ancient Athens Acropolis and Parthenon on distant rocky hill in deep starry night sky with glowing emerald teal aurora borealis and floating golden embers, "
                "sculpture strictly occupying 50% on the RIGHT half facing towards the left, leaving the entire LEFT 50% open deep twilight atmospheric sky for bold typography, "
                "chest-up low-angle framing, never full body, never standing on distant pedestal, photorealistic 8k render of a monumental classical sculpture, cinematic lighting, no text, no watermark."
            )"""

sp_text, c2 = re.subn(old_sp_pat, new_sp_prompt, sp_text, count=1)
print(f"Updated seo_packager.py stoic fallback: {c2}")

sp_p.write_text(sp_text, encoding="utf-8")
print("ALL PROMPT TEMPLATES UPDATED TO STATUE SCULPTURE!")
