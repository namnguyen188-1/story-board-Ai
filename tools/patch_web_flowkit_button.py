from pathlib import Path

def patch():
    # 1. Patch studio/web/index.html
    html_path = Path("studio/web/index.html")
    h_text = html_path.read_text(encoding="utf-8")
    
    btn_target = '<button class="btn btn-primary btn-xs" id="btnFlowLogin"'
    btn_insert = '''<button class="btn btn-warning btn-xs" id="btnInstallFlowKit" type="button" style="display:none;align-items:center;gap:4px;height:24px;padding:0 8px;font-size:0.68rem;font-weight:600;white-space:nowrap;background:linear-gradient(135deg,#f59e0b,#d97706);color:#fff;border:none;">
              🚀 Cài Đặt Động Cơ FlowKit
            </button>
            <button class="btn btn-primary btn-xs" id="btnFlowLogin"'''
    
    if btn_target in h_text and 'id="btnInstallFlowKit"' not in h_text:
        h_text = h_text.replace(btn_target, btn_insert, 1)
        html_path.write_text(h_text, encoding="utf-8")
        print("SUCCESS: studio/web/index.html patched with btnInstallFlowKit")
    else:
        print("INFO: index.html already contains btnInstallFlowKit or target not found")

    # 2. Patch studio/web/app.js
    app_path = Path("studio/web/app.js")
    js_text = app_path.read_text(encoding="utf-8")

    # Hook into refreshAutoFlowStatus
    js_target = 'node.textContent = data.badge_text || (data.connected ? "🟢 Sẵn sàng" : "🟡 Chờ đăng nhập");'
    js_replacement = '''node.textContent = data.badge_text || (data.connected ? "🟢 Sẵn sàng" : "🟡 Chờ đăng nhập");
    const btnInstallFk = document.getElementById("btnInstallFlowKit");
    const btnFlowLoginEl = document.getElementById("btnFlowLogin");
    const btnFlowAddEl = document.getElementById("btnFlowAddAccount");
    if (btnInstallFk) {
      if (data.flowkit_installed === false) {
        btnInstallFk.style.display = "inline-flex";
        if (btnFlowLoginEl) btnFlowLoginEl.style.display = "none";
        if (btnFlowAddEl) btnFlowAddEl.style.display = "none";
      } else {
        btnInstallFk.style.display = "none";
        if (btnFlowLoginEl) btnFlowLoginEl.style.display = "inline-flex";
        if (btnFlowAddEl) btnFlowAddEl.style.display = "inline-flex";
      }
    }'''

    if js_target in js_text and 'btnInstallFlowKit' not in js_text:
        js_text = js_text.replace(js_target, js_replacement, 1)

        # Also add click event listener for btnInstallFlowKit
        listener_target = 'const btnFlowAdd = document.getElementById("btnFlowAddAccount");'
        listener_insert = '''const btnInstallFkAction = document.getElementById("btnInstallFlowKit");
  if (btnInstallFkAction) {
    btnInstallFkAction.addEventListener("click", async () => {
      btnInstallFkAction.disabled = true;
      btnInstallFkAction.textContent = "⏳ Đang kết nối...";
      const statusBox = document.getElementById("mcpAccountStatus");
      if (statusBox) statusBox.textContent = "Đang bắt đầu tải và cài đặt động cơ FlowKit...";
      try {
        await fetch("/api/flowkit/install_engine", { method: "POST" });
        const timer = setInterval(async () => {
          try {
            const res = await fetch("/api/flowkit/install_status");
            const st = await res.json();
            btnInstallFkAction.textContent = `⏳ ${st.percent || 0}%`;
            if (statusBox) statusBox.textContent = st.message || "Đang cài đặt động cơ...";
            if (st.success) {
              clearInterval(timer);
              btnInstallFkAction.disabled = false;
              btnInstallFkAction.textContent = "🚀 Cài Đặt Động Cơ FlowKit";
              if (typeof showToast === "function") showToast("Đã cài đặt thành công động cơ FlowKit!");
              await refreshAutoFlowStatus();
            } else if (st.error) {
              clearInterval(timer);
              btnInstallFkAction.disabled = false;
              btnInstallFkAction.textContent = "⚠️ Thử Lại Cài Đặt";
              if (statusBox) statusBox.textContent = "Lỗi cài đặt: " + st.error;
            }
          } catch (_) {}
        }, 1500);
      } catch (e) {
        btnInstallFkAction.disabled = false;
        btnInstallFkAction.textContent = "🚀 Cài Đặt Động Cơ FlowKit";
        if (statusBox) statusBox.textContent = "Lỗi kích hoạt cài đặt: " + e.message;
      }
    });
  }

  const btnFlowAdd = document.getElementById("btnFlowAddAccount");'''
        
        js_text = js_text.replace(listener_target, listener_insert, 1)
        app_path.write_text(js_text, encoding="utf-8")
        print("SUCCESS: studio/web/app.js patched with btnInstallFlowKit handler")
    else:
        print("INFO: app.js already contains btnInstallFlowKit or target not found")

if __name__ == "__main__":
    patch()
