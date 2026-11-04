import re
from pathlib import Path

def patch():
    p = Path("studio/youtube_manager.py")
    content = p.read_text(encoding="utf-8")
    content_norm = content.replace("\r\n", "\n")

    target1 = """    # Strict YouTube hashtag enforcement: YouTube reads hashtags directly from description!
    # If description lacks hashtags, extract from tags list or synthesize
    if "#" not in clean_d and tags:
        synthesized_hashes = []
        for t in tags:
            clean_tag = re.sub(r'[^a-zA-Z0-9_\\u00C0-\\u1EF9]', '', str(t)).strip()
            if len(clean_tag) >= 3 and f"#{clean_tag.lower()}" not in [h.lower() for h in synthesized_hashes]:
                synthesized_hashes.append(f"#{clean_tag}")
            if len(synthesized_hashes) >= 5:
                break
        if synthesized_hashes:
            clean_d = f"{clean_d}\\n\\n{' '.join(synthesized_hashes)}".strip()"""

    replacement1 = """    # Strict YouTube hashtag enforcement: YouTube reads hashtags directly from description!
    # If description lacks hashtags or has fewer than 3, extract from tags list or synthesize
    existing_hashes = re.findall(r'#[a-zA-Z0-9_\\u00C0-\\u1EF9]+', clean_d)
    if len(existing_hashes) < 3 and tags:
        synthesized_hashes = list(existing_hashes)
        for t in tags:
            clean_tag = re.sub(r'[^a-zA-Z0-9_\\u00C0-\\u1EF9]', '', str(t)).strip()
            if len(clean_tag) >= 3 and f"#{clean_tag.lower()}" not in [h.lower() for h in synthesized_hashes]:
                synthesized_hashes.append(f"#{clean_tag}")
            if len(synthesized_hashes) >= 5:
                break
        new_hashes = [h for h in synthesized_hashes if h.lower() not in [eh.lower() for eh in existing_hashes]]
        if new_hashes:
            clean_d = f"{clean_d}\\n\\n{' '.join(new_hashes)}".strip()"""

    target2 = """        if shorts_pack:
            return {
                "video_path": video_path,
                "thumbnail_path": None,  # Shorts use frame extraction on YouTube
                "title": shorts_pack.get("best_title") or f"{ep_dir.parent.name} #shorts",
                "description": shorts_pack.get("description", ""),
                "tags": shorts_pack.get("tags", ["shorts", "youtube shorts"]),
                "vidiq_score": 100,
                "language": pack_data.get("language", ""),
                "pinned_comment": shorts_pack.get("pinned_comment", ""),
                "is_short": True
            }"""

    replacement2 = """        if shorts_pack:
            # Guarantee hashtags are embedded in Shorts description
            s_desc = shorts_pack.get("description", "")
            s_hashes = shorts_pack.get("hashtags") or pack_data.get("hashtags") or []
            if s_hashes:
                h_str = " ".join([h if h.startswith("#") else f"#{h}" for h in s_hashes if h])
                if h_str and h_str not in s_desc:
                    s_desc = f"{s_desc}\\n\\n{h_str}".strip()
            return {
                "video_path": video_path,
                "thumbnail_path": None,  # Shorts use frame extraction on YouTube
                "title": shorts_pack.get("best_title") or f"{ep_dir.parent.name} #shorts",
                "description": s_desc,
                "tags": shorts_pack.get("tags", ["shorts", "youtube shorts"]),
                "vidiq_score": 100,
                "language": pack_data.get("language", ""),
                "pinned_comment": shorts_pack.get("pinned_comment", ""),
                "publish_pack": shorts_pack,
                "is_short": True
            }"""

    assert target1 in content_norm, "target1 not found in youtube_manager.py"
    assert target2 in content_norm, "target2 not found in youtube_manager.py"

    content_norm = content_norm.replace(target1, replacement1)
    content_norm = content_norm.replace(target2, replacement2)

    p.write_text(content_norm.replace("\n", "\r\n"), encoding="utf-8")
    print("SUCCESS: studio/youtube_manager.py patched cleanly")

    # Also patch web_server.py
    wp = Path("studio/web_server.py")
    w_content = wp.read_text(encoding="utf-8")
    w_norm = w_content.replace("\r\n", "\n")

    w_target = """            # Critical Hashtag Guarantee: Ensure all 5 hashtags are attached at bottom of upload_desc
            pub_hashes = pub_pack.get("hashtags") or []
            if pub_hashes:
                hash_line = " ".join([h if h.startswith("#") else f"#{h}" for h in pub_hashes if h])
                if hash_line and hash_line not in upload_desc:
                    upload_desc = upload_desc.strip() + "\\n\\n" + hash_line"""

    w_replacement = """            # Critical Hashtag Guarantee: Ensure at least 3-5 hashtags are attached at bottom of upload_desc
            pub_hashes = pub_pack.get("hashtags") or []
            existing_h = re.findall(r'#[a-zA-Z0-9_\\u00C0-\\u1EF9]+', upload_desc)
            if len(existing_h) < 3:
                candidates_h = list(pub_hashes)
                if not candidates_h and upload_tags:
                    for t in upload_tags:
                        ct = re.sub(r'[^a-zA-Z0-9_\\u00C0-\\u1EF9]', '', str(t)).strip()
                        if len(ct) >= 3 and f"#{ct.lower()}" not in [x.lower() for x in candidates_h]:
                            candidates_h.append(f"#{ct}")
                        if len(candidates_h) >= 5:
                            break
                if candidates_h:
                    hash_line = " ".join([h if h.startswith("#") else f"#{h}" for h in candidates_h if h])
                    if hash_line and hash_line not in upload_desc:
                        upload_desc = upload_desc.strip() + "\\n\\n" + hash_line"""

    assert w_target in w_norm, "w_target not found in web_server.py"
    w_norm = w_norm.replace(w_target, w_replacement)
    wp.write_text(w_norm.replace("\n", "\r\n"), encoding="utf-8")
    print("SUCCESS: studio/web_server.py patched cleanly")

if __name__ == "__main__":
    patch()
