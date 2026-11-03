import re
from pathlib import Path

# 1. Patch studio/seo_packager.py
p1 = Path("studio/seo_packager.py")
content1 = p1.read_text(encoding="utf-8")

# Fix is_vertical_short_episode
old_cand = 'for img_cand in (root / "thumbnail_source_frame.jpg", root / "thumbnail_shorts.jpg"):'
new_cand = 'for img_cand in (root / "thumbnail_source_frame.jpg",):'
if old_cand in content1:
    content1 = content1.replace(old_cand, new_cand)
    print("Patched is_vertical_short_episode in seo_packager.py")

# Fix thumbnail_options in 16:9 - NEVER include shorts_file in 16:9 thumbnail_options
old_opts = "opts.append({'file': shorts_file.name, 'scene': selection['scene_number'], 'url': _media_url(shorts_file), 'label': 'Bìa dọc Shorts 9:16 (Dự phòng)'})"
new_opts = "# Strictly isolated: Never append 9:16 Shorts to 16:9 options"
if old_opts in content1:
    content1 = content1.replace(old_opts, new_opts)
    print("Removed shorts thumbnail option from 16:9 options in seo_packager.py")

p1.write_text(content1, encoding="utf-8")

# 2. Patch studio/seo_quality.py
p2 = Path("studio/seo_quality.py")
content2 = p2.read_text(encoding="utf-8")
old_opts2 = "package['thumbnail_options']=options[:1]"
new_opts2 = "package['thumbnail_options']=[opt for opt in options if 'short' not in str(opt.get('file','')).lower() and '9:16' not in str(opt.get('label','')).lower()][:1]"
if old_opts2 in content2:
    content2 = content2.replace(old_opts2, new_opts2)
    print("Patched seo_quality.py to exclude shorts from 16:9 options")
p2.write_text(content2, encoding="utf-8")

print("All python SEO files patched successfully!")
