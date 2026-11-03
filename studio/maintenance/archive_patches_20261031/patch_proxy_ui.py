# -*- coding: utf-8 -*-
import sys
import os

sys.stdout.reconfigure(encoding="utf-8")

def patch_index_html():
    path = os.path.join("studio", "web", "index.html")
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()

    # 1. Add Proxy button next to btnModalPasteCookie
    proxy_btn_html = """              <button type="button" class="btn btn-secondary btn-sm" id="btnModalPasteProxy" onclick="openMuseProxyModal()" style="background:#062318;border:1px solid rgba(16,185,129,0.5);color:#34d399;font-weight:700;padding:5px 12px;font-size:0.74rem;border-radius:6px;box-shadow:0 0 10px rgba(16,185,129,0.25);cursor:pointer;display:inline-flex;align-items:center;gap:5px;">
                <span>🌐 Gán Proxy Tự Động</span>
              </button>"""

    target_btn_marker = 'id="btnModalPasteCookie"'
    if target_btn_marker in html and 'id="btnModalPasteProxy"' not in html:
        idx_btn = html.find(target_btn_marker)
        close_btn_idx = html.find("</button>", idx_btn)
        if close_btn_idx != -1:
            insertion_pt = close_btn_idx + len("</button>")
            # check newline
            if html[insertion_pt:insertion_pt+2] == "\r\n":
                html = html[:insertion_pt] + "\r\n" + proxy_btn_html + html[insertion_pt:]
            elif html[insertion_pt:insertion_pt+1] == "\n":
                html = html[:insertion_pt] + "\n" + proxy_btn_html + html[insertion_pt:]
            print("[✓] Added btnModalPasteProxy to index.html")
    else:
        print("[!] btnModalPasteProxy already present or marker not found in index.html")

    # 2. Add modalMuseProxy
    modal_proxy_html = """  <!-- ======================================================== -->
  <!-- MODAL: GÁN PROXY CHO TÀI KHOẢN MUSE AI                    -->
  <!-- ======================================================== -->
  <div class="modal-overlay" id="modalMuseProxy" style="display:none;">
    <div class="modal-dialog" style="max-width:560px;width:92vw;background:#090d16;border:1.5px solid rgba(16,185,129,0.5);border-radius:12px;box-shadow:0 20px 50px rgba(0,0,0,0.95);overflow:hidden;display:flex;flex-direction:column;">
      <div style="padding:10px 16px;border-bottom:1px solid #1e293b;background:linear-gradient(90deg,#064e3b,#0f172a);display:flex;justify-content:space-between;align-items:center;">
        <div style="display:flex;align-items:center;gap:8px;">
          <span style="font-size:1.1rem;">🌐</span>
          <span style="font-size:0.92rem;font-weight:700;color:#fff;">Quản Lý & Tự Động Gán Proxy Cho Tài Khoản Muse</span>
        </div>
        <button class="modal-close" onclick="closeModal(document.getElementById('modalMuseProxy'))" style="font-size:1.2rem;color:#94a3b8;background:transparent;border:none;cursor:pointer;line-height:1;padding:0 4px;" title="Đóng">&times;</button>
      </div>
      <div style="padding:16px;display:flex;flex-direction:column;gap:12px;">
        <div style="background:#062318;border:1px solid rgba(16,185,129,0.3);border-radius:8px;padding:10px 12px;font-size:0.75rem;color:#a7f3d0;line-height:1.5;">
          <b style="color:#34d399;">💡 Cơ chế tự động phân bổ proxy thông minh:</b><br>
          Dán danh sách proxy vào khung bên dưới (mỗi dòng 1 proxy). Hệ thống sẽ tự động gán proxy lần lượt cho từng tài khoản Muse AI. Nếu ít proxy hơn số tài khoản, hệ thống sẽ luân phiên (round-robin) an toàn.
        </div>
        <div>
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;">
            <label style="font-size:0.78rem;font-weight:600;color:#cbd5e1;margin:0;">Danh Sách Proxy (mỗi dòng 1 proxy):</label>
            <span style="font-size:0.7rem;color:#34d399;">Hỗ trợ: ip:port:user:pass, ip:port, http://, socks5://</span>
          </div>
          <textarea id="inMuseProxyRaw" rows="6" placeholder="Ví dụ:&#10;103.149.130.12:8080:user123:pass456&#10;103.149.130.13:8080:user123:pass456&#10;http://user:pass@proxy.example.com:3128" style="width:100%;box-sizing:border-box;background:#030712;border:1px solid #334155;color:#e2e8f0;padding:10px;border-radius:8px;font-family:monospace;font-size:0.75rem;resize:vertical;"></textarea>
        </div>
        <div style="display:flex;justify-content:space-between;align-items:center;margin-top:6px;">
          <button type="button" class="btn btn-outline-danger btn-sm" onclick="clearAllMuseProxies()" style="background:transparent;color:#f87171;border:1px solid rgba(248,113,113,0.4);padding:6px 12px;border-radius:6px;cursor:pointer;font-size:0.75rem;">
            🗑️ Xóa Tất Cả Proxy (Dùng IP Gốc)
          </button>
          <div style="display:flex;gap:8px;">
            <button type="button" class="btn btn-secondary btn-sm" onclick="closeModal(document.getElementById('modalMuseProxy'))" style="background:#1e293b;color:#cbd5e1;border:1px solid #475569;padding:6px 14px;border-radius:6px;cursor:pointer;">Đóng</button>
            <button type="button" class="btn btn-primary btn-sm" id="btnSubmitMuseProxy" onclick="submitMuseProxyPaste()" style="background:#059669;color:#fff;border:none;padding:6px 18px;border-radius:6px;font-weight:700;cursor:pointer;box-shadow:0 0 12px rgba(5,150,105,0.4);display:inline-flex;align-items:center;gap:6px;">
              <span>✓ Tự Động Phân Bổ Proxy</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>\n\n"""

    target_modal_marker = 'id="modalMuseCookiePaste"'
    if target_modal_marker in html and 'id="modalMuseProxy"' not in html:
        idx_m = html.find(target_modal_marker)
        # Find closing tag of modalMuseCookiePaste (two </div>)
        closing_marker = "<!-- ======================================================== -->\n\n\n\n  <!-- MODAL: YOUTUBE"
        if closing_marker not in html:
            closing_marker = "<!-- ======================================================== -->\r\n\r\n\r\n\r\n  <!-- MODAL: YOUTUBE"
        
        if closing_marker in html:
            idx_insert = html.find(closing_marker)
            html = html[:idx_insert] + modal_proxy_html + html[idx_insert:]
            print("[✓] Added modalMuseProxy to index.html")
        else:
            # Fallback: look for id="modalYouTubeAdvancedPublish"
            yt_modal_idx = html.find('id="modalYouTubeAdvancedPublish"')
            if yt_modal_idx != -1:
                # insert right before the nearest preceding comment
                comment_idx = html.rfind("<!--", idx_m, yt_modal_idx)
                if comment_idx != -1:
                    html = html[:comment_idx] + modal_proxy_html + html[comment_idx:]
                    print("[✓] Added modalMuseProxy to index.html (fallback)")
    else:
        print("[!] modalMuseProxy already present or marker not found in index.html")

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


