"""Cinematic Camera Choreography & Master Shot Grammar Engine.
Provides Hollywood-grade visual storytelling, dynamic camera motion archetypes,
optical lens physics, and intelligent shot-sequencing rhythms to eliminate
visual monotony and maximize audience retention across cinematic genres.
"""

from __future__ import annotations

import sys
import re
from typing import Dict, List, Any, Optional

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


# ---------------------------------------------------------------------------
# 1. THE 12 HOLLYWOOD MASTER SHOT ARCHETYPES
# ---------------------------------------------------------------------------
CINEMATIC_SHOT_CATALOG: Dict[str, Dict[str, Any]] = {
    "DOLLY_ZOOM_VERTIGO": {
        "name_vi": "Cú máy Vertigo / Dolly Zoom (Hitchcock Effect)",
        "dramatic_purpose": "Sốc tâm lý cực độ, phát hiện sự thật bàng hoàng, cảm giác mặt đất sụp đổ.",
        "focal_length": "35mm to 85mm dynamic optical focal shift",
        "camera_rig": "High-precision optical tracking dolly with synchronized motorized zoom",
        "lighting_mood": "High-contrast rim lighting, deep shadows stretching backwards",
        "description_en": (
            "Hitchcock Dolly Zoom (Vertigo Effect): Camera dollies forward smoothly along central optical axis "
            "while telephoto lens dynamically zooms out in exact synchronization. The subject remains anchor-locked "
            "at frame center while the background perspective warps, compresses and stretches dramatically in deep parallax. "
            "Visceral psychological distortion, shallow depth of field f/1.8 with pristine circular optical bokeh."
        ),
        "stoic_variant": (
            "Monumental Dolly Zoom on classical marble statue: Camera dollies forward while background ancient Roman colonnade "
            "and thunderous stormy skies warp and stretch into deep perspective, leaving the stoic marble gaze imperturbable."
        ),
        "drama_variant": (
            "Vertigo Dolly Zoom on character's eyes as betrayal hits: Character remains locked in sharp 50mm focus while "
            "the luxury boardroom background stretches away into dizzying vertigo depth, practical ceiling lights blurring."
        )
    },

    "LOW_ANGLE_TITAN": {
        "name_vi": "Góc thấp vĩ đại / Titan Heroic Low-Angle",
        "dramatic_purpose": "Tôn vinh quyền lực tối thượng, sự bất khuất kiên định, vẻ uy nghiêm vượt thời gian.",
        "focal_length": "24mm anamorphic wide-angle prime",
        "camera_rig": "Floor-level ground mount (30cm off floor), 45-60 degree upward tilt",
        "lighting_mood": "Heroic volumetric rim light, edge-lit silhouette against dramatic sky or ceiling architecture",
        "description_en": (
            "Monumental Titan Low-Angle Shot: Camera placed 30cm off the floor, tilted steeply upward at 50 degrees "
            "framing the subject towering into the upper third of the frame. Slow cinematic upward jib drift. "
            "Imposing heroic scale, 24mm anamorphic lens, grand architectural background, dramatic atmospheric chiaroscuro lighting."
        ),
        "stoic_variant": (
            "Heroic low-angle perspective looking upward at the full-length standing classical statue of Marcus Aurelius: "
            "Plinth firmly planted, draped toga cascading down, lightning flash illuminating chiselled cheekbones against stormy clouds."
        ),
        "drama_variant": (
            "Low-angle power shot looking up at the antagonist standing before floor-to-ceiling windows, city skyline glowing below: "
            "Imposing silhouette, sharp tailored suit, slow upward tilt establishing unyielding dominance."
        )
    },

    "EXTREME_MACRO_ECU": {
        "name_vi": "Cận cảnh cực đại / Extreme Close-Up (ECU)",
        "dramatic_purpose": "Đẩy căng thẳng vào tiểu tiết vi mô: con ngươi giãn nở, giọt mồ hôi, mạch đập, vết nứt.",
        "focal_length": "100mm f/1.4 Macro Cine Prime",
        "camera_rig": "Micro-fluid head on ultra-fine slider track, microscopic push-in",
        "lighting_mood": "Single pinpoint key light slicing across texture, deep obsidian shadow",
        "description_en": (
            "Extreme Macro Chiaroscuro Close-Up (ECU): 100mm macro cinema prime at razor-thin f/1.4 depth of field. "
            "Camera glides 10cm from subject with micro-pan, revealing minute physical details in razor-sharp focus. "
            "Only the essential storytelling element is illuminated by a sharp slit of light against rich lifted shadow."
        ),
        "stoic_variant": (
            "Extreme Macro of carved Carrara marble: Chisel marks, weathered ancient stone fissure lines, blank sightless eyes "
            "as a single raindrop rolls slowly down the stone cheek like an unwept tear, volumetric rim lighting."
        ),
        "drama_variant": (
            "Extreme Macro on actor's dilated eye pupil: Iris micro-tremor reflecting the glowing text message on smartphone screen, "
            "bead of sweat tracing temple, jaw muscle clenching with suppressed rage."
        )
    },

    "DIRTY_OVER_THE_SHOULDER": {
        "name_vi": "Góc qua vai nghẹt thở / Dirty Over-The-Shoulder (OTS)",
        "dramatic_purpose": "Xung đột trực diện, thẩm vấn, đàm phán một mất một còn, tạo không gian kẹp chặt.",
        "focal_length": "85mm portrait prime, wide open f/2.0",
        "camera_rig": "Organic handheld rig with subtle human breathing pulse, no robotic stabilization",
        "lighting_mood": "Warm amber key on speaking face, cool blue backlight on foreground silhouette",
        "description_en": (
            "Dirty Over-The-Shoulder (OTS) Confrontation Frame: Camera nestled close behind character A's shoulder "
            "(dark out-of-focus silhouette occupying 25% of the foreground), focusing sharply on character B across the intimate space. "
            "Organic subtle handheld breathing movement conveys visceral tension, shallow depth of field f/2.0, eye lines locked."
        ),
        "stoic_variant": (
            "Over-the-shoulder perspective from behind an ancient Roman philosopher's draped stone shoulder, looking out across "
            "the burning city or crowded forum, stone folds framing the historic panorama."
        ),
        "drama_variant": (
            "Intense dirty OTS across the mahogany interrogation desk: Blurred dark jacket silhouette in left foreground, "
            "framing the protagonist's resolute, uncompromising gaze as they refuse to yield in the confrontation."
        )
    },

    "ORBITAL_ARC_360": {
        "name_vi": "Cú xoay bán nguyệt / 180-360 Degree Orbital Arc",
        "dramatic_purpose": "Thời khắc giác ngộ, ngưng đọng thời gian, chuyển giao số phận, quyết định không thể cứu vãn.",
        "focal_length": "35mm anamorphic prime",
        "camera_rig": "Circular curved tracking track or Steadicam orbit arm, floating 180-degree sweep",
        "lighting_mood": "Volumetric god rays slicing through darkness, backlight shifting continuously across silhouette",
        "description_en": (
            "Cinematic Semicircular Orbital Arc: Steadicam smoothly sweeps along a 180-degree curved trajectory around the subject. "
            "Background elements glide past in rich optical parallax while the subject remains centered in reflective contemplation. "
            "Volumetric light shafts intersect the camera path, creating momentary lens flares that emphasize the pivotal turning point."
        ),
        "stoic_variant": (
            "Smooth 180-degree arc around the standing Marcus Aurelius statue as dawn breaks over the Roman forum: "
            "Golden sunlight slowly sweeps across weathered marble contours, chisel marks catching amber rim light."
        ),
        "drama_variant": (
            "Semicircular Steadicam orbit around the protagonist standing alone in the rain outside the penthouse: "
            "Neon city reflections whirl around her as she makes the fateful phone call that will burn her bridges."
        )
    },

    "DUTCH_ANGLE_PARANOIA": {
        "name_vi": "Góc nghiêng tâm lý / Dutch Canted Angle",
        "dramatic_purpose": "Thế giới mất thăng bằng, hoang tưởng, nguy hiểm cận kề, nhân vật mất kiểm soát thực tại.",
        "focal_length": "28mm wide-angle cine prime",
        "camera_rig": "Tri-axis Dutch roll head, horizon tilted 18-25 degrees off axis",
        "lighting_mood": "Harsh diagonal practical lighting, jagged shadow angles slashing across the walls",
        "description_en": (
            "Dutch Canted Angle Shot: Camera tilted deliberately 22 degrees off the horizontal axis, inducing psychological unease. "
            "Slow ominous push-in along the diagonal axis. Walls lean unnaturally, creating visual tension and vertigo. "
            "Wide 28mm lens exaggerates spatial asymmetry; practical flickering fluorescents cast erratic shadows."
        ),
        "stoic_variant": (
            "Dutch angle tilt looking across toppling Roman pillars and stormy skies: World in chaos and decay, "
            "contrasting with the unwavering upright verticality of the Stoic statue."
        ),
        "drama_variant": (
            "Severe 25-degree Dutch angle in the narrow hospital hallway: Tilted fluorescent ceiling, Doctor rushing forward "
            "as monitors scream alarm, disorienting handheld sway conveying panic and imminent catastrophe."
        )
    },

    "PARALLAX_STEADICAM_FOLLOW": {
        "name_vi": "Cú lướt bám đuổi / Steadicam Parallax Follow",
        "dramatic_purpose": "Tạo nhịp điệu dấn thân, bước vào hang cọp, hành trình không thể quay đầu.",
        "focal_length": "35mm gimbal lens",
        "camera_rig": "Steadicam floating backward at walking speed ahead of character, or tracking in parallel",
        "lighting_mood": "Intermittent overhead pools of light with darkness in between, rhythmic lighting beats",
        "description_en": (
            "Steadicam Tracking Follow Shot: Camera floats backward with hypnotic fluidity 2 meters ahead of the walking subject. "
            "Foreground pillars and archways sweep past with pronounced parallax separation. "
            "Subject advances with unstoppable momentum; shallow depth of field keeps eyes pin-sharp while background corridors recede."
        ),
        "stoic_variant": (
            "Slow gliding tracking shot moving through an endless colonnade of marble statues and Roman archways, "
            "torches burning in wall sconces casting dynamic flickering shadows that dance across the marble."
        ),
        "drama_variant": (
            "Steadicam leading the character as they stride forward with determination: Foreground elements part in parallax separation, "
            "motivated atmospheric practical lighting, determined forward momentum."
        )
    },

    "FOCUS_PULL_REVEAL": {
        "name_vi": "Chuyển tiêu cự kịch tính / Rack Focus / Focus Pull",
        "dramatic_purpose": "Hé lộ mối liên hệ chết người giữa một đồ vật tiền cảnh và nhân vật hậu cảnh.",
        "focal_length": "85mm f/1.4 Telephoto Prime",
        "camera_rig": "Locked tripod with motorized wireless follow-focus unit",
        "lighting_mood": "Focused pool on foreground object, secondary key on background character",
        "description_en": (
            "Cinematic Rack Focus (Focus Pull Reveal): Begins with extreme sharp focus on a critical foreground object "
            "(whisky glass with poison, forged will, pistol) while the background character is a blurred silhouette. "
            "Over 1.5 seconds, focus smoothly racks to the background character's eyes as they notice the object. "
            "Visceral visual storytelling connecting cause and consequence."
        ),
        "stoic_variant": (
            "Focus pull from an ancient hourglass / skull on stone table in foreground to the calm stone eyes of Marcus Aurelius in background, "
            "memento mori symbolism, soft amber candle flame flickering."
        ),
        "drama_variant": (
            "Rack focus from the signed confession document lying on the glass table to Zara's terrified face standing in the doorway, "
            "realizing her secret has been discovered."
        )
    },

    "GODS_EYE_OVERHEAD": {
        "name_vi": "Góc nhìn thượng đế / God's Eye Top-Down Overhead",
        "dramatic_purpose": "Sự nhỏ bé trước định mệnh, cảm giác cô độc tuyệt đối, toàn cảnh bố cục như bàn cờ.",
        "focal_length": "24mm wide angle, straight down 90-degree zenith",
        "camera_rig": "Ceiling truss crane or overhead wire rig, slow 90-degree downward drift",
        "lighting_mood": "Radial downward lighting pool surrounded by vast pitch-navy darkness",
        "description_en": (
            "God's Eye Zenith Overhead Shot: Perpendicular 90-degree bird's eye view looking straight down from ceiling height. "
            "Slow downward vertical drift and subtle rotational roll. The subject is centered in geometric isolation, "
            "surrounded by architectural patterns, floor tiles, scattered documents, or sprawling labyrinth."
        ),
        "stoic_variant": (
            "Top-down 90-degree view looking straight down at the Marcus Aurelius statue standing on a colossal Roman mosaic compass, "
            "rain rippling outward in concentric circles, philosophical solitude."
        ),
        "drama_variant": (
            "Direct top-down shot of the character in a moment of dramatic crisis, "
            "forming an ominous pool around her, geometric isolation."
        )
    },

    "SILHOUETTE_RIM_LIT": {
        "name_vi": "Ngược sáng xẻ bóng / Chiaroscuro Silhouette Rim Light",
        "dramatic_purpose": "Huyền bí, quyền lực ngầm, sự cô đơn nội tâm sâu sắc, bước ra từ bóng tối.",
        "focal_length": "50mm anamorphic cine prime",
        "camera_rig": "Low tripod lock with slow forward creep",
        "lighting_mood": "Blinding background illumination (blaze/fog/window), zero front light, knife-edge golden rim",
        "description_en": (
            "Chiaroscuro Silhouette & Razor Rim Light: The subject is a pure dark silhouette framed against a blinding backlight source "
            "(roaring fire, rain-streaked twilight bay window, steam vent). A razor-thin golden rim light carves the exact contours "
            "of hair, shoulders, and jawline, separating form from darkness without revealing facial details until the final moment."
        ),
        "stoic_variant": (
            "Silhouette of Emperor Marcus Aurelius standing against a blazing Mediterranean sunset and burning Roman horizon, "
            "razor-sharp golden light carving every curl and toga fold in pure majestic silhouette."
        ),
        "drama_variant": (
            "Dark silhouette of Chief Damin standing in the doorway of the dimly lit warehouse, headlights blinding behind him, "
            "thin silver rim light outlining his heavy overcoat and cigar smoke rising into the beam."
        )
    },

    "COWBOY_CONFRONTATION": {
        "name_vi": "Góc Trung Rộng Đối Đầu / American Cowboy Medium-Wide",
        "dramatic_purpose": "Thế thủ trước giao tranh, tay gần vũ khí/tài liệu, ngôn ngữ cơ thể căng thẳng tột độ.",
        "focal_length": "40mm anamorphic prime",
        "camera_rig": "Low-slung Steadicam holding rock-steady at hip level",
        "lighting_mood": "Sidelight casting deep horizontal shadow dividing the frame",
        "description_en": (
            "American Cowboy Shot (Medium Wide from mid-thigh to head): Camera positioned at hip level, capturing both the actor's "
            "determined facial expression and their hands poised near pockets, weapons, or desk surface. "
            "Rock-steady tension, wide anamorphic depth, capturing subtle weight shifts and predatory body language."
        ),
        "stoic_variant": (
            "Medium-wide shot of the standing statue from knees up, capturing the carved hand resting firmly on the hilt of the gladius sword, "
            "stone drapery hanging motionless, resolute posture of an emperor ready to bear the weight of empire."
        ),
        "drama_variant": (
            "Cowboy shot of the hitman standing in the elevator lobby: Mid-thigh framing showing leather gloves slowly unbuttoning jacket, "
            "intense gaze fixed forward, elevator floor numbers counting down overhead."
        )
    },

    "WHIP_PAN_REVEAL": {
        "name_vi": "Cú lia máy chớp nhoáng / Whip Pan / Snap Pan",
        "dramatic_purpose": "Chuyển hướng bất ngờ, phản ứng sốc giật mình, cắt đứt sự êm ả bằng một mối đe dọa mới.",
        "focal_length": "35mm prime, high shutter speed 1/120s with dynamic motion blur",
        "camera_rig": "High-torque fluid head with rapid 90-degree whip-pan snap",
        "lighting_mood": "Dynamic light shift from dark ambient to sudden bright focal point",
        "description_en": (
            "Kinetic Whip Pan (Snap Pan): Fast aggressive horizontal camera whip producing high-velocity motion blur, "
            "abruptly locking onto an unexpected person, weapon, or sudden reaction with pinpoint precision. "
            "Creates immediate pulse-pounding rhythm, resetting viewer attention instantly (Pattern Interrupt)."
        ),
        "stoic_variant": (
            "Fast whip pan from a burning Roman parchment on a table to the towering stone statue standing in the shadows, "
            "unshaken by the flames."
        ),
        "drama_variant": (
            "Violent whip pan from the smiling face of the corporate executive across the table to the bodyguard drawing a silenced pistol "
            "by the doorway, instant transition from false peace to mortal danger."
        )
    }
}


