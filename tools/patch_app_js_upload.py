"""Patch studio/web/app.js for YouTube upload data forwarding with regex."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
app_js_p = ROOT / "studio" / "web" / "app.js"
app_js = app_js_p.read_text(encoding="utf-8")

# 1. Update triggerYouTubeUploadFromMonitor
pat_mon = r'(window\.triggerYouTubeUploadFromMonitor\s*=\s*function\s*\(\)\s*\{[\s\S]*?const\s+chSettings\s*=\s*\(ch\s*&&\s*ch\.publish_settings\)\s*\|\|\s*\{\};[\s\S]*?window\.triggerYouTubeUpload\(\{[\s\S]*?channelId:\s*channelId,)'

rep_mon = r"""window.triggerYouTubeUploadFromMonitor = function () {
  const selCh = document.getElementById("ytQuickChannelSelect");
  const selPriv = document.getElementById("ytQuickPrivacySelect");
  const selPl = document.getElementById("ytQuickPlaylistSelect");
  const channelId = selCh ? selCh.value : "";
  const ch = (window.youTubeState.channels || []).find(c => c.id === channelId);
  const chSettings = (ch && ch.publish_settings) || {};
  const sData = window.currentSeoData;

  window.triggerYouTubeUpload({
    channelId: channelId,
    title: (sData && (sData.best_title || sData.title)) || null,
    description: (sData && sData.description) || null,
    tags: (sData && sData.tags) || null,
    pinnedComment: (sData && sData.pinned_comment) || null,"""

app_js, count1 = re.subn(pat_mon, rep_mon, app_js, count=1)
print(f"[1/3] triggerYouTubeUploadFromMonitor patched: {count1}")

# 2. Update triggerYouTubeUploadFromSeoModal
pat_seo = r'(window\.triggerYouTubeUploadFromSeoModal\s*=\s*function\s*\(\)\s*\{[\s\S]*?const\s+chSettings\s*=\s*\(ch\s*&&\s*ch\.publish_settings\)\s*\|\|\s*\{\};[\s\S]*?window\.triggerYouTubeUpload\(\{[\s\S]*?channelId:\s*channelId,)'

rep_seo = r"""window.triggerYouTubeUploadFromSeoModal = function () {
  const selCh = document.getElementById("seoYtChannelSelect");
  const selPriv = document.getElementById("seoYtPrivacySelect");
  const selPl = document.getElementById("seoYtPlaylistSelect");
  const channelId = selCh ? selCh.value : "";
  const ch = (window.youTubeState.channels || []).find(c => c.id === channelId);
  const chSettings = (ch && ch.publish_settings) || {};
  const sData = window.currentSeoData;

  let activeTitle = null;
  const selTitleEl = document.querySelector("#seoTitlesContainer .title-card.selected, #seoTitlesContainer [data-selected='true']");
  if (selTitleEl && selTitleEl.dataset.title) {
    activeTitle = selTitleEl.dataset.title;
  } else if (sData) {
    activeTitle = sData.best_title || sData.title || null;
  }
  const descEl = document.getElementById("seoDescriptionArea");
  const activeDesc = (descEl && descEl.value.trim()) || (sData && sData.description) || null;
  const tagsEl = document.getElementById("seoTagsInput");
  const activeTags = (tagsEl && tagsEl.value.trim()) || (sData && sData.tags) || null;
  const pinEl = document.getElementById("seoPinnedCommentInput");
  const activePin = (pinEl && pinEl.value.trim()) || (sData && sData.pinned_comment) || null;

  window.triggerYouTubeUpload({
    channelId: channelId,
    title: activeTitle,
    description: activeDesc,
    tags: activeTags,
    pinnedComment: activePin,"""

app_js, count2 = re.subn(pat_seo, rep_seo, app_js, count=1)
print(f"[2/3] triggerYouTubeUploadFromSeoModal patched: {count2}")

# 3. Update triggerYouTubeUpload fallback payload
pat_body = r'pinned_comment:\s*pinnedComment\s*\|\|\s*null,[\s\S]*?title:\s*title\s*\|\|\s*null,[\s\S]*?description:\s*description\s*\|\|\s*null,[\s\S]*?tags:\s*tags\s*\|\|\s*null,'

rep_body = """pinned_comment: pinnedComment || (window.currentSeoData && window.currentSeoData.pinned_comment) || null,
        title: title || (window.currentSeoData && (window.currentSeoData.best_title || window.currentSeoData.title)) || null,
        description: description || (window.currentSeoData && window.currentSeoData.description) || null,
        tags: tags || (window.currentSeoData && window.currentSeoData.tags) || null,"""

app_js, count3 = re.subn(pat_body, rep_body, app_js, count=1)
print(f"[3/3] triggerYouTubeUpload payload fallback patched: {count3}")

app_js_p.write_text(app_js, encoding="utf-8")
print("FINISHED APP.JS PATCH!")
