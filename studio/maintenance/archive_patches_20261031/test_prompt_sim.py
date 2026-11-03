# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path

ep_d = Path(r'studio/productions/kh-m-ph/episode_004')
ref_hoa = ep_d / '00_ASSET_PACK' / 'characters' / 'b_h_a_turnaround.jpg'
req = {
    'width': 1280,
    'height': 720,
    'duration': 10,
    'reference_image': str(ref_hoa),
    'character_anchors': [str(ref_hoa)],
    'prompt': 'BÀ HÒA cảnh báo Linh...'
}

remote_anchors = []
for loc_anc in req.get('character_anchors', []):
    lp = Path(loc_anc)
    if lp.is_file():
        rem_p = f'character_anchors/{lp.name}'
        remote_anchors.append(rem_p)

primary_anc = remote_anchors[0]
anchor_instruction = (
    f"MANDATORY IMAGE-TO-VIDEO CHARACTER REFERENCE: The fixed master reference portrait for this scene's focal character is uploaded at: {primary_anc}. "
    f"All cast turnaround sheets are at: {', '.join(remote_anchors)}. "
    "You MUST use this exact reference image as the visual anchor (Image-to-Video). "
    "Strictly lock and preserve the exact facial geometry, eyes, nose, lips, hair, and wardrobe from this reference image in the generated video. "
    "Do NOT generate arbitrary new faces or conflicting clothing. "
)
prompt = f"Run an Image-to-Video scene generation job using the character reference image, ID tag123. {anchor_instruction}\n" + req['prompt']
print("PROMPT SENT TO MUSE FOR BÀ HÒA (SCENE 2):")
print(prompt)
