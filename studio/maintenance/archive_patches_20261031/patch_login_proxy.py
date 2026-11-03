# -*- coding: utf-8 -*-
import sys
import os

sys.stdout.reconfigure(encoding="utf-8")

def patch_muse_login():
    path = os.path.join("studio", "muse_login.py")
    with open(path, "r", encoding="utf-8") as f:
        code = f.read()

    helper_code = '''def _prepare_chrome_proxy_args(proxy_url: str | None, profile_dir: Path) -> list[str]:
    """Prepares Chrome CLI arguments and auto-auth extension for proxy."""
    if not proxy_url:
        return []
    try:
        from urllib.parse import urlparse
        u = urlparse(proxy_url)
        scheme = u.scheme or "http"
        host = u.hostname
        port = u.port
        user = u.username
        pword = u.password

        if not host:
            return [f"--proxy-server={proxy_url}"]

        # If proxy has authentication, generate lightweight extension so Chrome auto-authenticates
        if user and pword:
            ext_dir = profile_dir / "_proxy_auth_ext"
            ext_dir.mkdir(parents=True, exist_ok=True)
            manifest = {
                "version": "1.0.0",
                "manifest_version": 3,
                "name": "Muse Proxy Auth Extension",
                "permissions": ["webRequest", "webRequestAuthProvider"],
                "host_permissions": ["<all_urls>"],
                "background": {"service_worker": "background.js"}
            }
            (ext_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            bg_js = f"""// Auto-authenticate proxy in Chrome
chrome.webRequest.onAuthRequired.addListener(
    function(details) {{
        return {{
            authCredentials: {{
                username: {json.dumps(user)},
                password: {json.dumps(pword)}
            }}
        }};
    }},
    {{ urls: ["<all_urls>"] }},
    ["blocking"]
);
"""
            (ext_dir / "background.js").write_text(bg_js, encoding="utf-8")
            clean_proxy = f"{scheme}://{host}:{port}" if port else f"{scheme}://{host}"
            return [
                f"--proxy-server={clean_proxy}",
                f"--load-extension={str(ext_dir)}",
                f"--disable-extensions-except={str(ext_dir)}"
            ]
        else:
            clean_proxy = f"{scheme}://{host}:{port}" if port else f"{scheme}://{host}"
            return [f"--proxy-server={clean_proxy}"]
    except Exception as exc:
        print(f"[MUSE_PROXY_ERR] Không thể cấu hình proxy Chrome: {exc}")
        return [f"--proxy-server={proxy_url}"]
'''

    if "def _prepare_chrome_proxy_args" not in code:
        target_func = "class LoginManager:"
        idx = code.find(target_func)
        if idx != -1:
            code = code[:idx] + helper_code + "\n\n" + code[idx:]
            print("[✓] Injected _prepare_chrome_proxy_args into muse_login.py")

    old_proxy_call = 'if proxy_val:\n                    args.append(f"--proxy-server={proxy_val}")'
    new_proxy_call = 'if proxy_val:\n                    args.extend(_prepare_chrome_proxy_args(proxy_val, profile))'

    if old_proxy_call in code:
        code = code.replace(old_proxy_call, new_proxy_call)
        print("[✓] Replaced args.append with args.extend(_prepare_chrome_proxy_args) in muse_login.py")
    else:
        # Check CRLF
        old_proxy_call_crlf = 'if proxy_val:\r\n                    args.append(f"--proxy-server={proxy_val}")'
        new_proxy_call_crlf = 'if proxy_val:\r\n                    args.extend(_prepare_chrome_proxy_args(proxy_val, profile))'
        if old_proxy_call_crlf in code:
            code = code.replace(old_proxy_call_crlf, new_proxy_call_crlf)
            print("[✓] Replaced args.append with args.extend(_prepare_chrome_proxy_args) in muse_login.py (CRLF)")

    with open(path, "w", encoding="utf-8") as f:
        f.write(code)

if __name__ == "__main__":
    patch_muse_login()