# ---------------------------------------------------------------------------
# 2. SEQUENCE PACING & SHOT RHYTHM DIRECTOR
# ---------------------------------------------------------------------------
# Maps narrative dramatic intensity (0.0 to 1.0) and genre to ideal shot archetypes
GENRE_SHOT_PREFERENCES: Dict[str, List[str]] = {
    "stoic": [
        "LOW_ANGLE_TITAN",
        "EXTREME_MACRO_ECU",
        "SILHOUETTE_RIM_LIT",
        "ORBITAL_ARC_360",
        "DOLLY_ZOOM_VERTIGO",
        "GODS_EYE_OVERHEAD",
        "PARALLAX_STEADICAM_FOLLOW"
    ],
    "drama": [
        "DIRTY_OVER_THE_SHOULDER",
        "EXTREME_MACRO_ECU",
        "DUTCH_ANGLE_PARANOIA",
        "FOCUS_PULL_REVEAL",
        "COWBOY_CONFRONTATION",
        "DOLLY_ZOOM_VERTIGO",
        "PARALLAX_STEADICAM_FOLLOW",
        "WHIP_PAN_REVEAL"
    ],
    "crime": [
        "DIRTY_OVER_THE_SHOULDER",
        "DUTCH_ANGLE_PARANOIA",
        "COWBOY_CONFRONTATION",
        "SILHOUETTE_RIM_LIT",
        "WHIP_PAN_REVEAL",
        "FOCUS_PULL_REVEAL",
        "PARALLAX_STEADICAM_FOLLOW"
    ],
    "action": [
        "WHIP_PAN_REVEAL",
        "LOW_ANGLE_TITAN",
        "PARALLAX_STEADICAM_FOLLOW",
        "DOLLY_ZOOM_VERTIGO",
        "COWBOY_CONFRONTATION",
        "DUTCH_ANGLE_PARANOIA"
    ],
    "animation": [
        "ORBITAL_ARC_360",
        "LOW_ANGLE_TITAN",
        "EXTREME_MACRO_ECU",
        "PARALLAX_STEADICAM_FOLLOW",
        "DOLLY_ZOOM_VERTIGO"
    ],
    "whiteboard": [
        "EXTREME_MACRO_ECU",
        "GODS_EYE_OVERHEAD",
        "FOCUS_PULL_REVEAL",
        "PARALLAX_STEADICAM_FOLLOW"
    ]
}