def patch_app_js():
    path = os.path.join("studio", "web", "app.js")
    with open(path, "r", encoding="utf-8") as f:
        js = f.read()

    # 1. Update account card in renderMuseAccounts to display proxy badge
    proxy_badge_code = """            ${acc.proxy ? `
              <div style="font-size:0.65rem;color:#34d399;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:2px;display:flex;align-items:center;gap:4px;">
                <span>🌐</span> <span style="font-family:monospace;background:rgba(16,185,129,0.15);padding:1px 5px;border-radius:4px;border:1px solid rgba(16,185,129,0.3);color:#6ee7b7;">Proxy: ${escapeHtml(acc.proxy)}</span>
              </div>
            ` : `
              <div style="font-size:0.63rem;color:#64748b;margin-top:2px;display:flex;align-items:center;gap:4px;">
                <span>🌐 Direct Home IP</span>
              </div>
            `}"""

    card_marker = "${escapeHtml(acc.id)}</span>"
    if card_marker in js and "Proxy: ${escapeHtml(acc.proxy)}" not in js:
        idx_c = js.find(card_marker)
        idx_div_end = js.find("</div>", idx_c)
        if idx_div_end != -1:
            ins_pt = idx_div_end + len("</div>")
            js = js[:ins_pt] + "\n" + proxy_badge_code + js[ins_pt:]
            print("[✓] Added proxy badge display to account cards in app.js")
    else:
        print("[!] Proxy badge already present or marker not found in app.js")

    # 2. Add JS helper functions at bottom of app.js
    proxy_js_funcs = """

// ==========================================
// MUSE AI PROXY AUTO-MAPPING HANDLERS
// ==========================================

window.openMuseProxyModal = function() {
  const modal = document.getElementById("modalMuseProxy");
  if (!modal) return;
  const input = document.getElementById("inMuseProxyRaw");
  const btn = document.getElementById("btnSubmitMuseProxy");
  if (input) input.value = "";
  if (btn) { btn.disabled = false; btn.innerHTML = "<span>✓ Tự Động Phân Bổ Proxy</span>"; }
  openModal(modal);
};

window.submitMuseProxyPaste = async function() {
  const input = document.getElementById("inMuseProxyRaw");
  const btn = document.getElementById("btnSubmitMuseProxy");
  const raw = input ? input.value.trim() : "";
  if (!raw) {
    showToast("Vui lòng dán ít nhất 1 proxy!", "warning");
    if (input) input.focus();
    return;
  }

  try {
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" style="width:14px;height:14px;border-width:2px;display:inline-block;margin-right:6px;"></span> Đang gán proxy...`;
    }

    const res = await fetch("/api/muse/accounts/import_proxies", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ proxies: raw })
    });

    const data = await res.json();
    if (!res.ok || !data.ok) {
      throw new Error(data.error || "Không gán được proxy.");
    }

    const modal = document.getElementById("modalMuseProxy");
    if (modal) closeModal(modal);

    await loadMuseStatus(true);
    showToast(data.message || `Đã gán proxy cho ${data.assigned_count || 0} tài khoản!`, "success");

  } catch (err) {
    showToast(err.message, "error");
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = "<span>✓ Tự Động Phân Bổ Proxy</span>";
    }
  }
};

window.clearAllMuseProxies = async function() {
  if (!confirm("Bạn có chắc muốn xóa tất cả proxy đã gán? Các tài khoản sẽ quay lại dùng IP trực tiếp của máy.")) {
    return;
  }

  try {
    const res = await fetch("/api/muse/accounts/remove_proxies", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({})
    });

    const data = await res.json();
    if (!res.ok || !data.ok) {
      throw new Error(data.error || "Không xóa được proxy.");
    }

    const modal = document.getElementById("modalMuseProxy");
    if (modal) closeModal(modal);

    await loadMuseStatus(true);
    showToast(data.message || "Đã xóa proxy, tất cả tài khoản dùng IP gốc!", "success");

  } catch (err) {
    showToast(err.message, "error");
  }
};
"""

    if "window.openMuseProxyModal" not in js:
        js = js + proxy_js_funcs
        print("[✓] Added window.openMuseProxyModal, submitMuseProxyPaste, clearAllMuseProxies to app.js")
    else:
        print("[!] Proxy modal functions already present in app.js")

    with open(path, "w", encoding="utf-8") as f:
        f.write(js)


if __name__ == "__main__":
    patch_index_html()
    patch_app_js()
    print("Done patching.")
