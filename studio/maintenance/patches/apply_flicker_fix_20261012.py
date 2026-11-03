from pathlib import Path
import ast,shutil,datetime
root=Path(__file__).resolve().parent
backup=root/"checkpoints"/("flicker_before_"+datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
backup.mkdir(parents=True)
names=["web/app.js","web_server.py","series_studio.py","studio_hand_color.py","studio_color_render.py",
"engine/tools/merge_audio_video.py","engine/tools/video_subtitle.py","engine/tools/concatenate_videos.py"]
for name in names:
    target=backup/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/name,target)
def patch(name,old,new):
    file=root/name;s=file.read_text(encoding="utf-8")
    if s.count(old)!=1:raise RuntimeError("Bad anchor "+name+repr(old[:100]))
    file.write_text(s.replace(old,new),encoding="utf-8")
patch("web/app.js",'  isRunning: false,','  isRunning: false,\n  polling: false,\n  deckSignature: null,\n  logsSignature: null,')
patch("web/app.js",'async function pollStatus() {\n  try {',
'''async function pollStatus() {
  if (state.polling) return;
  state.polling = true;
  try {''')
patch("web/app.js",'''    // If final video is ready and we don't have it loaded yet
    if (data.final_video_url && (!state.loadedEpisodeData || !state.loadedEpisodeData.final_video_url)) {
      loadEpisodeDetails(state.currentSeries, state.currentEpisode);
    }

    // Poll scene details if running or just completed
    if (data.running || data.stage === "COMPLETED") {
      loadEpisodeDetails(state.currentSeries, state.currentEpisode);
    }''',
'''    // One awaited refresh; repeated data preserves the current preview and cards.
    if (data.running || data.stage === "COMPLETED" || data.final_video_url) {
      await loadEpisodeDetails(state.currentSeries, state.currentEpisode);
    }''')
patch("web/app.js",'    console.warn("Poll failed", err);\n  }\n}',
'''    console.warn("Poll failed", err);
  } finally {
    state.polling = false;
  }
}''')
patch("web/app.js",'function renderLogs(lines) {\n  if (!el.logsConsole) return;',
'''function renderLogs(lines) {
  if (!el.logsConsole) return;
  const signature = JSON.stringify(lines);
  if (signature === state.logsSignature) return;
  state.logsSignature = signature;''')
patch("web/app.js",'function renderStoryboardCards(scenes) {',
'''function reconcileStoryboardNodes(container, html) {
  const template = document.createElement("template");
  template.innerHTML = html;
  const wanted = [...template.content.children];
  const ids = new Set(wanted.map(node => node.id));
  for (const child of [...container.children]) {
    if (!ids.has(child.id)) child.remove();
  }
  wanted.forEach((node, index) => {
    const current = [...container.children].find(child => child.id === node.id);
    if (!current) container.insertBefore(node, container.children[index] || null);
    else if (current.outerHTML !== node.outerHTML) current.replaceWith(node);
  });
}

function renderStoryboardCards(scenes) {
  const signature = JSON.stringify([state.currentSeries, state.currentEpisode, scenes]);
  if (signature === state.deckSignature) return;
  state.deckSignature = signature;''')
patch("web/app.js",'src="${sc.image_url}?t=${Date.now()}"','src="${sc.image_url}"')
patch("web/app.js",'  el.scenesContainer.innerHTML = scenes','  const cardsHtml = scenes')
patch("web/app.js",'  // Render Filmstrip Timeline Bar',
'''  reconcileStoryboardNodes(el.scenesContainer, cardsHtml);

  // Render Filmstrip Timeline Bar''')
patch("web/app.js",'    track.innerHTML = scenes','    const timelineHtml = scenes')
patch("web/app.js",'''      .join("");
  }
  if (durText) {''','''      .join("");
    reconcileStoryboardNodes(track, timelineHtml);
  }
  if (durText) {''')
patch("web/app.js",'''  el.cinemaVideo.src = url;
  el.cinemaVideo.load();''',
'''  // Keep a user's playback position and pause state during status polling.
  el.playerTitle.textContent = title;
  el.btnDownloadMp4.href = url;
  if (el.cinemaVideo.getAttribute("src") === url) return;
  el.cinemaVideo.src = url;
  el.cinemaVideo.load();''')
patch("web_server.py",'''            if not ep_dir.exists():
                return self.end_json({"error": "Episode folder not found"}, 404)''',
'''            if not ep_dir.exists():
                ep_dir = PRODUCTIONS_DIR / slug(series_name+" - Offline Test") / f"episode_{ep_num:03d}"
            if not ep_dir.exists():
                return self.end_json({"error": "Episode folder not found"}, 404)''')
# Media URLs change only when the file itself changes, not on every poll.
for var in ("img_p","audio_p","final_clip"):
    patch("web_server.py",f'{var}.relative_to(STUDIO_DIR).as_posix()}}" if {var}.exists()',
          f'{var}.relative_to(STUDIO_DIR).as_posix()}}?v={{{var}.stat().st_mtime_ns}}" if {var}.exists()')
patch("web_server.py",'final_p.relative_to(STUDIO_DIR).as_posix()}" if final_p.exists() else None\n\n            return self.end_json',
    'final_p.relative_to(STUDIO_DIR).as_posix()}?v={final_p.stat().st_mtime_ns}" if final_p.exists() else None\n\n            return self.end_json')
# Hide each renderer/ffprobe/scene subprocess on Windows, without global monkeypatches.
for name in names[1:]:
    path=root/name;source=path.read_bytes();tree=ast.parse(source);lines=source.splitlines(keepends=True)
    starts=[0]
    for line in lines:starts.append(starts[-1]+len(line))
    additions=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute):
            fn=node.func
            if isinstance(fn.value,ast.Name) and fn.value.id=="subprocess" and fn.attr in ("run","Popen"):
                if any(k.arg=="creationflags" for k in node.keywords):continue
                end=starts[node.end_lineno-1]+node.end_col_offset-1
                prior=source[:end].rstrip()
                prefix=b"" if prior.endswith(b",") else b", "
                additions.append((end,prefix+b'creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)'))
    for position,text in sorted(additions,reverse=True):source=source[:position]+text+source[position:]
    compile(source,str(path),"exec")
    path.write_bytes(source)
print("FLICKER_FIX_INSTALLED",backup)
