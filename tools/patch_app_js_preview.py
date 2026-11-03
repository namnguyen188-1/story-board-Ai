from pathlib import Path

app_js = Path(r"D:\STORYBOARD_AI\studio\web\app.js")
text = app_js.read_text(encoding="utf-8")

old_snippet = """    if (imgThumb) {
      const { series: curSeries, episode: curEp } = getActiveSeriesAndEpisode();
      const thumbUrl = window.currentSeoData.thumbnail_url || (curSeries ? `/api/productions/${encodeURIComponent(curSeries)}/episodes/${curEp || 1}/thumbnail?t=${Date.now()}` : "");
      if (thumbUrl) imgThumb.src = thumbUrl;
    }"""

new_snippet = """    if (imgThumb) {
      const { series: curSeries, episode: curEp } = getActiveSeriesAndEpisode();
      const thumbUrl = window.currentSeoData.thumbnail_url || (curSeries ? `/api/productions/${encodeURIComponent(curSeries)}/episodes/${curEp || 1}/thumbnail?t=${Date.now()}` : "");
      if (thumbUrl) imgThumb.src = thumbUrl;
    }
    const previewUrlEl = document.getElementById("advYtPreviewVideoUrl");
    if (previewUrlEl) {
      const vidLink = window.currentSeoData.youtube_watch_url || window.currentSeoData.video_url;
      if (vidLink && vidLink.includes("http")) {
        previewUrlEl.innerText = vidLink;
      }
    }"""

if old_snippet in text:
    text = text.replace(old_snippet, new_snippet, 1)
    app_js.write_text(text, encoding="utf-8")
    print("PATCHED_APP_JS_PREVIEW_URL")
else:
    print("OLD_SNIPPET_NOT_FOUND")
