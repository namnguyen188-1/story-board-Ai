import json,pathlib,re,shutil,subprocess
root=pathlib.Path(r"D:\STORYBOARD_AI\studio");cp=root/"runtime/mcp_v2_only_20261108_102327"
for name in ["app.js","index.html"]:shutil.copy2(root/"web"/name,cp/name)
p=root/"web/app.js";s=p.read_text(encoding="utf-8-sig")
# All current/default image-provider payloads now use MCP V2.
s=s.replace('"flowkit"','"mcp_v2"')
s=s.replace('el.inImageSource.value === "mcp_v2" || el.inImageSource.value === "mcp_v2"','el.inImageSource.value === "mcp_v2"')
s=s.replace('"/api/flowkit/status"','"/api/flow/status"')
s=s.replace('FlowKit đã cài','MCP V2 đã kết nối')
a=s.index("function updateFlowKitUI(data) {");b=s.index("\nasync function refreshAutoFlowStatus",a)
s=s[:a]+'''function updateFlowKitUI(data) {
  const ready = Boolean(data && data.ready);
  const connected = Boolean(data && data.connected);
  const label = data?.badge_text || (connected ? "MCP V2: đã kết nối" : "MCP V2: chưa kết nối");
  const color = ready ? "#10b981" : "#fbbf24";
  for (const id of ["flowkitLiveStatusBadge", "statusFlowKit", "autoFlowManagerStatus"]) {
    const node = document.getElementById(id);
    if (node) { node.textContent = label; node.style.color = color; }
  }
  const box = document.getElementById("flowkitStatusBox");
  if (box) box.textContent = data?.status_text || "Kiểm tra kết nối MCP V2.";
  const cardChrome = document.getElementById("fkCardChrome");
  if (cardChrome) cardChrome.textContent = connected ? "MCP V2 · Chrome đã kết nối" : "MCP V2 · cần kết nối Chrome";
  const install = document.getElementById("btnInstallFlowKit");
  if (install) install.style.display = "none";
}
'''+s[b:]
p.write_text(s,encoding="utf-8")
p=root/"web/index.html";h=p.read_text(encoding="utf-8-sig")
a=h.index('<select id="inImageSource">');b=h.index("</select>",a)
block=h[a:b].replace('<option value="flowkit">Veo 3</option>','<option value="mcp_v2" selected>Google Flow · MCP V2</option>').replace('<option value="comfyui" selected>','<option value="comfyui">')
h=h[:a]+block+h[b:]
h=h.replace('FlowKit WebTool','Google Flow · MCP V2').replace('(FlowKit)','(MCP V2)').replace('Online (18110)','MCP V2 · đang kiểm tra')
for id in ["btnInstallFlowKit","btnFlowKitOpenLogin","btnFlowKitCheckStatus","btnFlowKitRestartDaemon"]:
    h=re.sub(r'<button\b[^>]*\bid="'+id+r'"[^>]*>.*?</button>',"",h,flags=re.S)
p.write_text(h,encoding="utf-8")
check=subprocess.run([r"C:\Program Files\nodejs\node.exe","--check",str(root/"web/app.js")],capture_output=True,text=True)
if check.returncode:
    for name in ["app.js","index.html"]:shutil.copy2(cp/name,root/"web"/name)
    raise RuntimeError(check.stderr)
test=subprocess.run([r"C:\Program Files\nodejs\node.exe",str(root/"tests/test_mcp_v2_status_ui.cjs")],capture_output=True,text=True,encoding="utf-8",errors="replace")
print(test.stdout+test.stderr)
assert test.returncode==0
for name in ["app.js","index.html"]:shutil.copy2(root/"web"/name,cp/"after"/name)
report=json.loads((cp/"migration_result.json").read_text());report["files"]+=["web/app.js","web/index.html"];report["ui_states"]="3/3 Node VM; visual browser unavailable"
(cp/"migration_result.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print("WEB_UI_MCP_V2_DEFAULT_AND_PAYLOADS_UPDATED")
