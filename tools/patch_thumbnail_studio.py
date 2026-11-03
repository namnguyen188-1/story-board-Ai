"""Patch studio/thumbnail_studio.py to clean up slash and refine typography."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
ts_p = ROOT / "studio" / "thumbnail_studio.py"
ts_text = ts_p.read_text(encoding="utf-8")

# Fix slash condition: do not draw blindly on i == len(line_configs) - 1 which causes collisions
old_slash_cond = 'if i == len(line_configs) - 1 or any(kw in line.upper() for kw in ("IMPONE", "ATRAE", "GANARÁS", "CONTROLAR", "RESPETO", "BRILLAR", "VOLVERÁ", "PRIMERO", "HÀNH ĐỘNG", "CHIẾN THẮNG")):'
new_slash_cond = 'if any(kw == line.strip().upper() for kw in ("IMPONE", "ATRAE", "RESPETO")) and i < len(line_configs) - 1:'

if old_slash_cond in ts_text:
    ts_text = ts_text.replace(old_slash_cond, new_slash_cond, 1)
    print("Cleaned up red slash collision in thumbnail_studio.py")
else:
    print("[WARN] old_slash_cond not found")

ts_p.write_text(ts_text, encoding="utf-8")
print("thumbnail_studio.py patched!")
