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
    from ..config import load_config, KeyRotator, save_config
except (ImportError, ValueError):
    from config import load_config, KeyRotator, save_config


SYSTEM_PROMPT = """Bạn là biên kịch trưởng chuyên nghiệp của các kênh Review Phim triệu view (như Phim Hay, Cuồng Phim, Spoil Phim).
Nhiệm vụ của bạn là viết kịch bản review phim cực kỳ cuốn hút, giữ chân người xem từ giây đầu tiên đến giây cuối cùng theo công thức 3 hồi kinh điển.

QUY TẮC BẮT BUỘC:
1. HOOK 3 GIÂY ĐẦU: Luôn mở đầu bằng câu giật gân, khơi gợi tò mò cực đại (Ví dụ: "Người đàn ông này...", "Cô gái này không thể ngờ...", "Đừng bao giờ dại dột chọc giận kẻ mang biệt danh...").
2. ĐỔI TÊN NHÂN VẬT THÀNH BIỆT DANH (ALIAS): Tuyệt đối không dùng tên Tây rườm rà. Dùng danh xưng thân thuộc, hóm hỉnh (anh Áo Đen, gã Đầu Trọc, chị Đẹp, ông Trùm, bé Cưng,...).
3. CẤU TRÚC 3 HỒI LEO THANG:
   - Hồi 1 (Khởi nguồn): Hoàn cảnh trớ trêu, bi kịch hoặc sự kiện khởi phát.
   - Hồi 2 (Xung đột & Dồn ép): Kẻ địch truy sát, cạm bẫy liên hoàn, tình thế ngàn cân treo sợi tóc.
   - Hồi 3 (Đại chiến & Cú twist): Màn phản công mãn nhãn, kết cục bất ngờ và đúc kết ngắn.
4. ĐỊNH DẠNG TỪNG CÂU ĐỌC (SEGMENT):
   - Mỗi câu thoại chỉ dài 12 - 25 từ (đọc trong khoảng 3.0s - 4.5s) để khớp hoàn hảo với nhịp cắt video nhanh chống Content-ID.
   - Gán `scene_mood`: "suspense" (hồi hộp), "action" (hành động), "drama" (kịch tính), "climax" (cao trào), "twist" (bất ngờ).
   - Gán `film_pos_pct`: Vị trí tương đối diễn ra trong phim từ 0.0 (đầu phim) đến 1.0 (kết phim) để bộ dựng tự động lấy đúng phân cảnh gốc.

BẠN BẮT BUỘC PHẢI TRẢ VỀ DỮ LIỆU ĐỊNH DẠNG JSON DUY NHẤT (không bọc trong markdown hoặc giải thích thêm):
{
  "title": "Tiêu đề review giật gân",
  "hook": "Câu mở đầu 3s",
  "character_aliases": {"Tên gốc": "Biệt danh"},
  "segments": [
    {
      "id": 1,
      "act": "hook",
      "text": "Người đàn ông này vừa bước vào thang máy thì bất ngờ bị 10 gã sát thủ bịt mặt bao vây.",
      "scene_mood": "suspense",
      "film_pos_pct": 0.05
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
        self.rotator = KeyRotator(self.keys)
        self.preferred_model = self.config.get("model_name", "gemini-3.5-flash")
        self.fallback_models = self.config.get("fallback_models", ["gemini-flash-latest", "gemini-flash-lite-latest"])

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

        prompt = f"""Hãy viết kịch bản review phim chi tiết:
- TÊN PHIM: {movie_title}
- THỂ LOẠI: {genre}
- PHONG CÁCH: {style}
- THỜI LƯỢNG MONG MUỐN: {pacing_note}
{alias_instruction}
- TÓM TẮT NỘI DUNG / TRANSCRIPT GỐC (nếu có):
{plot_context if plot_context else "Hãy sử dụng kiến thức chuẩn xác của bạn về cốt truyện phim này để viết một bản tóm tắt hấp dẫn nhất."}

Hãy xuất đúng định dạng JSON như đã quy định, đủ {total_segments} segments từ mở đầu đến kết thúc trọn vẹn của bộ phim.
"""

        models_to_try = [self.preferred_model] + [m for m in self.fallback_models if m != self.preferred_model]
        model_idx = 0
        max_attempts = len(self.keys) * len(models_to_try)
        attempt = 0

        last_error = None
        while attempt < max_attempts:
            client = self.rotator.get_client(timeout_sec=60.0)
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
