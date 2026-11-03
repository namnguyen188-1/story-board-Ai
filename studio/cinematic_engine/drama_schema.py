"""Cinematic Drama Engine - Schemas & Data Structures.
Strictly defines multi-character dialogue beats, casting profiles, and audio-visual cues.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional


@dataclass
class CharacterProfile:
    """Represents a cast member with their assigned distinct voice and visual DNA."""
    name: str
    gender: str = "male"  # male, female, neutral
    role: str = "protagonist"  # protagonist, antagonist, supporting, narrator
    voice_id: str = "Charon"
    voice_label: str = "Nam trầm điện ảnh"
    personality: str = "Điềm tĩnh, sắc sảo"
    appearance_lock: str = ""
    attire: str = ""
    wardrobe_by_act: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DialogueBeat:
    """A single spoken beat in a scene: either character speech or narrator exposition."""
    beat_id: int
    speaker: str  # Character name or 'Narrator'
    text: str  # Spoken line in native target language
    tone: str = "natural"  # commanding, whisper, angry, terrified, warm, sarcastic
    voice_id: str = "Orus"
    gender: str = "male"
    is_narrator: bool = False
    action: str = ""  # Physical action/expression during line (e.g. 'Arthur slams deed on desk')
    pause_after_seconds: float = 0.35  # Natural breathing cadence before next line

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SceneDrama:
    """A complete cinematic scene featuring multi-character dialogue, BGM mood and SFX."""
    scene_number: int
    setting: str
    summary: str
    visual_setup: str
    camera_motion: str = "slow_zoom_in"
    bgm_mood: str = "tense_investigation"
    sfx_cues: List[str] = field(default_factory=list)
    characters_present: List[str] = field(default_factory=list)
    dialogue_beats: List[DialogueBeat] = field(default_factory=list)
    visual_prompt: str = ""
    start_state: str = ""  # physical opening state; multi-role continuity only
    end_state: str = ""    # physical closing state; multi-role continuity only
    estimated_seconds: float = 8.0
    sequence_id: str = ""
    location_id: str = ""
    props_required: List[str] = field(default_factory=list)
    wardrobe_state: Dict[str, Any] = field(default_factory=dict)
    prop_state: Dict[str, Any] = field(default_factory=dict)
    transition_action: str = ""
    transition_props: List[str] = field(default_factory=list)
    wardrobe_transition_authorized: bool = False

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["dialogue_beats"] = [b.to_dict() if isinstance(b, DialogueBeat) else b for b in self.dialogue_beats]
        return data


@dataclass
class EpisodeDramaPlan:
    """Complete episodic screenplay for a Cinematic Drama episode."""
    series_name: str
    episode_num: int
    language: str
    genre: str
    title: str
    logline: str
    cast: Dict[str, CharacterProfile] = field(default_factory=dict)
    scenes: List[SceneDrama] = field(default_factory=list)
    created_at: str = ""
    locations: Dict[str, Any] = field(default_factory=dict)
    props: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["cast"] = {k: v.to_dict() if isinstance(v, CharacterProfile) else v for k, v in self.cast.items()}
        data["scenes"] = [s.to_dict() if isinstance(s, SceneDrama) else s for s in self.scenes]
        return data
