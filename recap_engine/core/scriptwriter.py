"""
Movie Recap Scriptwriter Engine powered by Google Gemini.
Generates high-retention 3-act movie recap scripts with character aliases and pacing timestamps.
"""

import json
import re
import time
import concurrent.futures
from typing import Dict, Any, List, Optional
from pathlib import Path
try:
    from ..config import load_config, KeyRotator, save_config, get_shared_rotator
except (ImportError, ValueError):
    from config import load_config, KeyRotator, save_config, get_shared_rotator


SYSTEM_PROMPT = """Bạn là biên kịch trưởng chuyên nghiệp của các kênh Review Phim triệu view (như Phim Hay, Cuồng Phim, Spoil Phim).
Nhiệm vụ của bạn là viết kịch bản review phim cực kỳ cuốn hút, nghẹt thở, giữ chân người xem từ giây đầu tiên đến giây cuối cùng theo công thức 3 hồi kinh điển.

QUY TẮC CỐT TỬ - KHỚP 100% VỚI HÀNH ĐỘNG THỰC TẾ TRONG VIDEO (CHỐNG NÓI ĐIÊU):
1. TUYỆT ĐỐI KHÔNG ĐƯỢC BỊA ĐẶT CỐT TRUYỆN NGOÀI LỀ!
   - Nếu video là cảnh rượt đuổi bắn nhau trên sa mạc thì toàn bộ lời bình phải mô tả nghẹt thở cuộc rượt đuổi, trốn chạy và chiến đấu.
   - Tuyệt đối không được nói 'đang tận hưởng bình yên', 'đi dạo', hoặc kể chuyện thần thoại/cổ tích không có trên màn hình.
2. MỖI PHÂN ĐOẠN (SEGMENT) BẮT BUỘC PHẢI MÔ TẢ ĐÚNG HÀNH ĐỘNG CỦA CẢNH ĐÓ VÀ GÁN CHÍNH XÁC `source_time` (mốc thời gian tính bằng giây trong video gốc):
   - Khi màn hình ở mốc thời gian đó là cảnh rượt đuổi xe bay ➔ Lời bình phải mô tả cuộc rượt đuổi xe bay.
   - Khi màn hình là cảnh nằm ngắm súng bắn tỉa ➔ Lời bình phải mô tả phát đạn phục kích định mệnh.
   - Khi quái thú khổng lồ hoặc đoàn xe bọc thép xuất hiện ➔ Lời bình phải mô tả sự đe dọa khổng lồ đó.
   - Trường `source_time`: BẮT BUỘC có (ví dụ: 10.5, 45.0, 95.0, 160.0...). Hệ thống dựng sẽ cắt clip video gốc bắt đầu đúng giây `source_time` này để khớp từng cử chỉ hành động với lời nói!
3. HOOK 3 GIÂY ĐẦU: Luôn mở đầu bằng câu giật gân, khơi gợi tò mò cực đại bám sát cảnh mở màn thực tế (Ví dụ: "Đừng bao giờ dại dột chọc giận gã thợ săn sa mạc này nếu không muốn bỏ mạng...", "Người đàn ông này vừa ôm khối báu vật thì bị cả một binh đoàn bọc thép truy sát...").
4. ĐỔI TÊN NHÂN VẬT THÀNH BIỆT DANH (ALIAS): Dùng danh xưng thân thuộc, hóm hỉnh, cuốn hút (anh Mũ Rộng, gã Thợ Săn, Trợ Lý Lùn, Tên Chỉ Huy, Binh Đoàn Bọc Thép,...).
5. ĐỊNH DẠNG TỪNG CÂU ĐỌC (SEGMENT):
   - Mỗi câu thoại chỉ dài 12 - 25 từ (đọc trong khoảng 3.0s - 4.5s) để khớp hoàn hảo với nhịp cắt video nhanh chống Content-ID.
   - Gán `scene_mood`: "action" (hành động), "suspense" (hồi hộp), "drama" (kịch tính), "climax" (cao trào), "twist" (bất ngờ).

BẠN BẮT BUỘC PHẢI TRẢ VỀ DỮ LIỆU ĐỊNH DẠNG JSON DUY NHẤT (không bọc trong markdown hoặc giải thích thêm):
{
  "title": "Tiêu đề review giật gân",
  "hook": "Câu mở đầu 3s",
  "character_aliases": {"Tên gốc": "Biệt danh"},
  "segments": [
    {
      "id": 1,
      "act": "hook",
      "text": "Đừng bao giờ dại dột chọc giận kẻ mang biệt danh Anh Mũ Rộng nếu không muốn bỏ mạng nơi sa mạc.",
      "scene_mood": "suspense",
      "source_time": 10.5,
      "film_pos_pct": 0.02
    }
  ]
}
"""


