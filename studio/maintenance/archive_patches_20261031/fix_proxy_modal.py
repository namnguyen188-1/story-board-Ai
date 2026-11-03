# -*- coding: utf-8 -*-
import sys
import os

sys.stdout.reconfigure(encoding="utf-8")

def fix_index_html():
    path = os.path.join("studio", "web", "index.html")
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()

    # Replace style="display:none;" on modalMuseProxy with style="z-index:100060;"
    old_tag = '<div class="modal-overlay" id="modalMuseProxy" style="display:none;">'
    new_tag = '<div class="modal-overlay" id="modalMuseProxy" style="z-index:100060;">'
    if old_tag in html:
        html = html.replace(old_tag, new_tag)
        print("[✓] Fixed modalMuseProxy style to z-index:100060 in index.html")
    else:
        print("[!] old_tag not found in index.html, checking if already updated...")

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


def fix_app_js():
    path = os.path.join("studio", "web", "app.js")
    with open(path, "r", encoding="utf-8") as f:
        js = f.read()

    # 1. Ensure closeModal is defined globally right after closeAllModals
    close_modal_def = """
function closeModal(modal) {
  if (typeof modal === "string") modal = document.getElementById(modal);
  if (modal && modal.classList) {
    modal.classList.remove("open");
  }
}
window.closeModal = closeModal;
"""
    if "window.closeModal = closeModal;" not in js:
        target = "window.closeAllModals = closeAllModals;"
        if target in js:
            js = js.replace(target, target + "\n" + close_modal_def)
            print("[✓] Added window.closeModal to app.js")
    else:
        print("[!] window.closeModal already exists in app.js")

    # 2. Fix openMuseCookiePasteModal so it doesn't close modalMuseManager
    old_cookie_open = '  openModal(modal);\n};'
    new_cookie_open = '  modal.classList.add("open");\n};'
    if old_cookie_open in js:
        js = js.replace(old_cookie_open, new_cookie_open)
        print("[✓] Fixed openMuseCookiePasteModal to stack with modal.classList.add('open')")

    # 3. Fix openMuseProxyModal and add closeMuseProxyModal
    old_proxy_handlers = """window.openMuseProxyModal = function() {
  const modal = document.getElementById("modalMuseProxy");
  if (!modal) return;
  const input = document.getElementById("inMuseProxyRaw");
  const btn = document.getElementById("btnSubmitMuseProxy");
  if (input) input.value = "";
  if (btn) { btn.disabled = false; btn.innerHTML = "<span>✓ Tự Động Phân Bổ Proxy</span>"; }
  openModal(modal);
};"""

    new_proxy_handlers = """window.openMuseProxyModal = function() {
  const modal = document.getElementById("modalMuseProxy");
  if (!modal) return;
  const input = document.getElementById("inMuseProxyRaw");
  const btn = document.getElementById("btnSubmitMuseProxy");
  if (input) input.value = "";
  if (btn) { btn.disabled = false; btn.innerHTML = "<span>✓ Tự Động Phân Bổ Proxy</span>"; }
  modal.classList.add("open");
};

window.closeMuseProxyModal = function() {
  const modal = document.getElementById("modalMuseProxy");
  if (modal) modal.classList.remove("open");
};"""

    if old_proxy_handlers in js:
        js = js.replace(old_proxy_handlers, new_proxy_handlers)
        print("[✓] Fixed openMuseProxyModal to stack and added closeMuseProxyModal")

    with open(path, "w", encoding="utf-8") as f:
        f.write(js)


if __name__ == "__main__":
    fix_index_html()
    fix_app_js()
    print("Done fixing proxy modal behavior.")
