"""Add Google Flow account setup to the actual Studio Pro web desktop UI.
All writes are confined to D:/STORYBOARD_AI/studio.
"""
from pathlib import Path
import shutil,py_compile
home=Path(r"D:\STORYBOARD_AI\studio")
paths=[home/"web_server.py",home/"web"/"index.html",home/"web"/"app.js",home/"mcp_v2_batch.py"]
backup=home/"checkpoints"/"mcp_studio_accounts_20261012"
backup.mkdir(parents=True,exist_ok=True)
for p in paths:shutil.copy2(p,backup/p.name)
def replace_one(s,old,new,tag):
    if old not in s:
        raise RuntimeError("ANCHOR_MISSING "+tag)
    return s.replace(old,new,1)

# The real image worker must use the selected browser/CDP session.
p=home/"mcp_v2_batch.py";s=p.read_text(encoding="utf-8")
s=replace_one(s,
'''    klass,models=preflight()
    if model_index not in (0,1,2):''',
'''    klass,models=preflight()
    from studio_flow_accounts import apply_worker_env
    account = apply_worker_env()
    print("MCP_ACCOUNT_SELECTED",account["name"],flush=True)
    if model_index not in (0,1,2):''',"batch_account")
p.write_text(s,encoding="utf-8")

# HTTP server: account management must happen on localhost, with no credentials.
p=home/"web_server.py";s=p.read_text(encoding="utf-8")
s=replace_one(s,
'''        elif path == "/api/productions":
            productions = []''',
'''        elif path == "/api/mcp/accounts":
            from studio_flow_accounts import accounts
            try:
                return self.end_json(accounts())
            except Exception as exc:
                return self.end_json({"error":"Không đọc được hồ sơ MCP: "+type(exc).__name__},500)

        elif path == "/api/productions":
            productions = []''',"GET_accounts")
s=replace_one(s,
'''        if path == "/api/produce":
            with job_lock:''',
'''        if path == "/api/mcp/account":
            # No cross-site account actions: only requests from this local Studio app.
            origin = self.headers.get("Origin","").rstrip("/")
            if origin and origin not in ("http://127.0.0.1:8765","http://localhost:8765"):
                return self.end_json({"error":"Only local Studio may manage browser profiles."},403)
            from studio_flow_accounts import accounts,create,select,open_login,check,verify
            from auto_studio.storyboard_accounts import AccountError
            action = str(body.get("action") or "")
            identifier = str(body.get("account_id") or "")
            if action not in ("create","select","login","check","verify"):
                return self.end_json({"error":"Unsupported MCP account action"},400)
            if action in ("create","select","login","verify"):
                with job_lock:
                    if job_status["running"]:
                        return self.end_json({"error":"Không đổi hoặc mở tài khoản khi phim đang sản xuất."},409)
            try:
                if action == "create":
                    result = create(body.get("name"))
                elif action == "select":
                    item = select(identifier)
                    result = {"id":item["id"],"name":item["name"]}
                elif action == "login":
                    result = open_login(identifier)
                elif action == "check":
                    result = check(identifier)
                else:
                    result = verify(identifier)
                return self.end_json({"ok":True,"result":result,"account_list":accounts()})
            except (AccountError,ValueError,OSError) as exc:
                return self.end_json({"error":str(exc)[:160]},400)
            except Exception as exc:
                return self.end_json({"error":"MCP account action failed: "+type(exc).__name__},500)

        if path == "/api/produce":
            with job_lock:''',"POST_accounts")
# Don't import V2 module until V2 is on path, use Studio wrapper only.
s=s.replace('''            from auto_studio.storyboard_accounts import AccountError''',
'''            from studio_flow_accounts import base
            AccountError = base.AccountError''')
p.write_text(s,encoding="utf-8")

# Frontend settings: dedicated login in browser, never ask Google passwords.
p=home/"web"/"index.html";s=p.read_text(encoding="utf-8")
s=replace_one(s,
'''title="Cấu hình API & Nền tảng Veo 3"''','''title="Cấu hình API và tài khoản MCP Web Tool"''',"top_title")
s=replace_one(s,
'''        Cài Đặt API''','''        Cài Đặt API & MCP''',"top_button")
s=replace_one(s,
'''                <option value="mcp_v2" selected>⚡ Google Veo 3 Vision (AI Khuyên Dùng)</option>''',
'''                <option value="mcp_v2" selected>🍌 MCP Google Flow — tạo ảnh Nano Banana</option>''',"provider")
s=replace_one(s,
'''              <span>⚡ GOOGLE VEO 3 CONFIGURATION</span>
              <span class="mcp-safe-badge">Ultra HD Engine</span>''',
'''              <span>🍌 MCP GOOGLE FLOW — TẠO ẢNH</span>
              <span class="mcp-safe-badge">Web Tool</span>''',"mcp_label")
