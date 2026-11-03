"""Studio MCP account UX fix - atomic checkpoints, V2 read-only.

After adding a profile: auto-select + open its OWN Chrome account for sign-in.
New profile opens Flow HOME, never another account's fixed Flow project.
"""
from pathlib import Path
import shutil,py_compile,datetime
root=Path(r"D:\STORYBOARD_AI\studio")
files=[root/"studio_flow_accounts.py",root/"web_server.py",root/"web"/"app.js",root/"web"/"index.html"]
cp=root/"checkpoints"/("mcp_account_login_fix_"+datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
cp.mkdir(parents=True,exist_ok=True)
for i,p in enumerate(files):shutil.copy2(p,cp/(str(i)+"_"+p.name))
def sub(path,pairs):
    s=path.read_text(encoding="utf-8")
    for label,old,new in pairs:
        if old not in s:
            raise ValueError("ANCHOR_MISSING "+path.name+" "+label)
        s=s.replace(old,new,1)
    path.write_text(s,encoding="utf-8")

sub(files[0],[
    ("subprocess_import","import os,sys,uuid,socket","import os,sys,uuid,socket,subprocess"),
    ("open_login",'''def open_login(identifier):
    return base.open_account_login(identifier,HOME)''',
'''def open_login(identifier):
    """User-triggered browser login. Never touch cookies or Google passwords.

    The new-account route must NOT be the hard-coded V2 project belonging
    to another Google identity. Users first sign in on Flow homepage.
    Access to the existing MCP tool is verified separately.
    """
    account=base.find_account(identifier,HOME)
    if account is None:
        raise base.AccountError("STORYBOARD_ACCOUNT_NOT_FOUND")
    if identifier=="default":
        return base.open_account_login(identifier,HOME)
    base._require_idle(HOME)
    chrome=base._chrome_path()
    if not chrome.is_file():
        raise base.AccountError("GOOGLE_CHROME_NOT_INSTALLED")
    observed=base.browser_probe(account)
    existing=base._pid_browser_for_account(account)
    if observed["connected"]:
        if not existing:
            raise base.AccountError("CHROME_PROFILE_PORT_IN_USE_BY_OTHER_PROCESS")
        base._show_window(existing)
        base.mark_manual_login(identifier,HOME)
        return {"opened":True,"reused":True,"account":identifier,
                "browser":"Google Flow","signin_required":True}
    if existing:
        raise base.AccountError("CHROME_PROFILE_ALREADY_RUNNING_WITHOUT_DEBUG_CONNECTION")
    Path(account["user_data_dir"]).mkdir(parents=True,exist_ok=True)
    subprocess.Popen([
        str(chrome),
        "--remote-debugging-port="+str(account["cdp_port"]),
        "--user-data-dir="+str(account["user_data_dir"]),
        "--profile-directory=Default",
        "--no-first-run","--no-default-browser-check",
        "--window-size=900,780","--window-position=80,70",
        "--app=https://flow.google.com/"
    ],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
      creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
    base.mark_manual_login(identifier,HOME)
    return {"opened":True,"reused":False,"account":identifier,
            "browser":"Google Flow","signin_required":True}''')
])
sub(files[1],[
    ("auto_login_new_account",'''                if action == "create":
                    result = create(body.get("name"))
                    select(result["id"])  # New Studio profile is active immediately.
                elif action == "select":''',
'''                if action == "create":
                    result = create(body.get("name"))
                    select(result["id"])  # New Studio profile is active immediately.
                    # A newly created profile is NOT a Google sign-in. Open a
                    # dedicated Chrome window immediately, so the user can act.
                    # If Chrome fails, preserve created profile for manual login.
                    try:
                        opened = open_login(result["id"])
                        result["login_opened"]=bool(opened.get("opened"))
                        result["login_error"]=""
                    except (AccountError,OSError) as login_exc:
                        result["login_opened"]=False
                        result["login_error"]=str(login_exc)[:120]
                elif action == "select":''')
])
sub(files[2],[
    ("create_msg",'''    if (action==="create") {
      await loadMcpAccounts();
      el.mcpAccountSelect.value=data.result.id;
      el.mcpAccountStatus.textContent="Đã tạo phiên làm việc mới. Bấm 'Mở Cửa Sổ Xác Thực' rồi chọn phiên để sản xuất.";
    } else if (action==="select") {''',
'''    if (action==="create") {
      await loadMcpAccounts();
      el.mcpAccountSelect.value=data.result.id;
      el.mcpNewAccountName.value="";
      const didOpen=Boolean(data.result.login_opened);
      el.mcpAccountStatus.textContent=didOpen ?
        "Đã thêm tài khoản và mở Chrome Google Flow riêng.\\n"
        +"BƯỚC 1: Đăng nhập Google trong Chrome.\\n"
        +"BƯỚC 2: Quay lại đây, bấm Kiểm tra trình duyệt rồi Xác minh MCP.\\n"
        +"Chưa xác minh quyền vào dự án; chưa thể coi tài khoản đã sẵn sàng." :
        "Đã thêm tài khoản nhưng chưa mở được Chrome: "+
        (data.result.login_error || "hãy bấm Mở đăng nhập Google Flow.");
    } else if (action==="select") {'''),
    ("select_msg",'''      el.mcpAccountStatus.textContent="Đã kích hoạt phiên làm việc. Sẵn sàng sản xuất.";''',
 '''      el.mcpAccountStatus.textContent="Đã chọn tài khoản. Chưa xác minh quyền vào Google Flow. Hãy mở đăng nhập và Xác minh MCP trước khi sản xuất.";'''),
    ("login_msg",'''      el.mcpAccountStatus.textContent="Đã mở cửa sổ xác thực phiên làm việc. Vui lòng hoàn tất trong cửa sổ đó, sau đó bấm 'Xác minh Veo 3 Core'.";''',
 '''      el.mcpAccountStatus.textContent="Đã yêu cầu mở Chrome Google Flow của tài khoản này. Đăng nhập tại Chrome, sau đó bấm Kiểm tra trình duyệt và Xác minh MCP.";'''),
    ("account_load_err",'''      el.mcpAccountStatus.textContent = "Không thể tải phiên làm việc Veo 3: " + error.message;''',
 '''      el.mcpAccountStatus.textContent = "Không thể tải tài khoản Google Flow: " + error.message;'''),
    ("account_name_missing",'''    el.mcpAccountStatus.textContent = "Nhập tên cho phiên làm việc Veo 3 mới.";''',
 '''    el.mcpAccountStatus.textContent = "Hãy nhập tên tài khoản Google Flow trước khi bấm Thêm & đăng nhập.";'''),
    ("account_request_pending",'''    "Đang xác minh kết nối Veo 3 Core..." : "Đang xử lý phiên làm việc...");''',
 '''    "Đang xác minh MCP (không tạo ảnh)..." : "Đang tạo hoặc kiểm tra tài khoản Google Flow...");'''),
    ("account_generic_error",'''    el.mcpAccountStatus.textContent="Lỗi phiên Veo 3: "+err.message;''',
 '''    el.mcpAccountStatus.textContent="Không thể thao tác tài khoản Google Flow: "+err.message;'''),
    ("account_verify_success",'''        "Veo 3 Core: Xác minh kết nối THÀNH CÔNG. Hệ thống sẵn sàng sản xuất." :''',
 '''        "Xác minh MCP tạo ảnh thành công cho hồ sơ đã chọn. Vui lòng kiểm tra quyền truy cập dự án trước khi dùng hàng loạt." :'''),
    ("account_verify_fail",'''        "Veo 3 Core chưa sẵn sàng: "+(data.result.reason||"kiểm tra quyền truy cập");''',
 '''        "MCP chưa sẵn sàng: "+(data.result.reason||"kiểm tra đăng nhập và quyền truy cập dự án Flow");''')
])
sub(files[3],[
    ("modal_title",'''Cài Đặt API & Quản Lý Phiên Làm Việc Veo 3''','''Cài Đặt API & Tài Khoản MCP Google Flow'''),
    ("session_label",'''Quản Lý Phiên Làm Việc Nền Tảng Veo 3''','''Quản Lý Tài Khoản Google Flow (MCP tạo ảnh)'''),
    ("session_desc",'''Xác thực phiên làm việc trong môi trường duyệt web độc lập. Studio bảo mật 100%, không lưu mật khẩu.''',
 '''Sau khi bấm Thêm tài khoản, Chrome riêng sẽ mở để bạn đăng nhập Google.
            Studio không hỏi mật khẩu hoặc sao chép cookie. Tài khoản mới phải có quyền truy cập công cụ Flow đã cấu hình; tạo hồ sơ không tự cấp quyền dự án.'''),
    ("session_add_placeholder",'''placeholder="Tên phiên mới (VD: Veo 3 Pro Session)"''',
 '''placeholder="Tên tài khoản (ví dụ: Google Flow 2)"'''),
    ("session_add_button",'''id="btnMcpAddAccount">+ Thêm phiên</button>''',
 '''id="btnMcpAddAccount" type="button">+ Thêm & mở đăng nhập</button>'''),
    ("login_button",'''id="btnMcpOpenLogin">🌐 Mở Cửa Sổ Xác Thực Veo 3</button>''',
 '''id="btnMcpOpenLogin" type="button">🌐 Mở đăng nhập Google Flow</button>'''),
    ("verify_button",'''id="btnMcpVerifyAccount">Xác minh Veo 3 Core</button>''',
 '''id="btnMcpVerifyAccount" type="button">Xác minh MCP tạo ảnh</button>'''),
    ("status_default",'''Chọn phiên làm việc và xác thực. Sẵn sàng sản xuất khi Veo 3 Core báo trực tuyến.''',
 '''Chưa xác minh đăng nhập. Thêm tài khoản → đăng nhập bằng Chrome → Xác minh MCP tạo ảnh.'''),
    ("new_script_version",'''app.js?v=20261012_multigenre_v2''',
 '''app.js?v=20261012_account_login_fix_v3''')
])
for p in files[:2]:
    py_compile.compile(str(p),doraise=True)
print("ACCOUNT_CREATE_AUTO_LOGIN_FIX_PASS")
print("CHECKPOINT",cp)
