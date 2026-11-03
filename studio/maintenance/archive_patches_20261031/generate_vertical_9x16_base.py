import sys
sys.path.insert(0, 'studio')
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
import mcp_v2_images

out_path = Path("studio/productions/stoi/episode_001/thumbnail_vertical_9x16_base.jpg")

prompt = (
    "Vertical 9:16 mobile YouTube Shorts masterpiece cover image: "
    "monumental, heroic Roman emperor philosopher statue (Marcus Aurelius), "
    "towering composition from the waist up, muscular chiseled stone chest and torso filling the bottom half of the frame, "
    "stern, intense brooding face with exquisitely sculpted beard and piercing eyes located in the upper-middle of the frame, "
    "the stone chest and lower torso provide an expansive dark surface, "
    "dramatic dark stormy night sky with swirling ominous storm clouds and subtle lightning rim lighting, "
    "high-contrast chiaroscuro lighting accentuating muscular anatomy and carved stone cracks, "
    "8k resolution, cinematic, photorealistic, no text, no watermark, perfectly framed in 9:16 vertical ratio."
)

print("Generating native 9:16 vertical thumbnail base with Flow MCP...")
try:
    mcp_v2_images.make_image(
        prompt=prompt,
        output_path=out_path,
        series="stoi",
        episode=1,
        scene=998,
        max_new_images=10,
        model_index=1,
        aspect_ratio="9:16"
    )
    print(f"Generated successfully: {out_path} (size: {out_path.stat().st_size} bytes)")
except Exception as e:
    print(f"Error: {e}")
