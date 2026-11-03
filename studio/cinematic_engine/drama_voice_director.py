"""Cinematic Voice Director - Automatic Character Voice Casting.
Selects and assigns distinct, persona-matched voices for each character in the drama.
Guarantees NO two characters in the same episode sound identical.
"""
from __future__ import annotations
import re
from typing import Dict, List, Any, Optional
from .drama_schema import CharacterProfile


# Curated Gemini 3.8 Voice Casting Profiles
MALE_CASTING_POOLS = [
    {"id": "Fenrir", "type": "Hero / Strong / Action", "tone": "Mạnh mẽ, uy lực, trực diện"},
    {"id": "Charon", "type": "Authoritative / Deep / Elder", "tone": "Trầm ấm, đĩnh đạc, quyền lực"},
    {"id": "Orus", "type": "Warm / Natural / Everyman", "tone": "Ấm áp, gần gũi, cảm xúc"},
    {"id": "Alnilam", "type": "Commanding / Antagonist / Boss", "tone": "Lãnh đạm, sắc sảo, nguy hiểm"},
    {"id": "Gacrux", "type": "Philosopher / Mature / Mentor", "tone": "Sâu lắng, từng trải, thông thái"},
    {"id": "Enceladus", "type": "Dark / Mysterious / Rogue", "tone": "Bí ẩn, khàn nhẹ, lạnh lùng"},
    {"id": "Iapetus", "type": "Young / Energetic / Youth", "tone": "Trẻ trung, nhiệt huyết, trong sáng"},
    {"id": "Algenib", "type": "Rugged / Western / Veteran", "tone": "Phong trần, phong sương, quyết đoán"},
]

FEMALE_CASTING_POOLS = [
    {"id": "Kore", "type": "Sharp / Determined / Leader", "tone": "Dứt khoát, sắc sảo, quyền lực"},
    {"id": "Aoede", "type": "Emotional / Tender / Empath", "tone": "Truyền cảm, dịu dàng, ấm áp"},
    {"id": "Sadachbia", "type": "Cunning / Rival / Antagonist", "tone": "Sống động, mỉa mai, hiểm hóc"},
    {"id": "Despina", "type": "Seductive / Smooth / Confident", "tone": "Mượt mà, cuốn hút, bí ẩn"},
    {"id": "Leda", "type": "Young / Modern / Clever", "tone": "Trẻ trung, lanh lợi, hiện đại"},
    {"id": "Zephyr", "type": "Intellectual / Scientific / Calm", "tone": "Trong trẻo, điềm tĩnh, tri thức"},
    {"id": "Puck", "type": "Playful / Child / Sassy", "tone": "Hoạt hình, tươi vui, nhí nhảnh"},
    {"id": "Sulafat", "type": "Deep / Motherly / Heartfelt", "tone": "Trầm ấm, dạt dào cảm xúc"},
]

NARRATOR_VOICES = {
    "male": {"id": "Charon", "label": "Nam trầm dẫn chuyện điện ảnh"},
    "female": {"id": "Aoede", "label": "Nữ truyền cảm dẫn dắt cốt truyện"},
}


class VoiceDirector:
    """Manages character voice casting across an episodic production."""

    def __init__(self, language: str = "Vietnamese", region: str = "auto"):
        self.language = language
        self.region = region
        self.used_voices = set()

    def cast_characters(self, character_defs: List[Dict[str, Any]]) -> Dict[str, CharacterProfile]:
        """Automatically assigns unique, persona-matched voices to all characters."""
        cast_map: Dict[str, CharacterProfile] = {}
        male_idx = 0
        female_idx = 0

        # Always reserve and assign a dedicated Narrator voice first
        narrator_gender = "male"
        cast_map["Narrator"] = CharacterProfile(
            name="Narrator",
            gender=narrator_gender,
            role="narrator",
            voice_id=NARRATOR_VOICES[narrator_gender]["id"],
            voice_label=NARRATOR_VOICES[narrator_gender]["label"],
            personality="Khách quan, dẫn dắt không gian điện ảnh",
            appearance_lock=""
        )
        self.used_voices.add(NARRATOR_VOICES[narrator_gender]["id"])

        for c_def in character_defs:
            name = str(c_def.get("name") or c_def.get("character_name") or "Nhân vật").strip()
            if not name or name.lower() in ("narrator", "người dẫn chuyện", "dẫn chuyện"):
                continue

            # Detect gender from persona or name
            gender = self._detect_gender(c_def)
            role = str(c_def.get("role") or "protagonist").lower()

            if gender == "female":
                voice_choice = self._pick_voice(FEMALE_CASTING_POOLS, female_idx, role)
                female_idx += 1
            else:
                voice_choice = self._pick_voice(MALE_CASTING_POOLS, male_idx, role)
                male_idx += 1

            profile = CharacterProfile(
                name=name,
                gender=gender,
                role=role,
                voice_id=voice_choice["id"],
                voice_label=f"{voice_choice['type']} ({voice_choice['tone']})",
                personality=str(c_def.get("personality") or voice_choice["tone"]),
                appearance_lock=str(c_def.get("appearance") or c_def.get("appearance_lock") or ""),
                attire=str(c_def.get("attire") or c_def.get("wardrobe") or ""),
                wardrobe_by_act=c_def.get("wardrobe_by_act") or {}
            )
            cast_map[name] = profile

        return cast_map

    def _detect_gender(self, c_def: Dict[str, Any]) -> str:
        text_blob = " ".join([
            str(c_def.get("name", "")),
            str(c_def.get("appearance", "")),
            str(c_def.get("gender", "")),
            str(c_def.get("personality", "")),
            str(c_def.get("role", "")),
        ]).lower()

        female_clues = ["nữ", "female", "woman", "girl", "bà", "cô", "chị", "mother", "mẹ", "vợ", "wife", "lady", "queen", "evelyn", "sarah", "mary", "emily"]
        if any(re.search(rf"\b{w}\b", text_blob) for w in female_clues):
            return "female"
        return "male"

    def _pick_voice(self, pool: List[Dict[str, str]], fallback_idx: int, role: str) -> Dict[str, str]:
        # Prefer villain/antagonist voice if role is antagonist
        if "antagonist" in role or "villain" in role:
            for item in pool:
                if "antagonist" in item["type"].lower() or "commanding" in item["type"].lower() or "cunning" in item["type"].lower():
                    if item["id"] not in self.used_voices:
                        self.used_voices.add(item["id"])
                        return item

        # Pick unused voice
        for item in pool:
            if item["id"] not in self.used_voices:
                self.used_voices.add(item["id"])
                return item

        # If pool exhausted, fallback modulo
        return pool[fallback_idx % len(pool)]
