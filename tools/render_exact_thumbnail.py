"""Render exact Valor Estoico 50/50 masterpiece thumbnail."""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "studio"))
sys.path.insert(0, str(ROOT))

import thumbnail_studio

ep_dir = ROOT / "studio" / "productions" / "Stoic-Philosophy-Full-Guides" / "episode_001"
brain_dir = Path(r"C:\Users\thean\.gemini\antigravity\brain\f09b98eb-8a36-4d31-bf47-3006530bfa18")

base_src = brain_dir / "thumbnail_valor_estoico_base_1793375549303.jpg"
target_base = ep_dir / "thumbnail_valor_estoico_base.jpg"
target_source_frame = ep_dir / "thumbnail_source_frame.jpg"

shutil.copyfile(base_src, target_base)
shutil.copyfile(base_src, target_source_frame)
print(f"Copied base image to {target_base}")

# Render Masterpiece: "TU PAZ / ES LO / PRIMERO"
out_thumb1 = ep_dir / "thumbnail_seo.jpg"
res_path = thumbnail_studio.render_pro_50_50_thumbnail(
    base_image_path=target_base,
    output_path=out_thumb1,
    hook_lines=["TU PAZ", "ES LO", "PRIMERO"],
    genre="stoic",
    subject_side="right"  # character on right, text on left
)
print("Rendered thumbnail_seo.jpg:", res_path)

# Copy to artifacts
artifact_thumb = brain_dir / "valor_estoico_exact_thumbnail.jpg"
shutil.copyfile(out_thumb1, artifact_thumb)
print(f"Copied final thumbnail to {artifact_thumb}")

# Update youtube_publish_pack.json
pack_p = ep_dir / "youtube_publish_pack.json"
if pack_p.exists():
    import json
    data = json.loads(pack_p.read_text(encoding="utf-8"))
    data["thumbnail_file"] = str(out_thumb1)
    data["thumbnail_hook_text"] = "TU PAZ / ES LO / PRIMERO"
    data["best_title"] = "SUELTA LO QUE NO PUEDES CONTROLAR Y LA ANSIEDAD SE IRÁ SOLA | 10 LECCIONES DE ESTOICISMO"
    data["primary_title"] = "SUELTA LO QUE NO PUEDES CONTROLAR Y LA ANSIEDAD SE IRÁ SOLA | 10 LECCIONES DE ESTOICISMO"
    pack_p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Updated youtube_publish_pack.json with competitor title & thumbnail!")
