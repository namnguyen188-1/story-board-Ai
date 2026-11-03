from pathlib import Path

app_js = Path(r"D:\STORYBOARD_AI\studio\web\app.js")
text = app_js.read_text(encoding="utf-8")

target = """    const res = await fetch("/api/status");

    if (!res.ok) throw new Error(`Status endpoint returned HTTP ${res.status}`);

    const data = await res.json();"""

replacement = """    let data = null;
    try {
      const activeRes = await fetch("/active_run_status.json?t=" + Date.now());
      if (activeRes.ok) {
        const candidate = await activeRes.json();
        if (candidate && typeof candidate.running === "boolean" && candidate.running) {
          data = candidate;
        }
      }
    } catch (_) {}

    if (!data) {
      const res = await fetch("/api/status");
      if (!res.ok) throw new Error(`Status endpoint returned HTTP ${res.status}`);
      data = await res.json();
    }"""

if target in text:
    text = text.replace(target, replacement, 1)
    app_js.write_text(text, encoding="utf-8")
    print("PATCH_APPLIED_SUCCESSFULLY")
else:
    print("TARGET_NOT_FOUND")
