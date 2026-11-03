"""Targeted Storyboard AI reference/voice alignment hardening, 2026-10-31.
Only modifies Storyboard AI. Transactional backups, no live Muse generation.
"""
from pathlib import Path
import shutil, time, py_compile

ROOT = Path(r"D:\STORYBOARD_AI\studio")
changes = {}
def load(name):
    path = ROOT / name
    if name not in changes:
        changes[name] = path.read_text(encoding="utf-8")
    return changes[name]
def replace(name, old, new):
    src = load(name)
    count = src.count(old)
    if count != 1:
        raise RuntimeError(f"Expected 1 match, found {count}: {name}, {old[:85]!r}")
    changes[name] = src.replace(old, new, 1)

# Preserve all original callers: style reference remains the default.
im = "engine/tools/image_gen.py"
replace(im,
    "def image_gen_tool_fn(prompt: str, reference_image_path: str = None, subject_reference_image_path: str = None) -> str:",
    "def image_gen_tool_fn(prompt: str, reference_image_path: str = None, subject_reference_image_path: str = None, *, reference_mode: str = 'style') -> str:")
replace(im,
    'contents.append("The following image is the PREVIOUS scene in this storyboard series. Use it ONLY as a style and aesthetic reference to maintain visual consistency (line weight, color palette, character style). Do NOT replicate or edit this image — generate a completely NEW scene based on the prompt.")\n                contents.append(types.Part.from_bytes(data=image_bytes, mime_type="image/png"))',
    '''if reference_mode == "character_identity":
                    contents.append("This is the APPROVED CHARACTER IDENTITY REFERENCE, NOT a previous scene. Keep the exact face, hairstyle, apparent age, costume and distinctive features of this character. Generate a new composition and action but NEVER change the character identity or outfit. Other people should keep their own identities.")
                else:
                    contents.append("The following image is the PREVIOUS scene in this storyboard series. Use it ONLY as a style and aesthetic reference to maintain visual consistency (line weight, color palette, character style). Do NOT replicate or edit this image — generate a completely NEW scene based on the prompt.")
                mime = "image/jpeg" if reference_image_path.lower().endswith((".jpg", ".jpeg")) else "image/png"
                contents.append(types.Part.from_bytes(data=image_bytes, mime_type=mime))''')

vp = "cinematic_engine/drama_video_engine.py"
replace(vp, "raw_path = image_gen_tool_fn(prompt=prompt_text, reference_image_path=ref_str)",
            'raw_path = image_gen_tool_fn(prompt=prompt_text, reference_image_path=ref_str, reference_mode="character_identity")')

# Muse videos may contain speech other than requested script: no false subtitle PASS.
replace(vp,
    '''self.generate_dialogue_subtitles_for_duration(
                    sc_beats, clip_dur, srt_path, json_path=json_path,
                    audio_path=muse_clip, language=target_lang)
''',
    '''self.generate_dialogue_subtitles_for_duration(
                    sc_beats, clip_dur, srt_path, json_path=json_path,
                    audio_path=muse_clip, language=target_lang)
                native_qc = json.loads(json_path.read_text(encoding="utf-8"))
                if native_qc.get("script_mismatch"):
                    raise RuntimeError("MUSE_NATIVE_VOICE_SCRIPT_MISMATCH: Muse speech is not identical to scripted dialogue; do not publish or place script subtitles over different speech.")
''')

# In static-image fallback, replace fake evenly distributed word estimates with
# measured audio word timings before burning subtitles.
replace(vp,
    '''        if total_dur <= 0.5:

            total_dur = 8.0



        if not base_img.is_file() or base_img.stat().st_size < 1000:''',
    '''        if total_dur <= 0.5:

            total_dur = 8.0

        if not no_subtitles and subtitle_style not in ("none", "off", "disabled"):
            dialogue_beats = (scene.get("dialogue_beats", []) if isinstance(scene, dict)
                              else scene.dialogue_beats)
            expected_speech = "\\n".join(
                clean_dialogue_text(str(b.get("text", "") if isinstance(b, dict)
                                        else getattr(b, "text", "")))
                for b in dialogue_beats
            ).strip()
            if expected_speech:
                from .native_audio_subtitles import write_native_subtitles
                # Clean isolated dialogue matches timestamps in the mixed master track.
                clean_audio = s_dir / "dialogue_master.wav"
                if not clean_audio.is_file():
                    clean_audio = master_audio
                target_language = ((scene.get("language") if isinstance(scene, dict)
                                    else getattr(scene, "language", None))
                                   or (bible or {}).get("language") or "auto")
                write_native_subtitles(clean_audio, expected_speech, srt_path,
                                       s_dir / "subtitles.json", language=target_language)
                alignment_qc = json.loads((s_dir / "subtitles.json").read_text(encoding="utf-8"))
                if alignment_qc.get("script_mismatch"):
                    raise RuntimeError("DRAMA_TTS_SCRIPT_MISMATCH: Synthesized audio differs from script; review voice output before publishing.")

        if not base_img.is_file() or base_img.stat().st_size < 1000:''')

