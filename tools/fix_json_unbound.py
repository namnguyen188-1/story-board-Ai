from pathlib import Path
p = Path("studio/youtube_manager.py")
txt = p.read_text(encoding="utf-8")

old_snippet = """    # Read SEO pack
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
                pass
    if pack_path.is_file():
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

new_snippet = """    # Read SEO pack
    import json
    pack_data = {}
    pack_path = ep_dir / "youtube_publish_pack.json"
    if pack_path.is_file() and pack_path.stat().st_size >= 10:
        try:
            pack_data = json.loads(pack_path.read_text(encoding="utf-8"))
        except Exception as _p_err:
            logger.warning(f"Error parsing youtube_publish_pack.json: {_p_err}")
            pack_data = {}

    if not pack_data or not pack_data.get("best_title") or not pack_data.get("description"):
        # Fallback to reference_analysis.json if available
        ref_path = ep_dir / "reference_analysis.json"
        if ref_path.is_file():
            try:
                ref_d = json.loads(ref_path.read_text(encoding="utf-8"))
                if not pack_data.get("best_title") and ref_d.get("title"):
                    pack_data["best_title"] = ref_d.get("title")
                if not pack_data.get("description") and ref_d.get("description"):
                    pack_data["description"] = ref_d.get("description")
                if not pack_data.get("tags") and ref_d.get("keywords"):
                    pack_data["tags"] = ref_d.get("keywords")
                if not pack_data.get("language") and ref_d.get("language"):
                    pack_data["language"] = ref_d.get("language")
            except Exception:
                pass"""

assert old_snippet in txt, "old_snippet not found in youtube_manager.py"
p.write_text(txt.replace(old_snippet, new_snippet, 1), encoding="utf-8")
print("Fixed UnboundLocalError json in youtube_manager.py!")
