"""Project Deliverable Organizer for Storyboard Studio.

Organizes production outputs from the outside in:
1. Series-level publish folder: `00_XUAT_BAN_TOAN_BO_SERIES/`
2. Episode-level publish folder: `00_DANG_BAI_YOUTUBE/`
3. Clear, descriptive file names ready for 1-click YouTube publishing.
4. Preserves all internal engine files (scenes, plan.json, manifest.json)
   without breaking web preview or resume features.
"""

from __future__ import annotations
import os
import re
import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional


def sanitize_filename(name: str) -> str:
    """Converts a title into a safe, clean Windows filename."""
    if not name:
        return "Video"
    # Replace invalid Windows filename characters: < > : " / \ | ? *
    clean = re.sub(r'[\<\>\:\"\/\\\|\?\*]+', ' - ', name)
    clean = re.sub(r'\s{2,}', ' ', clean).strip(' .-_')
    return clean[:120]


def safe_link_or_copy(src: Path, dst: Path) -> bool:
    """Creates an NTFS hard link (0 extra disk space) or falls back to copy."""
    if not src.is_file():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        try:
            if dst.samefile(src):
                return True
            dst.unlink()
        except Exception:
            pass
    try:
        os.link(src, dst)
        return True
    except Exception:
        try:
            shutil.copy2(src, dst)
            return True
        except Exception:
            return False


