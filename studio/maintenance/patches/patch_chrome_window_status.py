from pathlib import Path
import shutil,datetime,py_compile
root=Path(r"D:\STORYBOARD_AI\studio")
p=root/"studio_flow_accounts.py"
js=root/"web"/"app.js"
backup=root/"checkpoints"/("chrome_window_status_"+datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
backup.mkdir(parents=True,exist_ok=True)
shutil.copy2(p,backup/p.name)
shutil.copy2(js,backup/js.name)
s=p.read_text(encoding="utf-8")
old='''def check(identifier):
    return base.connection_check(identifier,HOME)'''
new='''def check(identifier):
    state=base.connection_check(identifier,HOME)
    account=base.find_account(identifier,HOME)
    visible=bool(account and _visible_chrome_window(base._pid_browser_for_account(account)))
    state["window_visible"]=visible
    if state.get("connected") and not visible:
        state["reason"]="CHROME_CONNECTED_BUT_WINDOW_HIDDEN"
    return state'''
assert old in s
p.write_text(s.replace(old,new,1),encoding="utf-8")
t=js.read_text(encoding="utf-8")
old='''      el.mcpAccountStatus.textContent=check.connected ?
        "Phiên duyệt đã kết nối. Hãy bấm 'Xác minh Veo 3 Core'." :
        "Phiên duyệt chưa sẵn sàng: "+(check.reason||"hãy mở xác thực");'''
new='''      el.mcpAccountStatus.textContent=check.connected && check.window_visible ?
        "Chrome Google Flow đang hiển thị. Sau khi đăng nhập, bấm Xác minh MCP tạo ảnh." :
        check.connected ?
        "Chrome đang chạy ngầm nhưng không có cửa sổ hiển thị. Bấm Mở đăng nhập Google Flow để khôi phục." :
        "Chrome chưa kết nối: "+(check.reason||"hãy mở đăng nhập");'''
assert old in t
js.write_text(t.replace(old,new,1),encoding="utf-8")
py_compile.compile(str(p),doraise=True)
print("BROWSER_VISIBILITY_STATUS_PATCH_PASS",backup,flush=True)
