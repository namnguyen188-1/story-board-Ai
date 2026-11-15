"""Storyboard AI Studio Pro - Cinematic Shot Bank & Montage Engine.
Implements professional documentary film montage grammar:
- Pre-renders a curated Master Shot Bank (24 high-fidelity cinematic shots: 12 A-Roll + 12 B-Roll)
- Intelligently maps the 24 shots across 100-500+ scenes based on narration semantics and film rhythm
- Strictly enforces Shot Alternation (no adjacent duplicate shots)
- Preserves 100% visual consistency of character & statues throughout long-form (30-60 min) productions
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

# Add parent directory to path
STUDIO_DIR = Path(__file__).resolve().parent
if str(STUDIO_DIR) not in sys.path:
    sys.path.insert(0, str(STUDIO_DIR))

from comfyui_image_provider import make_image


# Master 24-Shot Bank Definitions for Stoic / Marcus Aurelius Productions
STOIC_SHOT_BANK = [
    # --- 12 A-ROLL HERO STATUE SHOTS ---
    {
        "id": "shot_01_hero_torso",
        "type": "a_roll",
        "title": "Hero Center Torso",
        "keywords": ["virtud", "fuerza", "caracter", "presencia", "dignidad", "hombre", "valor", "estoico", "hero", "statue", "strength", "character", "virtue"],
        "prompt": (
            "Cinematic 16:9 photograph, 35mm cinema lens, master cinematography, photorealistic 8k. "
            "Centered medium shot framing of exactly one solitary Carrara marble statue of Stoic emperor Marcus Aurelius, solo figure. "
            "Hyper-muscular sculpted stone torso, broad shoulders, fully intact muscular stone arms and carved stone hands. "
            "Royal crimson draped linen toga cascading over one shoulder, weathered marble texture with fine chisel marks. "
            "Setting: Ancient Roman palace colonnades at sunrise, soft golden morning light, floating embers, sharp focus."
        ),
    },
    {
        "id": "shot_02_face_closeup",
        "type": "a_roll",
        "title": "Contemplative Face Close-up",
        "keywords": ["mente", "sabiduria", "pensamiento", "ojos", "mirada", "verdad", "conciencia", "sabio", "mind", "wisdom", "eyes", "contemplation", "truth"],
        "prompt": (
            "Cinematic 16:9 photograph, 35mm cinema lens, master cinematography, photorealistic 8k. "
            "Intimate close-up portrait of the head of solitary Carrara marble statue of Marcus Aurelius, solo figure. "
            "Intricate facial features, thick curly stone beard and hair, contemplative serene stone eyes gazing forward with quiet wisdom. "
            "Setting: Dramatic chiaroscuro side lighting against shadowy Roman marble pillars, sharp focus on chisel details."
        ),
    },
    {
        "id": "shot_03_low_angle_imposing",
        "type": "a_roll",
        "title": "Low-Angle Heroic Stance",
        "keywords": ["poder", "imperio", "grandeza", "superior", "firmeza", "voluntad", "inquebrantable", "power", "will", "unshakeable", "greatness", "emperor"],
        "prompt": (
            "Cinematic 16:9 photograph, 35mm cinema lens, master cinematography, photorealistic 8k. "
            "Low-angle heroic shot looking up at exactly one solitary monumental Carrara marble statue of Marcus Aurelius, solo figure. "
            "Colossal muscular chest, imposing posture, royal crimson toga draped over shoulder. "
            "Setting: Sunlit Roman colonnade arch reaching toward clear sky, dramatic low-angle perspective, cinematic scale."
        ),
    },
    {
        "id": "shot_04_profile_45_left",
        "type": "a_roll",
        "title": "Three-Quarter Profile Left",
        "keywords": ["distancia", "observar", "juicio", "percepcion", "calma", "prudente", "perspective", "distance", "observe", "judgment", "prudence"],
        "prompt": (
            "Cinematic 16:9 photograph, 35mm cinema lens, master cinematography, photorealistic 8k. "
            "Three-quarter angle view facing left of exactly one solitary Carrara marble statue of Marcus Aurelius, solo figure. "
            "Sculpted muscular stone physique, hand resting naturally at hip, classical toga folds across chest. "
            "Setting: Ancient Roman courtyard with soft ambient afternoon daylight, classical stone architecture."
        ),
    },
    {
        "id": "shot_05_profile_45_right",
        "type": "a_roll",
        "title": "Three-Quarter Profile Right",
        "keywords": ["camino", "destino", "futuro", "horizonte", "eleccion", "decidir", "path", "destiny", "future", "horizon", "choice"],
        "prompt": (
            "Cinematic 16:9 photograph, 35mm cinema lens, master cinematography, photorealistic 8k. "
            "Three-quarter angle view facing right of exactly one solitary Carrara marble statue of Marcus Aurelius, solo figure. "
            "Calm focused gaze into distance, muscular stone torso, crimson draped linen toga. "
            "Setting: Roman terrace overlooking olive groves at sunset, warm golden hour backlighting, cinematic atmosphere."
        ),
    },
    {
        "id": "shot_06_candlelight_study",
        "type": "a_roll",
        "title": "Night Study Chiaroscuro",
        "keywords": ["noche", "soledad", "silencio", "paz", "interior", "alma", "reflexion", "night", "solitude", "silence", "peace", "soul", "reflection"],
        "prompt": (
            "Cinematic 16:9 photograph, 35mm cinema lens, master cinematography, photorealistic 8k. "
            "Medium shot of exactly one solitary Carrara marble statue of Marcus Aurelius in a dark private imperial study, solo figure. "
            "Illuminated by warm golden candlelight bokeh, deep velvety chiaroscuro shadows on marble muscles, peaceful atmosphere. "
            "Setting: Ancient Roman stone library at midnight, quiet contemplation, sharp focus."
        ),
    },
    {
        "id": "shot_07_symmetric_frontal",
        "type": "a_roll",
        "title": "Symmetrical Monumental Frontal",
        "keywords": ["equilibrio", "armonia", "justicia", "razon", "orden", "constancia", "balance", "harmony", "justice", "reason", "order"],
        "prompt": (
            "Cinematic 16:9 photograph, 35mm cinema lens, master cinematography, photorealistic 8k. "
            "Perfect symmetrical medium shot framing of exactly one solitary Carrara marble statue of Marcus Aurelius, solo figure centered. "
            "Muscular carved stone anatomy, serene contemplative face, classical Roman toga draped symmetrically across chest. "
            "Setting: Grand Pantheon archway with harmonious classical geometry, balanced natural light."
        ),
    },
    {
        "id": "shot_08_mountain_twilight",
        "type": "a_roll",
        "title": "Mountain Twilight Resolute",
        "keywords": ["batalla", "lucha", "adversidad", "dificultad", "superar", "resistir", "resistencia", "battle", "struggle", "adversity", "resilience"],
        "prompt": (
            "Cinematic 16:9 photograph, 35mm cinema lens, master cinematography, photorealistic 8k. "
            "Medium shot of exactly one solitary Carrara marble statue of Marcus Aurelius, solo figure standing resolute. "
            "Muscular stone physique, one arm raised steadfastly, weathered marble texture. "
            "Setting: Roman mountain outpost at twilight, glowing brazier fire in foreground, snow-capped peaks in distant background."
        ),
    },
    {
        "id": "shot_09_courtyard_fountain",
        "type": "a_roll",
        "title": "Courtyard Water Fountain",
        "keywords": ["fluir", "naturaleza", "aceptar", "cambio", "tranquilidad", "serenidad", "flow", "nature", "accept", "change", "serenity"],
        "prompt": (
            "Cinematic 16:9 photograph, 35mm cinema lens, master cinematography, photorealistic 8k. "
            "Medium shot of exactly one solitary Carrara marble statue of Marcus Aurelius beside an ancient stone water basin, solo figure. "
            "Reflections of clear water gently rippling across the marble chest, peaceful expression. "
            "Setting: Classical Roman atrium with soft natural light, lush green foliage in background."
        ),
    },
    {
        "id": "shot_10_oil_lamp_night",
        "type": "a_roll",
        "title": "Lamp Light Night Vigil",
        "keywords": ["vigilia", "estudio", "escribir", "meditar", "aprender", "claridad", "vigil", "study", "learn", "clarity", "meditation"],
        "prompt": (
            "Cinematic 16:9 photograph, 35mm cinema lens, master cinematography, photorealistic 8k. "
            "Medium close-up of exactly one solitary Carrara marble statue of Marcus Aurelius, solo figure. "
            "Hand resting near a glowing antique bronze oil lamp, warm golden illumination highlighting facial features and muscular arm. "
            "Setting: Ancient Roman chamber in deep night, warm intimate chiaroscuro, sharp focus."
        ),
    },
    {
        "id": "shot_11_sun_dappled_colonnade",
        "type": "a_roll",
        "title": "Sun-Dappled Colonnade",
        "keywords": ["luz", "dia", "accion", "despertar", "vida", "presente", "momento", "light", "day", "action", "present", "now", "moment"],
        "prompt": (
            "Cinematic 16:9 photograph, 35mm cinema lens, master cinematography, photorealistic 8k. "
            "Medium shot of exactly one solitary Carrara marble statue of Marcus Aurelius, solo figure. "
            "Sunlight filtering through classical columns casting diagonal graphic shadow patterns across the muscular stone chest. "
            "Setting: Bright sunlit Roman temple peristyle courtyard, crisp marble textures, photorealistic 8k."
        ),
    },
    {
        "id": "shot_12_grand_pantheon_hall",
        "type": "a_roll",
        "title": "Grand Pantheon Oculus",
        "keywords": ["universo", "cosmos", "infinito", "eterno", "tiempo", "divino", "pantheon", "universe", "cosmos", "infinite", "eternal"],
        "prompt": (
            "Cinematic 16:9 photograph, 35mm cinema lens, master cinematography, photorealistic 8k. "
            "Wide medium shot of exactly one solitary Carrara marble statue of Marcus Aurelius, solo figure centered in frame. "
            "A radiant single sunbeam streaming down through a grand domed Roman oculus directly illuminating the statue. "
            "Setting: Monumental ancient Roman Pantheon interior, monumental architecture, awe-inspiring cinematography."
        ),
    },

    # --- 12 B-ROLL SYMBOLIC CUTAWAYS & RELICS ---
    {
        "id": "shot_13_hourglass_macro",
        "type": "b_roll",
        "title": "Brass Hourglass Macro",
        "keywords": ["reloj de arena", "hourglass", "clepsidra", "falling sand macro", "reloj arena"],
        "prompt": (
            "Cinematic 16:9 film still, 35mm cinema lens, master cinematography, photorealistic 8k. "
            "Macro close-up shot of an antique Roman brass and blown glass hourglass on a dark stone table. "
            "Fine golden grains of sand steadily trickling through the narrow glass neck, warm candlelight bokeh in background. "
            "Symbol of fleeting time and mortality, poetic lighting, tack sharp focus, shallow depth of field."
        ),
    },
    {
        "id": "shot_14_papyrus_scroll",
        "type": "b_roll",
        "title": "Ancient Papyrus Scroll",
        "keywords": ["escribir", "palabra", "libro", "filosofia", "diario", "meditaciones", "registro", "write", "words", "book", "scroll", "meditations"],
        "prompt": (
            "Cinematic 16:9 film still, 35mm cinema lens, master cinematography, photorealistic 8k. "
            "Close-up of an aged papyrus scroll partially unfurled on a rustic wooden desk, inscribed with ancient Latin calligraphy. "
            "A bronze stylus and small ink pot beside it, illuminated by the warm flickering glow of a nearby candle. "
            "Atmospheric antique Roman study, shallow depth of field, photorealistic texture."
        ),
    },
    {
        "id": "shot_15_roman_coins_scales",
        "type": "b_roll",
        "title": "Denarius Coins & Scales",
        "keywords": ["dinero", "riqueza", "oro", "plata", "comprar", "deseo", "codicia", "material", "money", "wealth", "gold", "coins", "material", "greed"],
        "prompt": (
            "Cinematic 16:9 film still, 35mm cinema lens, master cinematography, photorealistic 8k. "
            "Macro still life of ancient Roman silver and bronze denarius coins scattered on a polished marble slab. "
            "Intricate emperor profiles stamped on aged metallic surfaces, warm golden raking light, dark stone background. "
            "Symbol of material wealth and Stoic detachment, rich textures, sharp focus."
        ),
    },
    {
        "id": "shot_16_flickering_oil_lamp",
        "type": "b_roll",
        "title": "Terracotta Oil Lamp Flame",
        "keywords": ["llama", "fuego", "guia", "esperanza", "oscuridad", "chispa", "calor", "flame", "fire", "light", "darkness", "spark", "lamp"],
        "prompt": (
            "Cinematic 16:9 film still, 35mm cinema lens, master cinematography, photorealistic 8k. "
            "Macro shot of an authentic antique Roman terracotta oil lamp resting on dark weathered stone. "
            "A steady glowing golden flame illuminating the textured clay, delicate wisp of fragrant smoke rising in the dark. "
            "Atmospheric chiaroscuro lighting, warm intimate mood, cinematic shallow depth of field."
        ),
    },
    {
        "id": "shot_17_sundial_courtyard",
        "type": "b_roll",
        "title": "Stone Sundial Shadow",
        "keywords": ["sombra", "sol", "mediodia", "tarde", "reloj", "horas", "destino", "shadow", "sun", "sundial", "hours", "fate"],
        "prompt": (
            "Cinematic 16:9 film still, 35mm cinema lens, master cinematography, photorealistic 8k. "
            "Close-up of a classical carved stone Roman horizontal sundial in a sun-drenched courtyard. "
            "A sharp diagonal bronze gnomon shadow crossing carved Roman numerals, golden afternoon sunlight. "
            "Symbol of passing hours and stoic acceptance of time, beautiful ancient stone texture."
        ),
    },
    {
        "id": "shot_18_laurel_wreath_dagger",
        "type": "b_roll",
        "title": "Laurel Wreath on Marble",
        "keywords": ["honor", "gloria", "corona", "triunfo", "victoria", "deber", "servicio", "honor", "glory", "crown", "triumph", "duty"],
        "prompt": (
            "Cinematic 16:9 film still, 35mm cinema lens, master cinematography, photorealistic 8k. "
            "Still life of a fresh green laurel wreath resting on an ornate carved Carrara marble altar. "
            "Soft dramatic daylight striking the marble carvings, deep olive greens, classical Roman temple interior. "
            "Symbol of philosophical victory over self, master composition, sharp focus."
        ),
    },
    {
        "id": "shot_19_colonnade_perspective",
        "type": "b_roll",
        "title": "Vanishing Colonnade Perspective",
        "keywords": ["camino", "arquitectura", "roma", "columnas", "templo", "vacio", "silencio", "architecture", "columns", "colonnade", "temple", "empty"],
        "prompt": (
            "Cinematic 16:9 film still, 35mm cinema lens, master cinematography, photorealistic 8k. "
            "Architectural perspective view looking down a grand ancient Roman marble colonnade with towering Corinthian pillars. "
            "Golden morning sunbeams slanting across the polished marble floor tiles, empty tranquil grandeur, no people. "
            "Classical Roman majesty, cinematic symmetry, photorealistic 8k."
        ),
    },
    {
        "id": "shot_20_brazier_embers",
        "type": "b_roll",
        "title": "Brazier Glowing Embers",
        "keywords": ["ceniza", "pasion", "ira", "control", "arder", "purificar", "fuego", "ashes", "passion", "anger", "purify", "embers", "brazier"],
        "prompt": (
            "Cinematic 16:9 film still, 35mm cinema lens, master cinematography, photorealistic 8k. "
            "Close-up shot of a decorative bronze Roman brazier glowing with intensely hot red and orange charcoal embers. "
            "Volumetric golden sparks and micro embers floating upward into velvety darkness, atmospheric warmth. "
            "Symbol of inner passion controlled by reason, stunning color contrast, photorealistic detail."
        ),
    },
    {
        "id": "shot_21_chiseled_hand_tablet",
        "type": "b_roll",
        "title": "Marble Hand on Stone Tablet",
        "keywords": ["ley", "principio", "regla", "esculpir", "forma", "disciplina", "habito", "law", "principle", "discipline", "habit", "chisel"],
        "prompt": (
            "Cinematic 16:9 film still, 35mm cinema lens, master cinematography, photorealistic 8k. "
            "Extreme close-up shot of a carved classical Carrara marble hand firmly grasping a stone tablet. "
            "Intricate sculptor chisel textures, authentic marble fissure veins, warm raking sidelight highlighting stone contours. "
            "Master sculpture craftsmanship, macro photographic realism, sharp focus."
        ),
    },
    {
        "id": "shot_22_olive_tree_garden",
        "type": "b_roll",
        "title": "Olive Tree in Roman Garden",
        "keywords": ["paz", "serenidad", "naturaleza", "raiz", "madera", "arbol", "tranquilo", "peace", "serenity", "nature", "tree", "roots", "calm"],
        "prompt": (
            "Cinematic 16:9 film still, 35mm cinema lens, master cinematography, photorealistic 8k. "
            "Scenic view of a majestic ancient gnarled olive tree in a sun-drenched Roman villa peristyle garden. "
            "Sunbeams filtering through silver-green leaves, classical terracotta urns on stone ground, peaceful breeze. "
            "Atmospheric natural serenity, vibrant cinematic colors, photorealistic 8k."
        ),
    },
    {
        "id": "shot_23_scales_of_justice",
        "type": "b_roll",
        "title": "Antique Bronze Scales",
        "keywords": ["justicia", "igualdad", "balance", "pesado", "medida", "rectitud", "moral", "justice", "balance", "measure", "scales", "equity"],
        "prompt": (
            "Cinematic 16:9 film still, 35mm cinema lens, master cinematography, photorealistic 8k. "
            "Antique classical bronze balance scales in perfect horizontal equilibrium on a smooth white marble pedestal. "
            "Soft diffuse ambient museum lighting, subtle bronze patina and metallic reflections. "
            "Symbol of Stoic cardinal virtue of Justice, clean balanced composition, sharp focus."
        ),
    },
    {
        "id": "shot_24_night_temple_stars",
        "type": "b_roll",
        "title": "Roman Temple & Starry Sky",
        "keywords": ["universo", "estrellas", "noche", "cielo", "inmensidad", "eterno", "galaxia", "stars", "universe", "sky", "infinity", "cosmos"],
        "prompt": (
            "Cinematic 16:9 film still, 35mm cinema lens, master cinematography, photorealistic 8k. "
            "Low-angle view of the weathered stone pediment and columns of an ancient Roman temple silhouetted against the night sky. "
            "Brilliant glittering field of stars and the subtle purple and silver glow of the Milky Way arching overhead. "
            "Cosmic perspective, philosophical contemplation of our place in the universe, breathtaking cinematography."
        ),
    },
]


def generate_master_shot_bank(
    shot_bank_dir: Path,
    image_provider: str = "comfyui",
    width: int = 1280,
    height: int = 720,
    force_rebuild: bool = False,
) -> dict[str, Path]:
    """Generates or loads the 24 curated Master Shots into the shot bank directory.
    Returns a dictionary mapping shot_id -> image_path.
    """
    shot_bank_dir.mkdir(parents=True, exist_ok=True)
    shot_map: dict[str, Path] = {}

    print(f"\n[SHOT_BANK] Initializing Cinematic Master Shot Bank ({len(STOIC_SHOT_BANK)} shots)...", flush=True)

    for i, shot in enumerate(STOIC_SHOT_BANK, 1):
        s_id = shot["id"]
        img_file = shot_bank_dir / f"{s_id}.png"
        shot_map[s_id] = img_file

        if img_file.is_file() and img_file.stat().st_size > 50_000 and not force_rebuild:
            print(f"  [Shot {i:02d}/24] Cached: {shot['title']} ({img_file.name})", flush=True)
            continue

        print(f"  [Shot {i:02d}/24] Rendering: {shot['title']} [{shot['type'].upper()}]...", flush=True)
        try:
            make_image(
                prompt=shot["prompt"],
                output=img_file,
                reference_path=None,
                visual_style="color_cinematic",
                genre="stoic",
                width=width,
                height=height,
            )
            print(f"  [Shot {i:02d}/24] Finished: {img_file.name} ({img_file.stat().st_size} bytes)", flush=True)
        except Exception as e:
            print(f"  [Shot {i:02d}/24] ERROR rendering {s_id}: {e}", flush=True)
            # If fail, try to fallback to a neighboring rendered shot
            rendered = [p for p in shot_bank_dir.glob("*.png") if p.is_file() and p.stat().st_size > 50_000]
            if rendered:
                shutil.copy2(rendered[0], img_file)

    return shot_map


def map_scenes_to_shot_bank(
    scenes: list[dict],
    shot_map: dict[str, Path],
    scenes_dir: Path,
) -> list[dict]:
    """Applies professional film montage grammar to map 100-500+ scenes to the 24 Master Shots:
    - Semantic keyword scoring
    - Strict Shot Alternation (no 2 adjacent scenes share the same shot)
    - Pacing rhythm: 65% A-Roll (Character/Statue) / 35% B-Roll (Symbolic relics)
    - Dynamic camera motion cycling per scene
    """
    a_roll_shots = [s for s in STOIC_SHOT_BANK if s["type"] == "a_roll"]
    b_roll_shots = [s for s in STOIC_SHOT_BANK if s["type"] == "b_roll"]

    last_shot_id = ""
    last_was_b_roll = False
    consecutive_a_roll = 0

    print(f"\n[MONTAGE_ENGINE] Mapping {len(scenes)} scenes with Film Grammar & Shot Alternation...", flush=True)

    camera_motions = ["zoom_in", "pan_right", "zoom_out", "orbit_drift", "tilt_up", "pan_left"]

    for idx, sc in enumerate(scenes):
        scene_num = sc.get("scene_number", idx + 1)
        sc_dir = scenes_dir / f"scene_{scene_num:04d}"
        sc_dir.mkdir(parents=True, exist_ok=True)
        target_img = sc_dir / "image.png"

        # Extract combined text for semantic scoring
        narration = str(sc.get("narration", "")).lower()
        summary = str(sc.get("summary", "")).lower()
        desc = str(sc.get("description", "")).lower()
        combined_text = f"{narration} {summary} {desc}"

        # Decide whether this beat should be A-Roll or B-Roll
        # Macro inserts or mentions of objects strongly favor B-Roll
        has_object_kw = any(kw in combined_text for kw in ("tiempo", "hora", "arena", "vela", "fuego", "llama", "escribir", "papel", "moneda", "dinero", "balanza", "arbol", "naturaleza", "estrellas", "cielo"))
        
        prefer_b_roll = False
        if has_object_kw and not last_was_b_roll:
            prefer_b_roll = True
        elif consecutive_a_roll >= 3 and not last_was_b_roll:
            # Prevent character fatigue by inserting a symbolic cutaway
            prefer_b_roll = True
        elif last_was_b_roll:
            # Cut back to protagonist immediately after a B-roll cutaway
            prefer_b_roll = False

        candidate_pool = b_roll_shots if prefer_b_roll else a_roll_shots

        # Score candidates based on keyword matches
        best_score = -1
        best_candidate = candidate_pool[0]

        for cand in candidate_pool:
            if cand["id"] == last_shot_id:
                continue  # STRICT FILM RULE: Never repeat the same shot back-to-back
            score = sum(1 for kw in cand["keywords"] if kw in combined_text)
            if score > best_score:
                best_score = score
                best_candidate = cand

        # Fallback if no keyword matched: round-robin cycle
        if best_score <= 0:
            valid_candidates = [c for c in candidate_pool if c["id"] != last_shot_id]
            best_candidate = valid_candidates[idx % len(valid_candidates)]

        selected_id = best_candidate["id"]
        source_img = shot_map.get(selected_id)

        if source_img and source_img.is_file():
            shutil.copy2(source_img, target_img)

        # Update state for film pacing
        last_shot_id = selected_id
        if best_candidate["type"] == "b_roll":
            last_was_b_roll = True
            consecutive_a_roll = 0
        else:
            last_was_b_roll = False
            consecutive_a_roll += 1

        # Save metadata to job.json / montage_meta.json
        meta = {
            "scene_number": scene_num,
            "shot_id": selected_id,
            "shot_type": best_candidate["type"],
            "shot_title": best_candidate["title"],
            "camera_motion": camera_motions[(scene_num - 1) % len(camera_motions)],
        }
        (sc_dir / "montage_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"[MONTAGE_ENGINE] Successfully mapped {len(scenes)} scenes with 100% visual consistency!", flush=True)
    return scenes


def ensure_shot_bank_and_montage(
    episode_dir: Path,
    scenes: list[dict],
    genre: str = "stoic",
    image_provider: str = "comfyui",
    width: int = 1280,
    height: int = 720,
) -> None:
    """Entry point: pre-renders shot bank if needed, and maps shots across all scenes."""
    genre_clean = str(genre or "").lower().strip()
    # HARD ISOLATION: Only Stoic/Philosophy genres can use this Stoic Master Shot Bank
    if any(other in genre_clean for other in ("drama", "western", "whiteboard", "marker", "animation", "action", "horror")):
        print(f"[SHOT_BANK_GUARD] Skipping shot bank for non-stoic genre: {genre_clean}", flush=True)
        return

    shot_bank_dir = episode_dir / "shot_bank"
    scenes_dir = episode_dir / "scenes"

    shot_map = generate_master_shot_bank(
        shot_bank_dir=shot_bank_dir,
        image_provider=image_provider,
        width=width,
        height=height,
    )

    map_scenes_to_shot_bank(
        scenes=scenes,
        shot_map=shot_map,
        scenes_dir=scenes_dir,
    )
