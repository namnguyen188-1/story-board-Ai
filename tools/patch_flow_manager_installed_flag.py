from pathlib import Path

def patch():
    p = Path("studio/flow_account_manager.py")
    lines = p.read_text(encoding="utf-8").splitlines()

    start_else = -1
    for i, line in enumerate(lines):
        if line.strip() == "else:" and i > 1850:
            start_else = i
            break

    assert start_else != -1, "else block not found"

    # Find the return statement inside else
    ret_end = -1
    for j in range(start_else, min(len(lines), start_else + 40)):
        if line_has_brace := (lines[j].strip() == "}"):
            ret_end = j
            break

    assert ret_end != -1, "return end not found"

    new_else_block = [
        '    else:',
        '        from flowkit_installer import is_flowkit_installed',
        '        fk_installed = is_flowkit_installed()',
        '        if not fk_installed:',
        '            return {',
        '                "ready": False,',
        '                "connected": False,',
        '                "flowkit_installed": False,',
        '                "email": "",',
        '                "emails": [],',
        '                "total_accounts": total_cnt,',
        '                "ready_accounts": 0,',
        '                "badge_text": "⚠️ Thiếu động cơ FlowKit",',
        '                "badge_type": "warning",',
        '                "status_text": "Chưa cài đặt động cơ FlowKit (cần cho máy phụ). Bấm [Cài Đặt Động Cơ] để thiết lập tự động 100%.",',
        '                "watcher_active": False',
        '            }',
        '        return {',
        '            "ready": False,',
        '            "connected": False,',
        '            "flowkit_installed": True,',
        '            "email": "",',
        '            "emails": [],',
        '            "total_accounts": total_cnt,',
        '            "ready_accounts": 0,',
        '            "badge_text": "🔴 Chưa kết nối",',
        '            "badge_type": "error",',
        '            "status_text": "Chưa kết nối Web Tool Google Flow. Bấm [Đăng Nhập] để kết nối.",',
        '            "watcher_active": False',
        '        }'
    ]

    lines = lines[:start_else] + new_else_block + lines[ret_end + 1:]
    p.write_text("\n".join(lines).replace("\n", "\r\n"), encoding="utf-8")
    print("SUCCESS: studio/flow_account_manager.py patched with flowkit_installed check")

if __name__ == "__main__":
    patch()
