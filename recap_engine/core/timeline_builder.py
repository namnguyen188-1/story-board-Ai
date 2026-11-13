"""
Timeline Builder for Standalone Movie Recap Engine.
Maps timed voiceover segments to source movie footage with strict Fair-Use shot duration limits (<= 4.0s).
Supports explicit scene timestamps [MM:SS] and intelligent subtitle dialogue matching for 100% audio-visual sync.
"""

from typing import List, Dict, Any, Optional
import re


class TimelineBuilder:
    """Calculates shot slicing and matches voiceover segments with source video timecodes."""

    def __init__(self, source_duration: float, max_clip_seconds: float = 4.0):
        self.source_duration = source_duration
        self.max_clip_seconds = max_clip_seconds

    @staticmethod
    def find_best_subtitle_match(text: str, subtitles: List[Dict[str, Any]]) -> Optional[float]:
        """Finds the timestamp in source subtitles that best matches keywords in narration text."""
        if not subtitles or not text:
            return None

        # Extract significant words (>= 3 chars, lowercase)
        words = set(re.findall(r"\w{3,}", text.lower()))
        # Filter common Vietnamese stop words
        stop_words = {"người", "nhưng", "không", "những", "trong", "được", "nhiều", "này", "khi", "lúc", "với", "cho", "của", "vào", "một", "các", "đã", "sẽ"}
        meaningful_words = words - stop_words
        if not meaningful_words:
            return None

        best_time = None
        best_score = 0
        for sub in subtitles:
            sub_text = sub.get("text", "").lower()
            sub_words = set(re.findall(r"\w{3,}", sub_text)) - stop_words
            overlap = len(meaningful_words & sub_words)
            if overlap > best_score:
                best_score = overlap
                best_time = float(sub.get("start", 0.0))

        if best_score >= 1:
            return best_time
        return None

    def build_timeline(
        self,
        segments: List[Dict[str, Any]],
        start_buffer_pct: float = 0.02,
        end_buffer_pct: float = 0.95,
        subtitles: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Takes voiceover segments with calculated durations and returns a sequence of video cuts.
        Ensures no single video cut exceeds max_clip_seconds.
        Synchronizes 100% with audio duration and semantic scene content.
        """
        usable_start = self.source_duration * start_buffer_pct
        usable_end = self.source_duration * end_buffer_pct
        usable_span = max(10.0, usable_end - usable_start)

        cuts = []
        cut_id = 1
        current_timeline_time = 0.0

        for seg in segments:
            seg_id = seg.get("id", cut_id)
            duration = float(seg.get("duration", seg.get("est_duration", 3.5)))

            # Priority 1: Explicit scene timestamp specified by user or AI [MM:SS]
            if seg.get("source_time") is not None and float(seg["source_time"]) >= 0:
                base_src_time = max(0.0, min(self.source_duration - 4.0, float(seg["source_time"])))
            # Priority 2: Semantic keyword matching from source subtitles
            elif subtitles:
                matched_time = self.find_best_subtitle_match(seg.get("text", ""), subtitles)
                if matched_time is not None:
                    base_src_time = max(usable_start, min(usable_end - 4.0, matched_time))
                else:
                    film_pos_pct = float(seg.get("film_pos_pct", 0.1))
                    base_src_time = usable_start + (usable_span * film_pos_pct)
            # Priority 3: Film progression percentage (0.0 to 1.0)
            else:
                film_pos_pct = float(seg.get("film_pos_pct", 0.1))
                base_src_time = usable_start + (usable_span * film_pos_pct)

            # Clamp base_src_time within video bounds
            base_src_time = max(0.0, min(usable_end - 4.0, base_src_time))

            # If segment is longer than max_clip_seconds, divide into multiple sub-cuts
            remaining_dur = duration
            sub_index = 0

            while remaining_dur > 0:
                clip_dur = min(remaining_dur, self.max_clip_seconds)

                # Offset each sub-cut slightly to show dynamic camera angles
                src_start = base_src_time + (sub_index * 6.0)
                if src_start + clip_dur > usable_end:
                    src_start = max(usable_start, usable_end - clip_dur - (sub_index * 2.0))

                cuts.append({
                    "cut_id": cut_id,
                    "seg_id": seg_id,
                    "sub_index": sub_index,
                    "timeline_start": round(current_timeline_time, 2),
                    "timeline_end": round(current_timeline_time + clip_dur, 2),
                    "duration": round(clip_dur, 2),
                    "source_start": round(src_start, 2),
                    "source_end": round(src_start + clip_dur, 2)
                })

                current_timeline_time += clip_dur
                remaining_dur -= clip_dur
                cut_id += 1
                sub_index += 1

        return cuts