def organize_episode(episode_dir: Path | str) -> Dict[str, Any]:
    """Organizes an episode into a clean, publish-ready structure."""
    ep_dir = Path(episode_dir).resolve()
    if not ep_dir.is_dir():
        return {"ok": False, "error": f"Directory not found: {ep_dir}"}

    # 1. Parse publish pack metadata
    pack_json = ep_dir / "youtube_publish_pack.json"
    pack_txt = ep_dir / "youtube_publish_pack.txt"
    metadata = {}
    if pack_json.is_file():
        try:
            metadata = json.loads(pack_json.read_text(encoding="utf-8"))
        except Exception:
            metadata = {}

    series_name = metadata.get("series") or ep_dir.parent.name
    # Extract episode number
    ep_match = re.search(r'episode_(\d+)', ep_dir.name)
    episode_num = int(ep_match.group(1)) if ep_match else int(metadata.get("episode", 1))

    # Determine primary title
    raw_title = metadata.get("primary_title")
    if not raw_title and metadata.get("titles"):
        raw_title = metadata["titles"][0].get("title")
    if not raw_title:
        raw_title = f"{series_name} - Tap {episode_num}"

    clean_title = sanitize_filename(raw_title)

    # 2. Identify source deliverables
    final_video = ep_dir / "episode_final.mp4"
    is_vertical_short = False
    if final_video.is_file():
        try:
            import cv2
            cap = cv2.VideoCapture(str(final_video))
            if cap.isOpened():
                vw = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                vh = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                if vh > vw:
                    is_vertical_short = True
            cap.release()
        except Exception:
            pass

    grounded_pack = str(metadata.get("engine_version", "")).startswith("grounded-seo-")
    if is_vertical_short and (ep_dir / "thumbnail_shorts.jpg").is_file():
        # For vertical Shorts/Reels, the primary thumbnail MUST be the 9:16 vertical cover!
        main_thumbnail = ep_dir / "thumbnail_shorts.jpg"
    elif grounded_pack:
        saved_thumbnail = metadata.get("thumbnail_file")
        main_thumbnail = Path(saved_thumbnail) if saved_thumbnail else ep_dir / "__no_current_thumbnail__"
    else:
        main_thumbnail = ep_dir / "thumbnail_seo.jpg"
        if not main_thumbnail.is_file():
            main_thumbnail = ep_dir / "thumbnail_opt_1.jpg"

    # 3. Create Episode-Level Publish Folder: 00_DANG_BAI_YOUTUBE
    ep_publish_dir = ep_dir / "00_DANG_BAI_YOUTUBE"
    ep_publish_dir.mkdir(parents=True, exist_ok=True)

    results = {
        "episode_publish_dir": str(ep_publish_dir),
        "video": None,
        "thumbnail": None,
        "content_txt": None,
        "alt_thumbnails": []
    }

    # A. Video to publish
    if final_video.is_file():
        pub_video = ep_publish_dir / f"01_VIDEO_DANG_YOUTUBE - {clean_title}.mp4"
        if safe_link_or_copy(final_video, pub_video):
            results["video"] = str(pub_video)

    # B. Main SEO Thumbnail
    if main_thumbnail.is_file():
        pub_thumb = ep_publish_dir / f"02_THUMBNAIL_CHINH_SEO - {clean_title}.jpg"
        if safe_link_or_copy(main_thumbnail, pub_thumb):
            results["thumbnail"] = str(pub_thumb)

    # C. Publish Pack Text (Title, Description, 30 Tags, Chapters, Hashtags)
    guide_path = None
    if pack_txt.is_file():
        pub_txt = ep_publish_dir / f"03_THONG_TIN_DANG_BAI - {clean_title}.txt"
        try:
            shutil.copy2(pack_txt, pub_txt)
            results["content_txt"] = str(pub_txt)
        except Exception:
            pass

        # Standalone YouTube Studio upload guide (separate from metadata content)
        guide_path = None
        try:
            try:
                from studio import seo_packager
            except ImportError:
                import seo_packager
            guide_txt = seo_packager.format_upload_settings_checklist_txt(metadata)
            guide_path = ep_publish_dir / f"05_HUONG_DAN_CAI_DAT_YOUTUBE_STUDIO - {clean_title}.txt"
            guide_path.write_text(guide_txt, encoding="utf-8")
        except Exception:
            pass

    # D. Alternative Thumbnails (for A/B testing)
    alt_dir = ep_publish_dir / "04_CAC_MAU_THUMBNAIL_DU_PHONG"
    alt_mapping = [
        ("thumbnail_opt_1.jpg", "Mau_1_Khuon_Mat_Kich_Tinh.jpg"),
        ("thumbnail_opt_2.jpg", "Mau_2_Tuong_Phan_Anh_Sang.jpg"),
        ("thumbnail_opt_3.jpg", "Mau_3_Dien_Anh_Khac_Ky.jpg"),
        ("thumbnail_opt_4.jpg", "Mau_4_Toi_Gian_Tinh_Te.jpg"),
        ("thumbnail_competitor_trend.jpg", "Tham_Khao_Xu_Huong_Doi_Thu.jpg"),
    ]
    if grounded_pack:
        alt_mapping = []
        # Preserve existing alternatives outside the ready-to-publish folder.
        if alt_dir.is_dir():
            import time
            archived = ep_dir / "_du_lieu_tam" / f"seo_legacy_variants_{time.time_ns()}"
            archived.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(alt_dir), str(archived))
    for src_name, dst_name in alt_mapping:
        src_f = ep_dir / src_name
        if src_f.is_file():
            alt_dst = alt_dir / dst_name
            if safe_link_or_copy(src_f, alt_dst):
                results["alt_thumbnails"].append(str(alt_dst))

    # Note: Automatic YouTube Shorts generation has been completely removed to maximize production speed.

    # 4. Create Series-Level Central Publish Folder: productions/<series>/00_XUAT_BAN_TOAN_BO_SERIES/
    series_dir = ep_dir.parent
    if series_dir.is_dir() and series_dir.name != "productions":
        series_publish_dir = series_dir / "00_XUAT_BAN_TOAN_BO_SERIES"
        series_publish_dir.mkdir(parents=True, exist_ok=True)
        series_ep_dir = series_publish_dir / f"Tap_{episode_num:02d} - {clean_title}"

        # Clean up any stale or obsolete duplicate folder for this episode number
        for old_ep in series_publish_dir.glob(f"Tap_{episode_num:02d} - *"):
            if old_ep.is_dir() and old_ep.resolve() != series_ep_dir.resolve():
                try:
                    if grounded_pack:
                        import time
                        archive = ep_dir / "_du_lieu_tam" / f"seo_previous_series_{time.time_ns()}"
                        archive.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(old_ep), str(archive))
                    else:
                        shutil.rmtree(str(old_ep), ignore_errors=True)
                except Exception:
                    pass

        series_ep_dir.mkdir(parents=True, exist_ok=True)

        if final_video.is_file():
            s_vid = series_ep_dir / f"VIDEO_DANG_Tap_{episode_num:02d} - {clean_title}.mp4"
            safe_link_or_copy(final_video, s_vid)

        if main_thumbnail.is_file():
            s_thumb = series_ep_dir / f"THUMBNAIL_CHINH_Tap_{episode_num:02d} - {clean_title}.jpg"
            safe_link_or_copy(main_thumbnail, s_thumb)

        if grounded_pack and not main_thumbnail.is_file():
            stale_thumbs = list(series_ep_dir.glob("THUMBNAIL_CHINH_Tap_*.jpg"))
            if stale_thumbs:
                import time
                archive = ep_dir / "_du_lieu_tam" / f"seo_previous_series_thumbnails_{time.time_ns()}"
                archive.mkdir(parents=True, exist_ok=True)
                for stale_thumb in stale_thumbs:
                    shutil.move(str(stale_thumb), str(archive / stale_thumb.name))

        if pack_txt.is_file():
            s_txt = series_ep_dir / f"THONG_TIN_DANG_BAI_Tap_{episode_num:02d}.txt"
            shutil.copy2(pack_txt, s_txt)

        if guide_path and Path(guide_path).is_file():
            s_guide = series_ep_dir / f"HUONG_DAN_CAI_DAT_YOUTUBE_STUDIO_Tap_{episode_num:02d}.txt"
            shutil.copy2(guide_path, s_guide)

        results["series_publish_dir"] = str(series_ep_dir)

    # 5. Clean up redundant temporary raw concat video if final video is verified
    raw_concat = ep_dir / "episode_raw_concat.mp4"
    if final_video.is_file() and raw_concat.is_file() and final_video.stat().st_size > 1024 * 1024:
        # Move raw concat to temporary cache folder to avoid confusion and declutter root
        temp_dir = ep_dir / "_du_lieu_tam"
        temp_dir.mkdir(parents=True, exist_ok=True)
        try:
            target_raw = temp_dir / "episode_raw_concat.mp4"
            if not target_raw.exists():
                shutil.move(str(raw_concat), str(target_raw))
        except Exception:
            pass

    concat_list = ep_dir / "concat_list.txt"
    if concat_list.is_file():
        temp_dir = ep_dir / "_du_lieu_tam"
        temp_dir.mkdir(parents=True, exist_ok=True)
        try:
            target_list = temp_dir / "concat_list.txt"
            if not target_list.exists():
                shutil.move(str(concat_list), str(target_list))
        except Exception:
            pass

    if grounded_pack:
        keep = {str(Path(v).resolve()) for key, v in results.items() if key in ("video", "thumbnail", "content_txt") and v}
        stale = [f for f in ep_publish_dir.iterdir() if f.is_file() and f.name.startswith(("01_VIDEO_DANG_YOUTUBE", "02_THUMBNAIL_CHINH_SEO", "03_THONG_TIN_DANG_BAI")) and str(f.resolve()) not in keep]
        if stale:
            import time
            archived = ep_dir / "_du_lieu_tam" / f"seo_previous_publish_{time.time_ns()}"
            archived.mkdir(parents=True, exist_ok=True)
            for file in stale:
                shutil.move(str(file), str(archived / file.name))
    return {"ok": True, "details": results}


def organize_series(series_dir: Path | str) -> Dict[str, Any]:
    """Organizes all completed episodes in a series."""
    s_dir = Path(series_dir).resolve()
    episodes = sorted([p for p in s_dir.iterdir() if p.is_dir() and re.match(r'episode_\d+', p.name)])
    organized = []
    for ep in episodes:
        if (ep / "episode_final.mp4").is_file():
            res = organize_episode(ep)
            organized.append({"episode": ep.name, "result": res})
    return {"ok": True, "series": s_dir.name, "episodes": organized}


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "D:/STORYBOARD_AI/studio/productions/stoi"
    p = Path(target)
    if "episode_" in p.name:
        print(json.dumps(organize_episode(p), indent=2, ensure_ascii=False))
    else:
        print(json.dumps(organize_series(p), indent=2, ensure_ascii=False))
