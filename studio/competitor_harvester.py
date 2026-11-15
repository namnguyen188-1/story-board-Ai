"""Competitor Channel Harvester - Quét và quản lý danh sách video đối thủ chống trùng lặp.
Cung cấp API nhanh gọn (3-5s), không tải video, lưu trữ theo kênh, kiểm tra trạng thái sản xuất.
"""

import os
import re
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

STUDIO_DIR = Path(__file__).resolve().parent
COMPETITORS_DIR = STUDIO_DIR / "competitors"
CHARACTER_CLONES_DIR = STUDIO_DIR / "character_clones"
PRODUCTIONS_DIR = STUDIO_DIR / "productions"
QUEUE_FILE = STUDIO_DIR / "queue.json"


def _format_duration(seconds: Optional[int]) -> str:
    if not seconds:
        return "--:--"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def _format_views(views: Optional[int]) -> str:
    if views is None:
        return "--"
    if views >= 1_000_000:
        return f"{views / 1_000_000:.1f}M"
    if views >= 1_000:
        return f"{views / 1_000:.1f}K"
    return str(views)


def _get_processed_video_ids() -> Dict[str, str]:
    """Trả về từ điển {video_id: ghi_chú_sản_xuất} để kiểm tra trùng lặp."""
    processed = {}

    # 1. Kiểm tra character_clones (nơi lưu storyboard và frames bóc tách từ video gốc)
    if CHARACTER_CLONES_DIR.exists():
        for name in os.listdir(CHARACTER_CLONES_DIR):
            m = re.match(r"^([a-zA-Z0-9_-]{11})_", name)
            if m:
                vid = m.group(1)
                if vid not in processed:
                    processed[vid] = "Đã clone kịch bản / nhân vật"

    # 2. Kiểm tra queue.json
    if QUEUE_FILE.exists():
        try:
            with open(QUEUE_FILE, "r", encoding="utf-8") as qf:
                qdata = json.load(qf)
                items = qdata if isinstance(qdata, list) else qdata.get("items", [])
                for item in items:
                    ref = str(item.get("prompt", "")) + " " + str(item.get("reference_url", ""))
                    for word in ref.split():
                        m = re.search(r"(?:v=|\/)([a-zA-Z0-9_-]{11})", word)
                        if m:
                            q_vid = m.group(1)
                            st = item.get("status", "Chờ chạy")
                            processed[q_vid] = f"Hàng chờ ({st})"
        except Exception:
            pass

    # 3. Kiểm tra productions
    if PRODUCTIONS_DIR.exists():
        for meta_path in PRODUCTIONS_DIR.glob("**/metadata.json"):
            try:
                with open(meta_path, "r", encoding="utf-8") as mf:
                    mdata = json.load(mf)
                    ref = str(mdata.get("reference_url", "")) + " " + str(mdata.get("prompt", ""))
                    m = re.search(r"(?:v=|\/)([a-zA-Z0-9_-]{11})", ref)
                    if m:
                        vid = m.group(1)
                        ep = meta_path.parent.name
                        ser = meta_path.parent.parent.name
                        processed[vid] = f"Đã xuất bản ({ser} - {ep})"
            except Exception:
                pass

    return processed


def normalize_channel_url(input_str: str, tab: str = "videos") -> str:
    """Chuẩn hóa mọi dạng link kênh về link tab chuẩn."""
    s = input_str.strip()
    if not s:
        return ""
    if s.startswith("@"):
        return f"https://www.youtube.com/{s}/{tab}"
    if not s.startswith("http"):
        s = "https://" + s
    # Nếu là link video đơn lẻ
    if "watch?v=" in s or "youtu.be/" in s:
        return s
    # Xóa dấu gạch chéo cuối
    s = s.rstrip("/")
    if not any(s.endswith(t) for t in ["/videos", "/shorts", "/playlists", "/featured", "/streams"]):
        s = f"{s}/{tab}"
    return s


