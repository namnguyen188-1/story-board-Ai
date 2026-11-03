import sys
sys.path.insert(0, 'studio')
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
import shutil

ep_dir = Path("studio/productions/stoi/episode_001")
pub_dir = ep_dir / "00_DANG_BAI_YOUTUBE"

# 1. Update thumbnail_shorts.jpg with the masterpiece 9:16 version
master_shorts = ep_dir / "thumbnail_shorts_masterpiece.jpg"
if master_shorts.is_file():
    shutil.copy2(master_shorts, ep_dir / "thumbnail_shorts.jpg")
    print("Updated thumbnail_shorts.jpg with masterpiece version")

# 2. In 00_DANG_BAI_YOUTUBE:
# For Shorts (9:16 video), 02_THUMBNAIL_CHINH_SEO MUST be the 9:16 vertical cover!
clean_title = "Regalas tu vida a gente que no te importa - La verdad estoica que duele"
main_thumb_dst = pub_dir / f"02_THUMBNAIL_CHINH_SEO - {clean_title}.jpg"
shutil.copy2(master_shorts, main_thumb_dst)
print("Updated 02_THUMBNAIL_CHINH_SEO with 9:16 vertical cover:", main_thumb_dst.name)

# Update 02B_BIA_DOC_SHORTS to match
shorts_thumb_dst = pub_dir / f"02B_BIA_DOC_SHORTS - {clean_title}.jpg"
shutil.copy2(master_shorts, shorts_thumb_dst)

# In 04_CAC_MAU_THUMBNAIL_DU_PHONG, store the 16:9 desktop thumbnail
alt_dir = pub_dir / "04_CAC_MAU_THUMBNAIL_DU_PHONG"
alt_dir.mkdir(parents=True, exist_ok=True)
thumb_16_9 = ep_dir / "thumbnail_seo.jpg"
if thumb_16_9.is_file():
    shutil.copy2(thumb_16_9, alt_dir / "00_Thumbnail_Ngang_16x9_Desktop.jpg")
    print("Copied 16:9 desktop thumbnail to 04_CAC_MAU_THUMBNAIL_DU_PHONG")

# Copy final to artifact folder for user viewing
art_dir = Path("C:/Users/thean/.gemini/antigravity/brain/faeffa04-6f51-4674-aef9-401a741104e3")
shutil.copy2(master_shorts, art_dir / "stoi_ep01_final_shorts_cover.jpg")
print("Copied final 9:16 cover to artifacts: stoi_ep01_final_shorts_cover.jpg")

print("\nFiles in 00_DANG_BAI_YOUTUBE:")
for f in pub_dir.iterdir():
    print(" -", f.name)