def select_cinematic_shot_archetype(
    scene_number: int,
    total_scenes: int,
    genre: str = "drama",
    beat_tension: str = "medium",
    previous_shot: Optional[str] = None,
    previous_shot_key: Optional[str] = None
) -> Dict[str, Any]:
    prev = previous_shot or previous_shot_key
    """
    Intelligently assigns a Hollywood master shot archetype based on dramatic progression:
    - Act I (0-25%): Establishing geography, Titan Low-Angle, Tracking follow.
    - Act II (25-75%): Rising tension, Dirty OTS, Dutch angle, Macro ECU, Focus pull.
    - Climax (75-90%): High-impact pattern interrupt (Vertigo Dolly Zoom, Whip Pan, 360 Orbit).
    - Resolution (90-100%): Silhouette Rim-Lit, God's Eye Overhead, Monumental Low-Angle.
    Enforces the ZERO-REPETITION rule: Never selects the same archetype as the previous scene.
    """
    g_low = str(genre or "").lower().strip()
    is_stoic = (
        g_low == "stoic" or
        any(k in g_low for k in ["statue", "marble", "khắc kỷ", "philosophy"])
    )
    is_action = any(k in g_low for k in ["action", "hành động", "thriller", "giật gân"])
    is_crime = any(k in g_low for k in ["crime", "hình sự", "underworld", "tội phạm"])
    is_whiteboard = any(k in g_low for k in ["whiteboard", "colored_marker", "marker"])
    is_anim = any(k in g_low for k in ["animation", "hoạt hình", "anime"])

    if is_stoic:
        category = "stoic"
    elif is_action:
        category = "action"
    elif is_crime:
        category = "crime"
    elif is_whiteboard:
        category = "whiteboard"
    elif is_anim:
        category = "animation"
    else:
        category = "drama"

    candidates = list(GENRE_SHOT_PREFERENCES.get(category, GENRE_SHOT_PREFERENCES["drama"]))

    # Normalized progress across the episode
    progress = max(0.0, min(1.0, (scene_number - 1) / max(1, total_scenes - 1)))
    tension_low = str(beat_tension).lower()

    # Determine ideal shot candidate based on 3-Act Structure
    if progress < 0.15:
        # Scene 1-2: Strong Establishing Master / Heroic Intro
        pool = ["LOW_ANGLE_TITAN", "SILHOUETTE_RIM_LIT", "PARALLAX_STEADICAM_FOLLOW"]
    elif 0.75 <= progress <= 0.88 or "climax" in tension_low or "shock" in tension_low:
        # High Climax / Turning Point: Pattern Interrupt
        pool = ["DOLLY_ZOOM_VERTIGO", "ORBITAL_ARC_360", "WHIP_PAN_REVEAL", "DUTCH_ANGLE_PARANOIA"]
    elif progress > 0.90:
        # Resolution / Final Reflection
        pool = ["SILHOUETTE_RIM_LIT", "GODS_EYE_OVERHEAD", "LOW_ANGLE_TITAN"]
    else:
        # Mid-Arc Narrative Conflict: Alternating Coverage
        if scene_number % 3 == 0:
            pool = ["EXTREME_MACRO_ECU", "FOCUS_PULL_REVEAL"]
        elif scene_number % 3 == 1:
            pool = ["DIRTY_OVER_THE_SHOULDER", "COWBOY_CONFRONTATION"]
        else:
            pool = ["PARALLAX_STEADICAM_FOLLOW", "DUTCH_ANGLE_PARANOIA"]

    # Filter by genre candidates
    valid_pool = [c for c in pool if c in candidates]
    if not valid_pool:
        valid_pool = candidates

    # Enforce ZERO REPETITION: Exclude previous shot
    if prev and prev in valid_pool and len(valid_pool) > 1:
        valid_pool = [c for c in valid_pool if c != prev]

    selected_key = valid_pool[scene_number % len(valid_pool)]
    shot_data = dict(CINEMATIC_SHOT_CATALOG[selected_key])
    shot_data["shot_key"] = selected_key
    return shot_data


