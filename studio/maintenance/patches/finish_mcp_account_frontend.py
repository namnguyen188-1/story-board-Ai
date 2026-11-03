from pathlib import Path
home=Path(r"D:\STORYBOARD_AI\studio")
p=home/"web"/"app.js"
s=p.read_text(encoding="utf-8")
def replace_one(old,new,label):
    global s
    if old not in s:raise RuntimeError("JS_ANCHOR_MISSING "+label)
    s=s.replace(old,new,1)
replace_one('''  inGeminiKey: document.getElementById("inGeminiKey"),''',
'''  inGeminiKey: document.getElementById("inGeminiKey"),
  mcpAccountSelect: document.getElementById("mcpAccountSelect"),
  mcpNewAccountName: document.getElementById("mcpNewAccountName"),
  mcpAccountStatus: document.getElementById("mcpAccountStatus"),''',"js_refs")
replace_one('''  loadConfig();
  startStatusPolling();''',
'''  loadConfig();
  loadMcpAccounts();
  startStatusPolling();''',"js_init")
replace_one('''  el.btnSaveKey.addEventListener("click", saveApiKey);''',
'''  el.btnSaveKey.addEventListener("click", saveApiKey);
  document.getElementById("btnMcpOpenLogin").addEventListener("click", () => mcpAccountAction("login"));
  document.getElementById("btnMcpCheckAccount").addEventListener("click", () => mcpAccountAction("check"));
  document.getElementById("btnMcpVerifyAccount").addEventListener("click", () => mcpAccountAction("verify"));
  document.getElementById("btnMcpAddAccount").addEventListener("click", () => mcpAccountAction("create"));
  el.mcpAccountSelect.addEventListener("change", () => mcpAccountAction("select"));''',"js_handlers")
replace_one('''async function saveApiKey() {''',
'''async function loadMcpAccounts() {
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

async function saveApiKey() {''',"js_funcs")
replace_one('''        elMcp.textContent = "Google Veo 3 Core: Sẵn sàng (Trực Tuyến)";''',
'''        elMcp.textContent = "MCP đã cài đặt — cần xác minh tài khoản bên dưới";''',"mcp_status_success")
replace_one('''        elMcp.textContent = "Google Veo 3 Core: Chưa kết nối";''',
'''        elMcp.textContent = "MCP chưa được cấu hình đầy đủ";''',"mcp_status_fail")
p.write_text(s,encoding="utf-8")
print("MCP_ACCOUNT_UI_EVENTS_PASS")
