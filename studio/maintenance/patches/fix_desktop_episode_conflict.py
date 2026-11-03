from pathlib import Path
import shutil,py_compile
root=Path(r"D:\STORYBOARD_AI\studio")
server=root/"web_server.py"
client=root/"web"/"app.js"
backup=root/"checkpoints"/"desktop_episode_conflict_20261012"
backup.mkdir(parents=True,exist_ok=True)
for p in (server,client):shutil.copy2(p,backup/p.name)
s=server.read_text(encoding="utf-8")
marker='''                inbox = STUDIO_DIR / "inbox"
                inbox.mkdir(exist_ok=True)'''
assert marker in s,"Backend insertion not found"
insert='''                # Fail early with actionable conflict information BEFORE any API/MCP call.
                # The original episode and its provider assets are never overwritten.
                ep_folder = PRODUCTIONS_DIR / series_slug / f"episode_{episode:03d}"
                old_plan = ep_folder / "plan.json"
                old_job = ep_folder / "scenes" / "scene_0001" / "job.json"
                reason = ""
                if old_job.is_file():
                    try:
                        old_provider = json.loads(old_job.read_text(encoding="utf-8")).get("image_provider", "gemini")
                        if old_provider != img_prov:
                            reason = ("Tập " + str(episode) + " đã dùng nguồn ảnh '" +
                                      str(old_provider) + "'. Không thể trộn nguồn ảnh vào cùng một tập.")
                    except (ValueError, OSError):
                        reason = "Không thể xác minh nguồn ảnh cũ của tập này."
                if not reason and old_plan.is_file():
                    try:
                        cfg = json.loads(old_plan.read_text(encoding="utf-8")).get("config") or {}
                        wanted = {"series": series + (" - Offline Test" if mode == "offline" else ""),
                                  "episode": episode, "prompt": prompt,
                                  "minutes": 0.15 if mode == "offline" else minutes,
                                  "scene_seconds": 5 if mode == "offline" else scene_sec,
                                  "language": language, "model": model, "mode": mode}
                        changes = [k for k,v in wanted.items() if cfg.get(k)!=v]
                        if changes:
                            reason = ("Tập " + str(episode) +
                                      " đã có kịch bản với thông số khác (" +
                                      ", ".join(changes[:4]) + ").")
                    except (ValueError, OSError):
                        reason = "Không thể đọc kế hoạch sản xuất của tập này."
                if reason:
                    next_ep = max(episode+1, 1)
                    for _ in range(9999):
                        p = PRODUCTIONS_DIR / series_slug / f"episode_{next_ep:03d}"
                        if not p.exists():
                            break
                        next_ep += 1
                    return self.end_json({
                        "code": "EPISODE_CONFLICT",
                        "error": reason + " Dữ liệu cũ được giữ nguyên.",
                        "next_episode": next_ep,
                        "resolution": "Chuyển sang tập mới hoặc đổi tên bộ phim."
                    },409)

'''
s=s.replace(marker,insert+marker,1)
server.write_text(s,encoding="utf-8")
t=client.read_text(encoding="utf-8")
start=t.index('''    if (res.status === 409) {
      alert("Đang có tiến trình sản xuất đang chạy!");
      return;
    }''')
end=t.index('''    state.currentSeries = series;''',start)
t=t[:start]+'''    if (res.status === 409 && data.code === "EPISODE_CONFLICT") {
      setButtonsRunning(false);
      const next = Number(data.next_episode);
      const text = data.error + "\\n\\nBạn muốn thử ở Tập " + next +
          " (giữ nguyên Tập " + episode + ") không?";
      if (Number.isInteger(next) && next > episode && confirm(text)) {
        el.inEpisode.value = String(next);
        showToast("Đã chuyển sang Tập " + next +
                  ". Bấm Sản Xuất để bắt đầu an toàn.");
      }
      return;
    }
    if (!res.ok || data.status !== "STARTED") {
      throw new Error(data.error || "Máy chủ trả lỗi HTTP " + res.status);
    }
'''+t[end:]
client.write_text(t,encoding="utf-8")
py_compile.compile(str(server),doraise=True)
print("DESKTOP_WEB_BACKEND_EARLY_CONFLICT_PASS")
print("WEB_GUI_SAFE_EPISODE_SUGGESTION_PASS")
print("BACKUP",str(backup))
