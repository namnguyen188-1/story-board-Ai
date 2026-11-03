import re
from pathlib import Path

# 1. Patch studio/web/app.js
app_path = Path("studio/web/app.js")
content = app_path.read_text(encoding="utf-8")

# Fix 1: Completely hide the redundant bottom thumbnail gallery from 16:9 tab
# In renderSeoPackageUI:
old_gal = """  const gal = document.getElementById("seoThumbnailGallery");
  const galSection = gal ? gal.parentElement : null;
  if (gal) gal.innerHTML = "";

  // Strictly filter only 16:9 widescreen thumbnails! Exclude any vertical Shorts thumbnail!
  const valid16x9Options = (data.thumbnail_options || []).filter(opt => {
    const f = ((opt.file || "") + " " + (opt.url || "") + " " + (opt.label || "")).toLowerCase();
    return !f.includes("short") && !f.includes("9:16") && !f.includes("dọc");
  });

  if (galSection) {
    galSection.style.display = valid16x9Options.length ? "block" : "none";
  }"""

new_gal = """  const gal = document.getElementById("seoThumbnailGallery");
  const galSection = gal ? gal.parentElement : null;
  if (gal) gal.innerHTML = "";
  // Strictly hide bottom redundant gallery - keep 16:9 Tab 100% focused on main 16:9 thumbnail
  if (galSection) {
    galSection.style.display = "none";
  }"""

if old_gal in content:
    content = content.replace(old_gal, new_gal)
    print("Fixed thumbnail gallery hiding in app.js")
else:
    print("WARNING: old_gal pattern not matched")

# Fix 2: In populateAdvYtModal, do not let shorts_package hijack 16:9 uploads
old_isshort = """  const isShort = !!(sData.is_short || sData.is_vertical_short || (sData.shorts_package && Object.keys(sData.shorts_package).length > 0));"""
new_isshort = """  const isShort = window.currentSeoTab === "short" || (!!(sData.is_short || sData.is_vertical_short) && window.currentSeoTab !== "long");"""

if old_isshort in content:
    content = content.replace(old_isshort, new_isshort)
    print("Fixed isShort resolution in populateAdvYtModal")
else:
    print("WARNING: old_isshort pattern not matched")

# Fix 3: In switchSeoPackTab('short'), ensure renderShortsPackageUI is always called and fetches fresh data if missing
old_switch = """    if (shortContent) shortContent.style.display = "flex";
    if (typeof window.renderShortsPackageUI === "function") {
      window.renderShortsPackageUI(window.currentSeoData || state.currentSeoData);
    }"""

new_switch = """    if (shortContent) shortContent.style.display = "flex";
    if (typeof window.renderShortsPackageUI === "function") {
      window.renderShortsPackageUI(window.currentSeoData || state.currentSeoData);
    }
    if (!window.currentSeoData || !window.currentSeoData.shorts_package) {
      fetch(`/api/episode/seo?series=${encodeURIComponent(seriesName)}&episode=${epNum}`)
        .then(r => r.json())
        .then(d => {
          if (d && !d.error) {
            window.currentSeoData = d;
            if (typeof window.renderShortsPackageUI === "function") window.renderShortsPackageUI(d);
          }
        }).catch(err => console.warn("Auto-fetch shorts SEO:", err));
    }"""

if old_switch in content:
    content = content.replace(old_switch, new_switch)
    print("Fixed switchSeoPackTab('short') in app.js")
else:
    print("WARNING: old_switch pattern not matched")

app_path.write_text(content, encoding="utf-8")

# 2. Patch studio/web/index.html to ensure default display of galSection is none
idx_path = Path("studio/web/index.html")
idx_content = idx_path.read_text(encoding="utf-8")

old_sec = """          <!-- 4+ BẢN THUMBNAIL ĐIỆN ẢNH CHUẨN CAO CẤP -->
          <div style="margin-top:14px;padding-top:12px;border-top:1px solid #1e293b;">"""

new_sec = """          <!-- 4+ BẢN THUMBNAIL ĐIỆN ẢNH CHUẨN CAO CẤP -->
          <div style="margin-top:14px;padding-top:12px;border-top:1px solid #1e293b;display:none;">"""

if old_sec in idx_content:
    idx_content = idx_content.replace(old_sec, new_sec)
    print("Fixed index.html thumbnail gallery container display:none")

idx_path.write_text(idx_content, encoding="utf-8")
print("Done patching web UI!")