def scan_channel(
    channel_input: str,
    limit: int = 150,
    tab: str = "videos",
    sort_by: str = "default"  # 'default', 'views_desc', 'duration_desc'
) -> Dict[str, Any]:
    """Quét toàn bộ video từ kênh đối thủ siêu tốc bằng yt-dlp flat playlist."""
    import yt_dlp

    COMPETITORS_DIR.mkdir(parents=True, exist_ok=True)
    target_url = normalize_channel_url(channel_input, tab=tab)

    ydl_opts = {
        "extract_flat": True,
        "quiet": True,
        "no_warnings": True,
        "playlistend": limit,
        "skip_download": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            data = ydl.extract_info(target_url, download=False)
    except Exception as e:
        return {
            "success": False,
            "error": f"Lỗi khi quét kênh: {str(e)}",
            "videos": [],
            "total": 0
        }

    channel_title = data.get("channel") or data.get("uploader") or data.get("title") or "Kênh Đối Thủ"
    channel_id = data.get("channel_id") or data.get("uploader_id") or "channel_unknown"
    channel_url = data.get("channel_url") or data.get("uploader_url") or target_url

    raw_entries = data.get("entries", [])
    processed_map = _get_processed_video_ids()

    videos = []
    for idx, e in enumerate(raw_entries, 1):
        if not e:
            continue
        vid = e.get("id") or ""
        if not vid or len(vid) != 11:
            # Có thể url là link
            u = e.get("url") or ""
            m = re.search(r"(?:v=|\/)([a-zA-Z0-9_-]{11})", u)
            if m:
                vid = m.group(1)
        if not vid:
            continue

        url = f"https://www.youtube.com/watch?v={vid}"
        title = e.get("title") or "Không có tiêu đề"
        dur = e.get("duration")
        views = e.get("view_count")
        thumb = e.get("thumbnail") or f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"

        # Tình trạng
        status_note = processed_map.get(vid)
        is_processed = bool(status_note)

        videos.append({
            "idx": idx,
            "id": vid,
            "url": url,
            "title": title,
            "duration": dur,
            "duration_str": _format_duration(dur),
            "views": views,
            "views_str": _format_views(views),
            "thumbnail": thumb,
            "is_processed": is_processed,
            "status_note": status_note or "Chưa làm"
        })

    # Sắp xếp nếu có yêu cầu
    if sort_by == "views_desc":
        videos.sort(key=lambda x: x.get("views") or 0, reverse=True)
    elif sort_by == "duration_desc":
        videos.sort(key=lambda x: x.get("duration") or 0, reverse=True)

    # Đánh lại chỉ số idx sau khi sắp xếp
    for i, v in enumerate(videos, 1):
        v["idx"] = i

    result = {
        "success": True,
        "channel_title": channel_title,
        "channel_id": channel_id,
        "channel_url": channel_url,
        "total": len(videos),
        "processed_count": sum(1 for v in videos if v["is_processed"]),
        "unprocessed_count": sum(1 for v in videos if not v["is_processed"]),
        "scanned_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "videos": videos
    }

    # Lưu kết quả vào tệp json của kênh
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", channel_title)[:50]
    out_file = COMPETITORS_DIR / f"{safe_name}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # Cập nhật index danh sách kênh đã lưu
    _update_competitor_index(safe_name, channel_title, channel_url, len(videos), result["processed_count"])

    return result


def _update_competitor_index(file_key: str, title: str, url: str, total: int, processed: int):
    index_file = COMPETITORS_DIR / "channels_index.json"
    idx_data = {}
    if index_file.exists():
        try:
            with open(index_file, "r", encoding="utf-8") as f:
                idx_data = json.load(f)
        except Exception:
            idx_data = {}

    idx_data[file_key] = {
        "title": title,
        "url": url,
        "total_videos": total,
        "processed_videos": processed,
        "file_path": str(COMPETITORS_DIR / f"{file_key}.json"),
        "last_scanned": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(idx_data, f, ensure_ascii=False, indent=2)


def list_saved_channels() -> List[Dict[str, Any]]:
    """Liệt kê danh sách các kênh đối thủ đã từng quét."""
    index_file = COMPETITORS_DIR / "channels_index.json"
    if not index_file.exists():
        return []
    try:
        with open(index_file, "r", encoding="utf-8") as f:
            idx_data = json.load(f)
        return [{"key": k, **v} for k, v in idx_data.items()]
    except Exception:
        return []


def load_channel_videos(file_key: str) -> Optional[Dict[str, Any]]:
    """Tải lại danh sách video đã lưu và cập nhật trạng thái mới nhất."""
    file_path = COMPETITORS_DIR / f"{file_key}.json"
    if not file_path.exists():
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Cập nhật trạng thái trùng lặp theo thời gian thực
        processed_map = _get_processed_video_ids()
        for v in data.get("videos", []):
            vid = v.get("id")
            if vid in processed_map:
                v["is_processed"] = True
                v["status_note"] = processed_map[vid]
            else:
                v["is_processed"] = False
                v["status_note"] = "Chưa làm"

        data["processed_count"] = sum(1 for v in data["videos"] if v["is_processed"])
        data["unprocessed_count"] = sum(1 for v in data["videos"] if not v["is_processed"])
        return data
    except Exception:
        return None


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Competitor Channel Harvester")
    parser.add_argument("--channel", required=True, help="Link kênh hoặc @handle")
    parser.add_argument("--limit", type=int, default=50, help="Số video tối đa cần quét")
    parser.add_argument("--sort", choices=["default", "views_desc", "duration_desc"], default="views_desc")
    args = parser.parse_args()

    print(f"[*] Đang quét kênh: {args.channel} (limit={args.limit}, sort={args.sort})...")
    res = scan_channel(args.channel, limit=args.limit, sort_by=args.sort)
    if res.get("success"):
        print(f"[+] Quét thành công kênh: {res['channel_title']}")
        print(f"[+] Tổng số video: {res['total']} (Đã làm: {res['processed_count']}, Chưa làm: {res['unprocessed_count']})")
        for v in res["videos"][:10]:
            tag = "✅ " + v['status_note'] if v['is_processed'] else "🆕 Chưa làm"
            print(f"  {v['idx']}. [{v['id']}] {v['title'][:45]}... | {v['duration_str']} | {v['views_str']} views | {tag}")
    else:
        print(f"[-] Thất bại: {res.get('error')}")
