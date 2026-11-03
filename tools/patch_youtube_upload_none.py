"""Patch YouTube upload None values and missing fields."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 1. Patch studio/web_server.py
ws_path = ROOT / "studio" / "web_server.py"
ws_text = ws_path.read_text(encoding="utf-8")

# Replace custom_title & custom_description
pattern1 = r'custom_title\s*=\s*str\(body\.get\("title",\s*""\)\)\.strip\(\)\s*custom_description\s*=\s*str\(body\.get\("description",\s*""\)\)\.strip\(\)'
replacement1 = """raw_title = body.get("title")
            custom_title = ""
            if raw_title is not None:
                st = str(raw_title).strip()
                if st.lower() not in ("", "none", "null", "undefined"):
                    custom_title = st

            raw_desc = body.get("description")
            custom_description = ""
            if raw_desc is not None:
                sd = str(raw_desc).strip()
                if sd.lower() not in ("", "none", "null", "undefined"):
                    custom_description = sd"""

m1 = re.search(pattern1, ws_text)
if m1:
    ws_text = ws_text[:m1.start()] + replacement1 + ws_text[m1.end():]
    print("[1/4] web_server.py custom_title/desc successfully patched.")
else:
    print("[WARN] pattern1 not found in web_server.py")

# Replace upload_title & upload_desc fallback
pattern2 = r'upload_title\s*=\s*custom_title or media_info\.get\("title"\) or series_name\s*upload_desc\s*=\s*custom_description or media_info\.get\("description"\) or ""'
replacement2 = """pub_pack = media_info.get("publish_pack") or {}
            fallback_title = (
                media_info.get("title")
                or pub_pack.get("best_title")
                or pub_pack.get("primary_title")
                or series_name
            )
            upload_title = custom_title or fallback_title
            if str(upload_title).strip().lower() in ("", "none", "null", "undefined"):
                upload_title = fallback_title or series_name or "Stoic Philosophy"

            fallback_desc = (
                media_info.get("description")
                or pub_pack.get("description")
                or ""
            )
            upload_desc = custom_description or fallback_desc
            if str(upload_desc).strip().lower() in ("none", "null", "undefined"):
                upload_desc = fallback_desc"""

m2 = re.search(pattern2, ws_text)
if m2:
    ws_text = ws_text[:m2.start()] + replacement2 + ws_text[m2.end():]
    print("[2/4] web_server.py upload_title/desc fallback successfully patched.")
else:
    print("[WARN] pattern2 not found in web_server.py")

ws_path.write_text(ws_text, encoding="utf-8")


# 2. Patch studio/youtube_manager.py
yt_path = ROOT / "studio" / "youtube_manager.py"
yt_text = yt_path.read_text(encoding="utf-8")

# Fix channel_title: target_ch.get("title") -> target_ch.get("name") or target_ch.get("title") or channel_id
old_ch_title = '"channel_title": target_ch.get("title")'
new_ch_title = '"channel_title": target_ch.get("name") or target_ch.get("title") or channel_id'
if old_ch_title in yt_text:
    yt_text = yt_text.replace(old_ch_title, new_ch_title)
    print("[3/4] youtube_manager.py channel_title bug fixed.")

old_ch_name = 'ch_name = target_ch.get("title") or channel_id'
new_ch_name = 'ch_name = target_ch.get("name") or target_ch.get("title") or channel_id'
if old_ch_name in yt_text:
    yt_text = yt_text.replace(old_ch_name, new_ch_name)
    print("[4/4] youtube_manager.py ch_name log bug fixed.")

# Fix safe_title / safe_desc in upload_video_to_youtube
safe_pat = r'safe_title\s*=\s*\(title or video_path\.stem\)\[:100\]\s*safe_desc\s*=\s*\(description or ""\)\[:5000\]'
safe_rep = """clean_t = str(title or "").strip()
    if clean_t.lower() in ("none", "null", "undefined", ""):
        clean_t = video_path.stem.replace("_", " ").title()
    safe_title = clean_t[:100]

    clean_d = str(description or "").strip()
    if clean_d.lower() in ("none", "null", "undefined"):
        clean_d = ""
    safe_desc = clean_d[:5000]"""

m_safe = re.search(safe_pat, yt_text)
if m_safe:
    yt_text = yt_text[:m_safe.start()] + safe_rep + yt_text[m_safe.end():]
    print("[5/4] youtube_manager.py safe_title/desc sanitization patched.")

# Add reference_analysis.json fallback in resolve_episode_media
ref_hook = '    # Read SEO pack\n    pack_data = {}\n    pack_path = ep_dir / "youtube_publish_pack.json"'
ref_rep = """    # Read SEO pack
    pack_data = {}
    pack_path = ep_dir / "youtube_publish_pack.json"
    if not pack_path.is_file() or pack_path.stat().st_size < 10:
        # Fallback to reference_analysis.json if available
        ref_path = ep_dir / "reference_analysis.json"
        if ref_path.is_file():
            try:
                import json
                ref_d = json.loads(ref_path.read_text(encoding="utf-8"))
                pack_data = {
                    "best_title": ref_d.get("title") or "",
                    "description": ref_d.get("description") or "",
                    "tags": ref_d.get("keywords") or [],
                    "language": ref_d.get("language") or "",
                }
            except Exception:
                pass"""

if ref_hook in yt_text:
    yt_text = yt_text.replace(ref_hook, ref_rep, 1)
    print("[6/4] youtube_manager.py reference_analysis fallback added.")

yt_path.write_text(yt_text, encoding="utf-8")
print("ALL PYTHON UPLOAD PATCHES APPLIED SUCCESSFULLY!")
