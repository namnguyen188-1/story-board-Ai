import os
import json
import hashlib
from pathlib import Path
import sys

sys.path.insert(0, r"d:\STORYBOARD_AI\studio")
from cinematic_engine.drama_auto_repair import parse_9_fields, sanitize_forbidden_words

ep_dir = Path(r"d:\STORYBOARD_AI\studio\productions\DRAMA-2\episode_002\scenes")

PROMPTS = {
    13: """========== SCENE_013 | TIMELINE 02:00–02:10 | GENERATE 10 SECONDS ==========
FORMAT & STYLE: 16:9; 10s motion-video; photorealistic Hollywood cinematic live-action film, natural lighting, organic skin texture. NO 3D CGI, NO cartoons, NO statues.
CHARACTERS: Princess Ugomma: Age 22, African royal woman in emerald silk robes. Prince Obaza: Age 25, royal prince in dark tunic.
SETTING & START STATE: Royal Banquet Hall. Ugomma stands center hall; Obaza stands nearby looking at her with cold shock.
LIGHTING & COLOR: Dramatic cinematic chiaroscuro, warm candle glow, soft golden rim light.
CAMERA: Smooth cinematic medium-shot tracking subtly with actor movement.
TIMED ACTION: 0-2s: Ugomma looks around in disbelief. 2-8s: Obaza gestures in dismay. Ugomma clasps her hands, stepping back in deep emotional distress. 8-10s: Ugomma stands alone in sorrow.
END STATE: Ugomma stands center room in quiet distress as candlelight flickers.
AUDIO: 0.5-5.0s: Prince Obaza speaks in English (commanding, voice Charon): "What has come over you, Ugomma? Look at what you have done to this hall.". Only Prince Obaza lip-syncs. 5.0-9.5s: Princess Ugomma speaks in English (trembling, voice Kore): "It is not me... please, I do not know why this is happening to me.". Only Princess Ugomma lip-syncs. Ambient SFX: soft_wind, flickering_candles.
CONSTRAINTS: Strict live-action realism, preserve actor likeness and wardrobe, no subtitles or text overlays.""",

    41: """========== SCENE_041 | TIMELINE 06:40–06:50 | GENERATE 10 SECONDS ==========
FORMAT & STYLE: 16:9; 10s motion-video; photorealistic Hollywood cinematic live-action film, natural lighting, organic skin texture. NO 3D CGI, NO cartoons, NO statues.
CHARACTERS: Efora: Age 23, sharp angular features, wearing dark hooded robes, intense focused expression.
SETTING & START STATE: Efora's Hideout, ancient damp stone cavern with dim torchlight. Efora kneels on the stone floor.
LIGHTING & COLOR: Moody low-key cinematic lighting, deep indigo shadows, soft violet glow on fingertips.
CAMERA: Steady eye-level cinematic medium shot, subtle slow push-in.
TIMED ACTION: 0-2s: Efora kneels breathing heavily. 2-8s: She arches slightly, hands trembling on stone floor as energy pulses. 8-10s: Collapses backward clutching her chest in exhaustion.
END STATE: Efora rests against stone wall, gasping softly in dim violet ambient light.
AUDIO: 0.5-9.5s: Efora speaks in English (menacing whisper, voice Sadachbia): "The power... it consumes. It hungers for more.". Only Efora lip-syncs. Ambient SFX: low_frequency_hum, cavern_drips.
CONSTRAINTS: Strict live-action realism, preserve actor likeness and wardrobe, no subtitles or text overlays.""",

    44: """========== SCENE_044 | TIMELINE 07:10–07:20 | GENERATE 10 SECONDS ==========
FORMAT & STYLE: 16:9; 10s motion-video; photorealistic Hollywood cinematic live-action film, natural lighting, organic skin texture. NO 3D CGI, NO cartoons, NO statues.
CHARACTERS: Princess Ugomma: Age 22, regal African woman wearing woven amber and silk bedchamber gown.
SETTING & START STATE: Ugomma's Royal Chamber. Ugomma is seated on the edge of a carved mahogany bed.
LIGHTING & COLOR: Warm ambient oil lamp glow, long dramatic shadows dancing on woven tapestries.
CAMERA: Intimate medium close-up with gentle cinematic breathing motion.
TIMED ACTION: 0-2s: Ugomma sits listening attentively. 2-8s: She clutches her silk gown, gazing anxiously at the moving shadows on the wall. 8-10s: She lowers her head in deep contemplation.
END STATE: Ugomma remains on the bed, watchful and guarded in the lamplight.
AUDIO: 0.5-9.5s: Princess Ugomma speaks in English (trembling whisper, voice Kore): "Efora... what secret power have you summoned against our people?". Only Princess Ugomma lip-syncs. Ambient SFX: oil_lamp_crackle, distant_wind.
CONSTRAINTS: Strict live-action realism, preserve actor likeness and wardrobe, no subtitles or text overlays.""",

    47: """========== SCENE_047 | TIMELINE 07:40–07:50 | GENERATE 10 SECONDS ==========
FORMAT & STYLE: 16:9; 10s motion-video; photorealistic Hollywood cinematic live-action film, natural lighting, organic skin texture. NO 3D CGI, NO cartoons, NO statues.
CHARACTERS: Odili: Age 26, athletic royal guard captain in brown leather tunic and bronze wrist bracers.
SETTING & START STATE: Palace Training Courtyard at night. Odili stands in the center of the mist-covered courtyard holding a ceremonial staff.
LIGHTING & COLOR: Cool moonlight cutting through mist, warm torchlight in background.
CAMERA: Dynamic medium shot tracking Odili's defensive stance.
TIMED ACTION: 0-2s: Odili steps into defensive stance. 2-8s: Swings ceremonial staff smoothly, sweeping mist aside, eyes scanning shadows. 8-10s: Staff held firmly, breathing steady.
END STATE: Odili stands resolute in courtyard, staff grounded, vigilant.
AUDIO: 0.5-9.5s: Odili speaks in English (commanding, voice Fenrir): "Stand fast, shadowy rival! You will not pass!". Only Odili lip-syncs. Ambient SFX: staff_swoosh, night_crickets, swirling_wind.
CONSTRAINTS: Strict live-action realism, preserve actor likeness and wardrobe, no subtitles or text overlays.""",

    56: """========== SCENE_056 | TIMELINE 09:10–09:20 | GENERATE 10 SECONDS ==========
FORMAT & STYLE: 16:9; 10s motion-video; photorealistic Hollywood cinematic live-action film, natural lighting, organic skin texture. NO 3D CGI, NO cartoons, NO statues.
CHARACTERS: Princess Ugomma: Age 22, emerald silk robe. Odili: Age 26, captain in leather tunic.
SETTING & START STATE: Ugomma's Chamber. Ugomma and Odili stand in center room under warm lamp glow.
LIGHTING & COLOR: Rich warm interior cinematic lighting, golden highlights on facial features.
CAMERA: Two-shot medium framing with subtle motivated pans between speakers.
TIMED ACTION: 0-2s: Ugomma looks intently at Odili. 2-8s: She grasps his forearm urgently; Odili nods with resolute loyalty. 8-10s: Both turn toward chamber door, prepared.
END STATE: Ugomma and Odili stand united in determined resolve.
AUDIO: 0.5-5.0s: Ugomma speaks in English (commanding, voice Kore): "We cannot wait for dawn. We must confront before he strikes again.". Only Ugomma lip-syncs. 5.0-9.5s: Odili speaks in English (steadfast, voice Fenrir): "I will stand by your side, Princess. Always.". Only Odili lip-syncs. Ambient SFX: soft_torch_flicker, distant_night_owl.
CONSTRAINTS: Strict live-action realism, preserve actor likeness and wardrobe, no subtitles or text overlays.""",

    114: """========== SCENE_114 | TIMELINE 18:50–19:00 | GENERATE 10 SECONDS ==========
FORMAT & STYLE: 16:9; 10s motion-video; photorealistic Hollywood cinematic live-action film, natural lighting, organic skin texture. NO 3D CGI, NO cartoons, NO statues.
CHARACTERS: Odili: Age 26, guard captain in leather tunic. Palace Guards: Two guards in bronze helmets in background.
SETTING & START STATE: Ancient Marketplace Gate. Odili stands confidently near carved timber gate posts.
LIGHTING & COLOR: Bright daytime golden African sunlight, soft shadows beneath market canopies.
CAMERA: Cinematic medium tracking shot moving alongside Odili.
TIMED ACTION: 0-2s: Odili adjusts belt near gate. 2-8s: Odili addresses guards with authoritative hand gesture; guards salute respectfully. 8-10s: Odili surveys busy market street.
END STATE: Odili stands guard, watchful and composed as market bustles behind.
AUDIO: 0.5-9.5s: Odili speaks in English (commanding, voice Fenrir): "Keep a watchful eye while the markets remain this full. No lapse in guard.". Only Odili lip-syncs. Ambient SFX: bustling_market_murmur, distant_clatter.
CONSTRAINTS: Strict live-action realism, preserve actor likeness and wardrobe, no subtitles or text overlays.""",

    117: """========== SCENE_117 | TIMELINE 19:20–19:30 | GENERATE 10 SECONDS ==========
FORMAT & STYLE: 16:9; 10s motion-video; photorealistic Hollywood cinematic live-action film, natural lighting, organic skin texture. NO 3D CGI, NO cartoons, NO statues.
CHARACTERS: Princess Ugomma: Age 22, golden patterned silk dress. Odili: Age 26, relaxed leather tunic.
SETTING & START STATE: Guest Palace Balcony Chamber. Ugomma stands by carved table unrolling scroll; Odili leans on pillar.
LIGHTING & COLOR: Soft afternoon sunlight streaming through arched colonnades, warm ambient glow.
CAMERA: Smooth medium two-shot with shallow depth of field.
TIMED ACTION: 0-2s: Ugomma looks up from scroll smiling. 2-8s: Shows scroll to Odili; Odili smiles back with genuine warmth and admiration. 8-10s: Both share relaxed peaceful moment.
END STATE: Ugomma and Odili smiling together, atmosphere of relief and joy.
AUDIO: 0.5-5.0s: Ugomma speaks in English (hopeful, voice Kore): "The markets are thriving; the people finally have abundance again.". Only Ugomma lip-syncs. 5.0-9.5s: Odili speaks in English (warm, voice Fenrir): "It is your wisdom that restored their hope.". Only Odili lip-syncs. Ambient SFX: distant_city_cheers, gentle_breeze.
CONSTRAINTS: Strict live-action realism, preserve actor likeness and wardrobe, no subtitles or text overlays.""",

    122: """========== SCENE_122 | TIMELINE 20:10–20:20 | GENERATE 10 SECONDS ==========
FORMAT & STYLE: 16:9; 10s motion-video; photorealistic Hollywood cinematic live-action film, natural lighting, organic skin texture. NO 3D CGI, NO cartoons, NO statues.
CHARACTERS: Princess Ugomma: Age 22, simple travelling wrap. Odili: Age 26, relaxed posture.
SETTING & START STATE: Wilderness Campsite under night sky. Both sitting on woven mats near small glowing campfire.
LIGHTING & COLOR: Warm flickering campfire glow on faces, deep midnight blue star-filled backdrop.
CAMERA: Intimate medium close-up, slow gentle drift across campfire light.
TIMED ACTION: 0-2s: Ugomma looks into flames pensively. 2-8s: Turns to Odili with soft gentle gaze; Odili smiles tenderly, leaning slightly closer. 8-10s: Peaceful shared silence.
END STATE: Both sit side by side looking into fire with quiet affection.
AUDIO: 0.5-5.0s: Ugomma speaks in English (gentle whisper, voice Kore): "Do you dream of a home filled with children, Odili?". Only Ugomma lip-syncs. 5.0-9.5s: Odili speaks in English (tender, voice Fenrir): "With you, Ugomma, any home would be my kingdom.". Only Odili lip-syncs. Ambient SFX: crackling_campfire_sparks, night_wind.
CONSTRAINTS: Strict live-action realism, preserve actor likeness and wardrobe, no subtitles or text overlays.""",

    134: """========== SCENE_134 | TIMELINE 22:10–22:20 | GENERATE 10 SECONDS ==========
FORMAT & STYLE: 16:9; 10s motion-video; photorealistic Hollywood cinematic live-action film, natural lighting, organic skin texture. NO 3D CGI, NO cartoons, NO statues.
CHARACTERS: Elder Chuka: Age 58, respected village elder in festive tunic. Villagers in background.
SETTING & START STATE: Village Square under afternoon sun. Sunlit square with villagers gathered.
LIGHTING & COLOR: Rich golden hour sunlight, vibrant African textiles, deep dynamic range.
CAMERA: Medium-wide establishing shot slowly pushing toward Elder Chuka.
TIMED ACTION: 0-2s: Elder Chuka raises staff toward sky. 2-8s: Villagers clap and cheer joyfully; Elder Chuka turns smiling broadly to the crowd. 8-10s: Crowd celebrates with raised hands.
END STATE: Crowd cheers as festive energy fills the square.
AUDIO: 0.5-9.5s: Elder Chuka speaks in English (celebratory, voice Charon): "Long live the royal house! The future of Ehi is secure!". Only Elder Chuka lip-syncs. Ambient SFX: joyful_village_cheers, distant_ceremonial_drums.
CONSTRAINTS: Strict live-action realism, preserve actor likeness and wardrobe, no subtitles or text overlays.""",

    163: """========== SCENE_163 | TIMELINE 27:00–27:10 | GENERATE 10 SECONDS ==========
FORMAT & STYLE: 16:9; 10s motion-video; photorealistic Hollywood cinematic live-action film, natural lighting, organic skin texture. NO 3D CGI, NO cartoons, NO statues.
CHARACTERS: Elder Chuka: Age 58, respected elder in patterned tunic. Villagers in background.
SETTING & START STATE: Village Square in clear morning light. Small groups of villagers conversing happily.
LIGHTING & COLOR: Bright crisp morning sunlight, pastel sky, warm earth tones.
CAMERA: Wide cinematic tracking shot gliding through smiling village gathering.
TIMED ACTION: 0-2s: Villagers point toward palace hill. 2-8s: Elder Chuka steps forward with hand on chest, speaking warmly as villagers listen with bright smiles. 8-10s: Villagers nod in agreement.
END STATE: Villagers looking toward palace with hopeful, happy expressions.
AUDIO: 0.5-9.5s: Elder Chuka speaks in English (joyful, voice Charon): "The stars align for the child of Ehi. Peace is coming.". Only Elder Chuka lip-syncs. Ambient SFX: morning_birds, gentle_village_murmur.
CONSTRAINTS: Strict live-action realism, preserve actor likeness and wardrobe, no subtitles or text overlays.""",

    174: """========== SCENE_174 | TIMELINE 28:50–29:00 | GENERATE 10 SECONDS ==========
FORMAT & STYLE: 16:9; 10s motion-video; photorealistic Hollywood cinematic live-action film, natural lighting, organic skin texture. NO 3D CGI, NO cartoons, NO statues.
CHARACTERS: Elder Chuka: Age 58, respected elder in festive tunic. Villagers in background.
SETTING & START STATE: Village Square festively decorated. Villagers gather beating traditional drums and dancing.
LIGHTING & COLOR: Golden afternoon sunlight illuminating swirling dust and colorful dance wraps.
CAMERA: Vibrant medium shot moving with the rhythm of the dancers.
TIMED ACTION: 0-2s: Dancers sway to drum rhythm. 2-8s: Elder Chuka raises both arms in joyful praise, leading celebratory dance. 8-10s: Dancers smile and spin in unison.
END STATE: Village celebrating royal birth with colorful energy and laughter.
AUDIO: 0.5-9.5s: Elder Chuka speaks in English (triumphant, voice Charon): "A new life! The Kingdom of Ehi breathes again today!". Only Elder Chuka lip-syncs. Ambient SFX: rhythmic_traditional_drums, joyful_celebration_cheers.
CONSTRAINTS: Strict live-action realism, preserve actor likeness and wardrobe, no subtitles or text overlays.""",

    181: """========== SCENE_181 | TIMELINE 30:00–30:10 | GENERATE 10 SECONDS ==========
FORMAT & STYLE: 16:9; 10s motion-video; photorealistic Hollywood cinematic live-action film, natural lighting, organic skin texture. NO 3D CGI, NO cartoons, NO statues.
CHARACTERS: Princess Ugomma: Age 22, regal woman in cream linen gown. Royal Child: Newborn infant wrapped in soft white cloth.
SETTING & START STATE: Ugomma's Bedchamber. Ugomma sits on low bed cradling the sleeping infant.
LIGHTING & COLOR: Intimate warm oil lamp light, soft shadows, subtle mystical violet shimmer in ambient dust.
CAMERA: Intimate slow push-in from medium shot to close-up of mother and child.
TIMED ACTION: 0-2s: Ugomma looks lovingly at infant. 2-8s: Gently touches child's cheek, then gasps softly as baby opens eyes; Ugomma's eyes widen in awe and quiet mystery. 8-10s: Holds child closer protectively.
END STATE: Ugomma cradling child, staring with profound wonder into the camera direction.
AUDIO: 0.5-9.5s: Princess Ugomma speaks in English (trembling whisper, voice Kore): "What... what flows through your spirit, my little one?". Only Princess Ugomma lip-syncs. Ambient SFX: soft_infant_breath, distant_thunder, oil_lamp_crackle.
CONSTRAINTS: Strict live-action realism, preserve actor likeness and wardrobe, no subtitles or text overlays."""
}

for sc, prompt_text in PROMPTS.items():
    clean_prompt = sanitize_forbidden_words(prompt_text.strip())
    # validate with 9 fields
    header, fields = parse_9_fields(clean_prompt)
    sdir = ep_dir / f"scene_{sc:04d}"
    sdir.mkdir(parents=True, exist_ok=True)
    
    # write clean repair file
    rf = sdir / "muse_scene_repair_9_fields.txt"
    rf.write_text(clean_prompt, encoding="utf-8")
    
    # write metadata manifest
    mf = sdir / "muse_scene_repair.json"
    manifest = {
        "status": "ONE_REPAIR_ARMED",
        "attempt_limit": 1,
        "repaired_sha256": hashlib.sha256(clean_prompt.encode("utf-8")).hexdigest(),
        "error_class": "SANITIZED_CONCISE_PROMPT",
        "must_not_cascade_accounts": True
    }
    mf.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Scene {sc:04d}: SUCCESS - len={len(clean_prompt)}, fields={len(fields)}")

print("\nALL 12 SCENES PREPARED SUCCESSFULLY!")
