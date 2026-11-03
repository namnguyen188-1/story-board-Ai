from pathlib import Path
p = Path("studio/youtube_manager.py")
txt = p.read_text(encoding="utf-8")
old = """    if pack_path.is_file():
        try:
            pack_data = json.loads(pack_path.read_text(encoding="utf-8"))
        except Exception:
            pass"""
new = """    if pack_path.is_file():
        try:
            raw_txt = pack_path.read_text(encoding="utf-8")
            print("[DEBUG_RESOLVE] pack_path exists, size:", len(raw_txt))
            pack_data = json.loads(raw_txt)
            print("[DEBUG_RESOLVE] pack_data keys count:", len(pack_data))
        except Exception as _e:
            print("[DEBUG_RESOLVE_ERR]", _e)
            pass
    else:
        print("[DEBUG_RESOLVE] pack_path NOT is_file:", pack_path)"""
assert old in txt, "old not found"
p.write_text(txt.replace(old, new, 1), encoding="utf-8")
print("Added debug prints to youtube_manager.py")
