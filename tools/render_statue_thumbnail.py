"""Render the ultimate Stoic Statue Masterpiece Thumbnail."""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "studio"))
sys.path.insert(0, str(ROOT))

import thumbnail_studio

ep_dir = ROOT / "studio" / "productions" / "Stoic-Philosophy-Full-Guides" / "episode_001"
brain_dir = Path(r"C:\Users\thean\.gemini\antigravity\brain\f09b98eb-8a36-4d31-bf47-3006530bfa18")

base_src = brain_dir / "thumbnail_stoic_statue_exact_base_1793376683467.jpg"
target_base = ep_dir / "thumbnail_valor_estoico_base.jpg"
target_source_frame = ep_dir / "thumbnail_source_frame.jpg"

shutil.copyfile(base_src, target_base)
shutil.copyfile(base_src, target_source_frame)
print(f"Copied statue base to {target_base}")

# Render Masterpiece with exact yellow-white-yellow typography
out_thumb = ep_dir / "thumbnail_seo.jpg"
thumbnail_studio.LOCKED_THUMBNAIL_GENRE_PRESETS["stoic"]["accent_color"] = (255, 230, 0)

thumbnail_studio.render_pro_50_50_thumbnail(
    base_image_path=target_base,
    output_path=out_thumb,
    hook_lines=["TU PAZ", "ES LO", "PRIMERO"],
    genre="stoic",
    subject_side="right"
)
print(f"Rendered masterpiece thumbnail to {out_thumb}")

# Copy to artifacts
artifact_final = brain_dir / "exact_stoic_statue_masterpiece_thumbnail.jpg"
shutil.copyfile(out_thumb, artifact_final)
print(f"Copied final artifact to {artifact_final}")

# Sync to 00_DANG_BAI_YOUTUBE
out_dir = ep_dir / "00_DANG_BAI_YOUTUBE"
if out_dir.exists():
    for f in out_dir.glob("02_THUMBNAIL_CHINH_SEO*.jpg"):
        try:
            shutil.copyfile(out_thumb, f)
            print("Synced to 00_DANG_BAI_YOUTUBE:", f.name)
        except shutil.SameFileError:
            pass

# Update youtube_publish_pack.json
pack_p = ep_dir / "youtube_publish_pack.json"
if pack_p.exists():
    import json
    data = json.loads(pack_p.read_text(encoding="utf-8"))
    data["thumbnail_file"] = str(out_thumb)
    data["thumbnail_hook_text"] = "TU PAZ / ES LO / PRIMERO"
    data["best_title"] = "SUELTA LO QUE NO PUEDES CONTROLAR Y LA ANSIEDAD SE IRÁ SOLA | 10 LECCIONES DE ESTOICISMO"
    data["primary_title"] = "SUELTA LO QUE NO PUEDES CONTROLAR Y LA ANSIEDAD SE IRÁ SOLA | 10 LECCIONES DE ESTOICISMO"
    pack_p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Updated youtube_publish_pack.json!")