# Collect references for ALL scene characters, not merely the primary.
mu = "muse_video_provider.py"
replace(mu, 'if not ref_img and scene.get("scene_dir"):', 'if scene.get("scene_dir"):')
replace(mu, 'if prim_anc and prim_anc.is_file():\n                    ref_img = str(prim_anc)',
            'if prim_anc and prim_anc.is_file() and not ref_img:\n                    ref_img = str(prim_anc)')
replace(mu, 'char_anchors = [a["image_path"] for a in all_anc if a.get("image_path")]',
            'char_anchors = list(dict.fromkeys(([ref_img] if ref_img else []) + [a["image_path"] for a in all_anc if a.get("image_path")]))')

gw = "muse_gateway_worker.py"
replace(gw,
    'fingerprint = hashlib.sha256(json.dumps({k: request[k] for k in ("prompt", "width", "height", "duration")}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()',
    '''# Reference image bytes are part of scene identity. Never reuse a clip made with
    # old/absent character pictures under a matching text-only fingerprint.
    anchor_sources = list(dict.fromkeys(list(request.get("character_anchors") or []) +
                                          ([request["reference_image"]] if request.get("reference_image") else [])))
    missing_anchors = [str(p) for p in anchor_sources if not Path(p).is_file()]
    if missing_anchors:
        raise RuntimeError("MUSE_REFERENCE_MISSING: " + ", ".join(missing_anchors))
    signature = {k: request[k] for k in ("prompt", "width", "height", "duration")}
    signature["reference_sha256"] = [digest(str(Path(p))) for p in anchor_sources]
    fingerprint = hashlib.sha256(json.dumps(signature, sort_keys=True, ensure_ascii=False).encode()).hexdigest()''')
replace(gw,
    '''if receipt.get("state") == "complete" and (output.parent / "muse_clip.mp4").is_file() and (output.parent / "muse_clip.mp4").stat().st_size > 1024:
            pass''',
    '''if receipt.get("state") == "complete" and (output.parent / "muse_clip.mp4").is_file() and (output.parent / "muse_clip.mp4").stat().st_size > 1024:
            raise RuntimeError("MUSE_SCENE_REFERENCE_CHANGED: old completed video exists with different script/reference signature; do not silently reuse it.")''')
replace(gw, 'anchor_list = list(request.get("character_anchors") or [])',
            'anchor_list = list(dict.fromkeys(request.get("character_anchors") or []))\n            upload_errors = []')
replace(gw,
    'print(f"[MUSE_ANCHOR_WARN] Could not upload anchor {lp.name}: {anc_up_err}", flush=True)',
    'upload_errors.append(str(anc_up_err))\n                        print(f"[MUSE_ANCHOR_WARN] Could not upload anchor {lp.name}: {anc_up_err}", flush=True)')
replace(gw,
    '''            if remote_anchors:
                primary_anc = remote_anchors[0]''',
    '''            if anchor_list and (upload_errors or len(remote_anchors) != len(anchor_list)):
                receipt["state"] = "failed"
                receipt["terminal_reason"] = "reference_upload_failed"
                atomic_json(receipt_path, receipt)
                raise RuntimeError("MUSE_REFERENCE_UPLOAD_FAILED: required image was not uploaded; no text-only substitute permitted.")
            if remote_anchors:
                receipt["reference_images_uploaded"] = list(remote_anchors)
                atomic_json(receipt_path, receipt)
                primary_anc = remote_anchors[0]''')

# Validate syntax before any write; keep timestamped .bak for safe rollback.
for name, new_text in changes.items():
    compile(new_text, str(ROOT / name), "exec")
stamp = time.strftime("%Y%m%d_%H%M%S")
backup_dir = ROOT.parent / "tools" / "backups" / ("reference_voice_" + stamp)
backup_dir.mkdir(parents=True, exist_ok=True)
for name in changes:
    src = ROOT / name
    dst = backup_dir / name
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
for name, text in changes.items():
    src = ROOT / name
    tmp = src.with_suffix(src.suffix + ".tmp_ref_voice")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(src)
    print(f"PATCHED: {src}")
print("BACKUP:", backup_dir)
print("PATCH_OK: syntax prevalidated; no running processes touched")