def extract_json_from_text(text: str) -> dict:
    """Robust JSON extractor from LLM response text."""
    text = text.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if m:
        text = m.group(1).strip()
    idx_start = text.find("{")
    idx_end = text.rfind("}")
    if idx_start != -1 and idx_end != -1:
        text = text[idx_start:idx_end+1]
    return json.loads(text)


class RecapScriptwriter:
    """Manages recap script generation using Gemini API with key rotation."""

    def __init__(self):
        self.config = load_config()
        self.keys = self.config.get("gemini_keys", [])
        if not self.keys:
            raise ValueError("Chưa có Gemini API Key nào trong recap_config.json!")
        self.rotator = get_shared_rotator()
        self.preferred_model = self.config.get("model_name", "gemini-3.5-flash")
        self.fallback_models = self.config.get("fallback_models", ["gemini-3.8-flash", "gemini-flash-latest"])

    def generate_recap_script(
        self,
        movie_title: str,
        genre: str = "Hành động, Kịch tính",
        target_minutes: int = 5,
        plot_context: str = "",
        user_aliases: Optional[Dict[str, str]] = None,
        style: str = "Kịch tính, gay cấn",
        source_duration: float = 0.0
    ) -> Dict[str, Any]:
        """
        Generates a complete 3-act movie recap script structured as timed segments.
        Calculates ~12-15 segments per minute of video.
        """
        # Smart scaling of segment counts from Short (1-10p) to Feature Length (30p, 1h, 2h)
        if target_minutes <= 15:
            total_segments = max(15, int(target_minutes * 12))
            pacing_note = f"Thời lượng recap ngắn {target_minutes} phút (Nhịp cắt nhanh, mỗi câu 12-25 từ, khoảng {total_segments} phân đoạn)."
        elif target_minutes <= 60:
            hrs = f"{target_minutes/60:.1f} giờ" if target_minutes >= 60 else f"{target_minutes} phút"
            total_segments = min(160, max(50, int(target_minutes * 3.2)))
            pacing_note = f"Thời lượng review dài {target_minutes} phút (~{hrs} - Bản chi tiết đầy đủ 5 Hồi kinh điển, dẫn dắt mạch lạc từng diễn biến cốt truyện, khoảng {total_segments} phân đoạn kể chuyện có chiều sâu)."
        else:
            hrs = f"{target_minutes/60:.1f} giờ"
            total_segments = min(220, max(120, int(target_minutes * 2.2)))
            pacing_note = f"Thời lượng review siêu phẩm {target_minutes} phút (~{hrs} - Trọn bộ phim điện ảnh), bao quát toàn bộ câu chuyện, các tuyến nhân vật, biến cố và cú twist cao trào kết thúc mãn nhãn, khoảng {total_segments} phân đoạn."

        alias_instruction = ""
        if user_aliases:
            alias_list = ", ".join([f"{k} -> {v}" for k, v in user_aliases.items()])
            alias_instruction = f"\nBẮT BUỘC SỬ DỤNG CÁC BIỆT DANH SAU CHO NHÂN VẬT: {alias_list}\n"

        prompt = f"""Hãy viết kịch bản review phim chi tiết và khớp 100% với video:
- TÊN PHIM: {movie_title}
- THỂ LOẠI: {genre}
- PHONG CÁCH: {style}
- THỜI LƯỢNG MONG MUỐN: {pacing_note}
{alias_instruction}
- DỮ LIỆU CẢNH QUAY THỰC TẾ & CỐT TRUYỆN:
{plot_context if plot_context else "Hãy sử dụng kiến thức chuẩn xác của bạn về cốt truyện phim này để viết một bản tóm tắt hấp dẫn nhất."}

YÊU CẦU CỐT TỬ:
- Dựa vào diễn biến thực tế của từng cảnh quay ở trên, mỗi segment BẮT BUỘC PHẢI mô tả đúng hành động, sự kiện của cảnh quay đó (truy đuổi, bắn súng, phục kích, chạy trốn...). Tuyệt đối không nói chuyện ngoài lề!
- Gán chính xác `source_time` (số giây trong video gốc) cho từng segment để hệ thống cắt đúng cảnh khớp với lời bình.
- Hãy xuất đúng định dạng JSON như đã quy định, đủ {total_segments} segments từ mở đầu đến kết thúc trọn vẹn của bộ phim.
"""

        models_to_try = [self.preferred_model] + [m for m in self.fallback_models if m != self.preferred_model]
        model_idx = 0
        max_attempts = len(self.keys) * len(models_to_try)
        attempt = 0

        last_error = None
        while attempt < max_attempts:
            client = self.rotator.get_client(timeout_sec=35.0)
            current_model = models_to_try[model_idx % len(models_to_try)]
            print(f"🔄 Scriptwriter attempt {attempt+1}/{max_attempts} with model '{current_model}' and key index {self.rotator.index}...", flush=True)
            try:
                full_prompt = f"{SYSTEM_PROMPT}\n\n{prompt}"
                resp = client.models.generate_content(
                    model=current_model,
                    contents=full_prompt
                )
                print(f"✅ Gemini response received from {current_model}", flush=True)
                raw_text = resp.text.strip()
                data = extract_json_from_text(raw_text)
                if "segments" in data and len(data["segments"]) > 0:
                    # Enrich segments with calculated durations
                    for idx, seg in enumerate(data["segments"]):
                        seg["id"] = idx + 1
                        word_count = len(seg.get("text", "").split())
                        est_sec = max(2.5, round(word_count / 3.0, 1))
                        seg["est_duration"] = est_sec

                        # Preserve or calculate exact source scene timestamp
                        src_time = seg.get("source_time_sec", seg.get("source_time"))
                        if src_time is not None:
                            try:
                                seg["source_time"] = round(float(src_time), 1)
                            except Exception:
                                pass
                        elif source_duration > 0:
                            pos_pct = float(seg.get("film_pos_pct", idx / max(1, len(data["segments"]))))
                            seg["source_time"] = round(source_duration * pos_pct, 1)

                    data["total_est_seconds"] = round(sum(s["est_duration"] for s in data["segments"]), 1)
                    data["model_used"] = current_model
                    return data
            except Exception as e:
                last_error = e
                print(f"⚠️ Attempt {attempt+1} error: {e}", flush=True)
                err_str = str(e).lower()
                if "503" in err_str or "unavailable" in err_str or "high demand" in err_str:
                    # Model overloaded: immediately switch to next model
                    model_idx += 1
                elif "429" in err_str or "resource_exhausted" in err_str or "quota" in err_str:
                    # Key quota exhausted: rotate key
                    self.rotator.rotate_next()
                else:
                    # Generic error: switch both model and key
                    model_idx += 1
                    self.rotator.rotate_next()
                attempt += 1

        raise RuntimeError(f"Không thể tạo kịch bản sau {attempt} lần thử: {last_error}")
