import re
from pathlib import Path

def patch():
    wp = Path("studio/web_server.py")
    lines = wp.read_text(encoding="utf-8").splitlines()

    # Find GET handler insertion point
    get_idx = -1
    for i, line in enumerate(lines):
        if 'elif path in ("/api/flow/status", "/api/flowkit/status"):' in line:
            get_idx = i
            break

    assert get_idx != -1, "GET handler index not found"

    get_chunk = [
        '        elif path == "/api/flowkit/install_status":',
        '            try:',
        '                from flowkit_installer import get_install_status',
        '                return self.end_json(get_install_status())',
        '            except Exception as exc:',
        '                return self.end_json({"active": False, "error": str(exc)}, 200)',
        ''
    ]

    lines = lines[:get_idx] + get_chunk + lines[get_idx:]

    # Find POST handler insertion point
    post_idx = -1
    for i, line in enumerate(lines):
        if 'if path in ("/api/flow/login", "/api/flowkit/open_browser"):' in line:
            post_idx = i
            break

    assert post_idx != -1, "POST handler index not found"

    post_chunk = [
        '        if path == "/api/flowkit/install_engine":',
        '            try:',
        '                import threading',
        '                from flowkit_installer import install_flowkit_engine, get_install_status',
        '                curr = get_install_status()',
        '                if curr.get("active"):',
        '                    return self.end_json({"ok": True, "status": curr})',
        '                def _do_install():',
        '                    try:',
        '                        install_flowkit_engine()',
        '                    except Exception as err:',
        '                        pass',
        '                threading.Thread(target=_do_install, daemon=True).start()',
        '                return self.end_json({"ok": True, "message": "Bắt đầu cài đặt động cơ FlowKit tự động..."})',
        '            except Exception as exc:',
        '                return self.end_json({"ok": False, "error": str(exc)}, 500)',
        ''
    ]

    lines = lines[:post_idx] + post_chunk + lines[post_idx:]

    wp.write_text("\n".join(lines).replace("\n", "\r\n"), encoding="utf-8")
    print("SUCCESS: studio/web_server.py patched cleanly with flowkit installer endpoints")

if __name__ == "__main__":
    patch()