s=replace_one(s,
'''                <label for="inMcpModel">Phiên Bản Veo 3</label>
                <select id="inMcpModel">
                  <option value="1" selected>Veo 3 Ultra Turbo (Nhanh & Chuẩn)</option>
                  <option value="0">Veo 3 Pro Cinematic</option>
                  <option value="2">Veo 3 Studio Master</option>
                </select>''',
'''                <label for="inMcpModel">Model tạo ảnh</label>
                <select id="inMcpModel">
                  <option value="1" selected>Nano Banana 2 Lite</option>
                  <option value="0">Nano Banana Pro</option>
                  <option value="2">Nano Banana 2.1</option>
                </select>''',"mcp_models")
s=replace_one(s,
'''          ⚙️ Cấu Hình API Key & Nền Tảng Veo 3''',
'''          ⚙️ Cài đặt API & Tài khoản MCP Web Tool''',"modal_title")
s=replace_one(s,
'''    <div class="modal-dialog">
      <div class="modal-header">
        <h3 style="font-size:1.05rem;color:#ffffff;display:flex;align-items:center;gap:8px;">
          ⚙️ Cài đặt API & Tài khoản MCP Web Tool''',
'''    <div class="modal-dialog" style="max-width:680px;max-height:85vh;overflow-y:auto;">
      <div class="modal-header">
        <h3 style="font-size:1.05rem;color:#ffffff;display:flex;align-items:center;gap:8px;">
          ⚙️ Cài đặt API & Tài khoản MCP Web Tool''',"modal_size")
marker='''        <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:14px;">
          <button class="btn btn-secondary btn-sm modal-close">Đóng</button>'''
add='''        <div id="mcpAccountSection" style="padding:14px 0;border-top:1px solid #334155;margin-top:14px;">
          <div style="font-size:.94rem;color:#fff;font-weight:700;margin-bottom:7px;">
            🌐 Tài khoản Google Flow / MCP Web Tool
          </div>
          <p style="font-size:.76rem;color:#94a3b8;line-height:1.55;margin-bottom:10px;">
            Đăng nhập trong cửa sổ Chrome riêng của tài khoản. Không nhập mật khẩu hay cookie Google vào Studio.
            Tài khoản mới cần được cấp quyền truy cập Web Tool tương ứng.
          </p>
          <div class="field-wrap" style="margin-bottom:9px;">
            <label for="mcpAccountSelect">Tài khoản dùng khi tạo ảnh</label>
            <select id="mcpAccountSelect" style="width:100%;"></select>
          </div>
          <div style="display:flex;flex-wrap:wrap;gap:7px;margin-bottom:11px;">
            <button class="btn btn-primary btn-sm" id="btnMcpOpenLogin">🌐 Mở đăng nhập Google Flow</button>
            <button class="btn btn-secondary btn-sm" id="btnMcpCheckAccount">Kiểm tra trình duyệt</button>
            <button class="btn btn-secondary btn-sm" id="btnMcpVerifyAccount">Xác minh MCP</button>
          </div>
          <div style="display:flex;gap:8px;align-items:center;margin-bottom:6px;">
            <input type="text" id="mcpNewAccountName" placeholder="Tên tài khoản mới (VD: Google Flow 2)"
              style="min-width:0;flex:1;padding:9px;border-radius:6px;background:#0f172a;color:#fff;border:1px solid #475569;">
            <button class="btn btn-secondary btn-sm" id="btnMcpAddAccount">+ Thêm tài khoản</button>
          </div>
          <div id="mcpAccountStatus" role="status"
            style="font-size:.76rem;line-height:1.6;color:#cbd5e1;white-space:pre-line;">
            Chọn tài khoản rồi mở đăng nhập. Chỉ chạy sản xuất khi xác minh MCP thành công.
          </div>
        </div>

'''
s=replace_one(s,marker,add+marker,"mcp_account_ui")
p.write_text(s,encoding="utf-8")

# JS functions: account API calls use actions, no arbitrary URLs or passwords.
p=home/"web"/"app.js";s=p.read_text(encoding="utf-8")
s=replace_one(s,
'''  inGeminiKey: document.getElementById("inGeminiKey"),''',
'''  inGeminiKey: document.getElementById("inGeminiKey"),
  mcpAccountSelect: document.getElementById("mcpAccountSelect"),
  mcpNewAccountName: document.getElementById("mcpNewAccountName"),
  mcpAccountStatus: document.getElementById("mcpAccountStatus"),''',"js_refs")
