"""Complete Studio MCP account UI changes; backend was separately patched.
Atomic frontend write only after ALL anchors validate.
"""
from pathlib import Path
root=Path(r"D:\STORYBOARD_AI\studio")
js=root/"web"/"app.js"
html=root/"web"/"index.html"
s=js.read_text(encoding="utf-8")
h=html.read_text(encoding="utf-8")
def one(text,old,new,label):
    if old not in text:raise RuntimeError("MISSING: "+label)
    return text.replace(old,new,1)
old="""    if (action==="create") {
      await loadMcpAccounts();
      el.mcpAccountSelect.value=data.result.id;
      el.mcpAccountStatus.textContent="Đã tạo phiên làm việc mới. Bấm 'Mở Cửa Sổ Xác Thực' rồi chọn phiên để sản xuất.";
    } else if (action==="select") {"""
new="""    if (action==="create") {
      await loadMcpAccounts();
      el.mcpAccountSelect.value=data.result.id;
      el.mcpNewAccountName.value="";
      el.mcpAccountStatus.textContent=data.result.login_opened ?
        "Đã thêm tài khoản và mở Chrome Google Flow riêng.\\n"
        +"Bước 1: Đăng nhập Google trong Chrome.\\n"
        +"Bước 2: Quay lại, bấm Kiểm tra trình duyệt rồi Xác minh MCP.\\n"
        +"Chưa xác minh đăng nhập hoặc quyền truy cập dự án." :
        "Hồ sơ đã tạo, nhưng chưa mở được Chrome: "
        +(data.result.login_error || "Bấm Mở đăng nhập Google Flow.");
    } else if (action==="select") {"""
s=one(s,old,new,"create_status")
for a,b,label in [
('Đã kích hoạt phiên làm việc. Sẵn sàng sản xuất.','Đã chọn tài khoản. Chưa xác minh Google Flow hoặc quyền MCP. Hãy đăng nhập và kiểm tra kết nối.','selected_status'),
("Đã mở cửa sổ xác thực phiên làm việc. Vui lòng hoàn tất trong cửa sổ đó, sau đó bấm 'Xác minh Veo 3 Core'.","Đã yêu cầu mở Chrome Google Flow riêng. Đăng nhập trong Chrome, sau đó quay lại Xác minh MCP.","login_status"),
("Không thể tải phiên làm việc Veo 3: ","Không thể tải tài khoản Google Flow: ","account_load_error"),
("Nhập tên cho phiên làm việc Veo 3 mới.","Hãy nhập tên tài khoản trước khi bấm Thêm & đăng nhập.","missing_name"),
("Đang xác minh kết nối Veo 3 Core...","Đang xác minh MCP (không tạo ảnh)...","checking"),
("Đang xử lý phiên làm việc...","Đang tạo hoặc chọn tài khoản Google Flow...","processing"),
("Lỗi phiên Veo 3: ","Lỗi tài khoản MCP: ","error_name"),
("Veo 3 Core: Xác minh kết nối THÀNH CÔNG. Hệ thống sẵn sàng sản xuất.","Xác minh chức năng MCP thành công cho tài khoản đã chọn.","verified"),
("Veo 3 Core chưa sẵn sàng: ","MCP chưa sẵn sàng: ","not_verified"),
]:
    s=one(s,a,b,label)
h=one(h,'Cài Đặt API & Quản Lý Phiên Làm Việc Veo 3','Cài Đặt API & Tài Khoản Google Flow MCP','modal_title')
h=one(h,'Quản Lý Phiên Làm Việc Nền Tảng Veo 3','Quản lý tài khoản Google Flow (MCP tạo ảnh)','section_title')
h=one(h,'Xác thực phiên làm việc trong môi trường duyệt web độc lập. Studio bảo mật 100%, không lưu mật khẩu.',
    'Bấm Thêm để tạo hồ sơ Chrome riêng và mở trang đăng nhập Google Flow. Studio không hỏi mật khẩu hay sao chép cookie. Tài khoản mới phải có quyền truy cập công cụ Flow đã cấu hình; thêm hồ sơ không tự cấp quyền dự án.','description')
h=one(h,'Tên phiên mới (VD: Veo 3 Pro Session)','Tên tài khoản (ví dụ: Google Flow 2)','placeholder')
h=one(h,'id="btnMcpAddAccount">+ Thêm phiên</button>','id="btnMcpAddAccount" type="button">+ Thêm & mở đăng nhập</button>','add_button')
h=one(h,'id="btnMcpOpenLogin">🌐 Mở Cửa Sổ Xác Thực Veo 3</button>','id="btnMcpOpenLogin" type="button">🌐 Mở đăng nhập Google Flow</button>','login_button')
h=one(h,'id="btnMcpVerifyAccount">Xác minh Veo 3 Core</button>','id="btnMcpVerifyAccount" type="button">Xác minh MCP tạo ảnh</button>','verify_button')
h=one(h,'Chọn phiên làm việc và xác thực. Sẵn sàng sản xuất khi Veo 3 Core báo trực tuyến.',
    'Chưa xác minh tài khoản. Thêm tài khoản → đăng nhập Google bằng Chrome → Xác minh MCP.','initial_state')
h=one(h,'app.js?v=20261012_multigenre_v2','app.js?v=20261012_account_login_fix_v3','cache_buster')
js.write_text(s,encoding="utf-8")
html.write_text(h,encoding="utf-8")
print("ACCOUNT_FRONTEND_PATCH_PASS")