def enrich_scene_camera_direction(
    scene: Dict[str, Any],
    scene_number: int,
    total_scenes: int,
    genre: str = "drama",
    previous_shot_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Transforms generic camera descriptions into professional Hollywood camera setups:
    Returns updated dict with:
    - 'camera_motion': Enriched Hollywood camera movement prompt
    - 'optical_specs': Focal length & rig details
    - 'visual_setup_enhancement': Atmospheric lighting and depth cues
    - 'shot_key': The applied archetype key
    """
    existing_motion = str(scene.get("camera_motion") or scene.get("camera") or "").strip()
    beat_text = str(scene.get("summary") or scene.get("beat_summary") or scene.get("description") or "")

    shot = select_cinematic_shot_archetype(
        scene_number=scene_number,
        total_scenes=total_scenes,
        genre=genre,
        beat_tension="climax" if any(w in beat_text.lower() for w in ["sốc", "chết", "bắn", "phản bội", "bí mật", "khủng khiếp", "climax", "shock", "betrayal"]) else "medium",
        previous_shot_key=previous_shot_key
    )

    g_low = str(genre or "").lower()
    is_stoic = "stoic" in g_low or "khắc kỷ" in g_low or "statue" in g_low

    variant_desc = shot.get("stoic_variant") if is_stoic else shot.get("drama_variant")
    core_desc = variant_desc if variant_desc else shot["description_en"]

    enriched_camera = f"{shot['name_vi']} | {core_desc} Lens: {shot['focal_length']}. Rig: {shot['camera_rig']}."

    return {
        "shot_key": shot["shot_key"],
        "name_vi": shot["name_vi"],
        "camera_motion": enriched_camera,
        "optical_specs": f"{shot['focal_length']} on {shot['camera_rig']}",
        "lighting_mood": shot["lighting_mood"],
        "dramatic_purpose": shot["dramatic_purpose"]
    }