s=replace_one(s,
'''  loadConfig();
  startStatusPolling();''',
'''  loadConfig();
  loadMcpAccounts();
  startStatusPolling();''',"js_init")
s=replace_one(s,
'''  el.btnSaveKey.addEventListener("click", saveApiKey);''',
'''  el.btnSaveKey.addEventListener("click", saveApiKey);
  document.getElementById("btnMcpOpenLogin").addEventListener("click", () => mcpAccountAction("login"));
  document.getElementById("btnMcpCheckAccount").addEventListener("click", () => mcpAccountAction("check"));
  document.getElementById("btnMcpVerifyAccount").addEventListener("click", () => mcpAccountAction("verify"));
  document.getElementById("btnMcpAddAccount").addEventListener("click", () => mcpAccountAction("create"));
  el.mcpAccountSelect.addEventListener("change", () => mcpAccountAction("select"));''',"js_handlers")
marker='''async function saveApiKey() {'''
add='''async function loadMcpAccounts() {
  if (!el.mcpAccountSelect) return;
  try {
    const res = await fetch("/api/mcp/accounts");
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Không đọc được tài khoản");
    el.mcpAccountSelect.replaceChildren();
    for (const acc of (data.accounts || [])) {
      const option = document.createElement("option");
      option.value = acc.id;
      option.textContent = acc.name + (acc.id === "default" ? " — V2 hiện có" : "");
      el.mcpAccountSelect.appendChild(option);
    }
    el.mcpAccountSelect.value = data.active;
  } catch (error) {
    el.mcpAccountStatus.textContent = "Không thể tải tài khoản MCP: " + error.message;
  }
}
async function mcpAccountAction(action) {
  const id = el.mcpAccountSelect.value;
  const name = el.mcpNewAccountName.value.trim();
  if (action === "create" && !name) {
    el.mcpAccountStatus.textContent = "Nhập tên cho tài khoản Google Flow mới.";
    return;
  }
  el.mcpAccountStatus.textContent = (action === "verify" ?
    "Đang xác minh MCP qua Web Tool (không tạo ảnh)..." : "Đang xử lý tài khoản...");
  try {
    const res = await fetch("/api/mcp/account", {
      method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({action,account_id:id,name})
    });
    const data=await res.json();
    if (!res.ok || !data.ok) throw new Error(data.error || "MCP account request failed");
    if (action==="create") {
      await loadMcpAccounts();
      el.mcpAccountSelect.value=data.result.id;
      el.mcpAccountStatus.textContent="Đã tạo hồ sơ Chrome riêng. Bấm 'Mở đăng nhập' rồi chọn tài khoản mới để sản xuất.";
    } else if (action==="select") {
      await loadMcpAccounts();
      el.mcpAccountStatus.textContent="Đã chọn tài khoản. Kiểm tra MCP trước khi sản xuất.";
    } else if (action==="login") {
      el.mcpAccountStatus.textContent="Đã mở cửa sổ Chrome của tài khoản. Đăng nhập Google trực tiếp trong cửa sổ đó, sau đó bấm 'Xác minh MCP'.";
    } else if (action==="check") {
      const check=data.result;
      el.mcpAccountStatus.textContent=check.connected ?
        "Chrome đã kết nối; chưa chứng minh Google đã đăng nhập. Hãy bấm 'Xác minh MCP'." :
        "Chrome chưa sẵn sàng: "+(check.reason||"hãy mở đăng nhập");
    } else if (action==="verify") {
      el.mcpAccountStatus.textContent=data.result.ok ?
        "MCP Web Tool: xác minh chức năng tạo ảnh THÀNH CÔNG. Không dùng credit trong lần kiểm tra." :
        "MCP chưa sẵn sàng: "+(data.result.reason||"kiểm tra quyền truy cập Web Tool");
    }
  } catch(err) {
    el.mcpAccountStatus.textContent="Lỗi tài khoản MCP: "+err.message;
  }
}

'''
s=replace_one(s,marker,add+marker,"js_account_functions")
s=replace_one(s,
'''        elMcp.textContent = "MCP Web Tool: Sẵn sàng (Đã kết nối)";''',
'''        elMcp.textContent = "MCP đã cài đặt; cần xác minh tài khoản trong phần dưới";''',"js_no_false_login_claim")
p.write_text(s,encoding="utf-8")
for file in (home/"web_server.py",home/"mcp_v2_batch.py",home/"studio_flow_accounts.py"):
    py_compile.compile(str(file),doraise=True)
print("STUDIO_MCP_ACCOUNT_INTEGRATION_COMPILE_PASS")
print("BACKUP",str(backup))
