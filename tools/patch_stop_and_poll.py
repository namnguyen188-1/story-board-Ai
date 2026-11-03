from pathlib import Path

app_js = Path(r"D:\STORYBOARD_AI\studio\web\app.js")
text = app_js.read_text(encoding="utf-8")

# 1. Patch pollStatus freshness
old_poll = """    let data = null;
    try {
      const activeRes = await fetch("/active_run_status.json?t=" + Date.now());
      if (activeRes.ok) {
        const candidate = await activeRes.json();
        if (candidate && typeof candidate.running === "boolean" && candidate.running) {
          data = candidate;
        }
      }
    } catch (_) {}"""

new_poll = """    let data = null;
    try {
      const activeRes = await fetch("/active_run_status.json?t=" + Date.now());
      if (activeRes.ok) {
        const candidate = await activeRes.json();
        const isFresh = candidate && candidate.timestamp && (Math.abs(Date.now() - Number(candidate.timestamp)) < 12000);
        if (candidate && typeof candidate.running === "boolean" && candidate.running && isFresh) {
          data = candidate;
        }
      }
    } catch (_) {}"""

if old_poll in text:
    text = text.replace(old_poll, new_poll, 1)
    print("POLL_FRESHNESS_PATCHED")
else:
    print("OLD_POLL_NOT_FOUND")

# 2. Patch stopProduction
old_stop = """async function stopProduction() {

  if (!confirm("Bạn có chắc chắn muốn dừng tiến trình hiện tại?")) return;

  try {

    await fetch("/api/stop", { method: "POST" });

    showToast("Đã gửi lệnh dừng tiến trình");

  } catch (e) {

    console.error(e);

  }

}"""

new_stop = """async function stopProduction() {

  if (!confirm("Bạn có chắc chắn muốn dừng tiến trình hiện tại?")) return;

  try {
    state.isRunning = false;
    setButtonsRunning(false, 0);
    if (el.headerStatusDot) el.headerStatusDot.classList.remove("active", "error");
    if (el.headerStatusText) el.headerStatusText.textContent = "Đã dừng";
    await fetch("/api/stop", { method: "POST" }).catch(() => {});
    await fetch("/api/status/reset", { method: "POST" }).catch(() => {});
    showToast("Đã dừng tiến trình sản xuất");
    setTimeout(pollStatus, 500);
  } catch (e) {
    console.error(e);
  }

}"""

if old_stop in text:
    text = text.replace(old_stop, new_stop, 1)
    print("STOP_PRODUCTION_PATCHED")
else:
    print("OLD_STOP_NOT_FOUND")

app_js.write_text(text, encoding="utf-8")
print("DONE")
