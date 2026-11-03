"""Visible Muse sign-in and verified export into the local Muse CLI session.

Browser ownership is scoped to a dedicated profile. Cookie values never leave
the authentication worker or appear in API responses and logs.
"""
from __future__ import annotations
import ctypes
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

# Ensure bundled muse packages are always importable
_MUSE_SITE = (Path(__file__).resolve().parent / "runtime" / "muse" / "python" / "Lib" / "site-packages")
if _MUSE_SITE.is_dir() and str(_MUSE_SITE) not in sys.path:
    sys.path.insert(0, str(_MUSE_SITE))
from urllib.parse import urlsplit
from urllib.request import urlopen

# Root currently enters Meta cross-service session probing and may end on Instagram.
# This official Muse entry exposes the phone/email sign-in form directly.
LOGIN_ENTRY_URL = "https://muse.ai/business"
VERIFY_TIMEOUT_SECONDS = 35


def _private_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    fd = os.open(str(temp), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(text); f.flush(); os.fsync(f.fileno())
        os.replace(temp, path)
        os.chmod(path, 0o600)
    finally:
        temp.unlink(missing_ok=True)


def muse_cookies(jar):
    return [c for c in jar if isinstance(c, dict)
            and str(c.get("domain", "")).lstrip(".").lower() == "muse.ai"
            and isinstance(c.get("name"), str) and isinstance(c.get("value"), str)
            and not any(ch in c["name"] + c["value"] for ch in "\r\n\t")]


def _agent_browser_path():
    bundled = Path(__file__).resolve().parent / "runtime" / "muse" / "agent-browser.exe"
    if bundled.is_file():
        return str(bundled)
    local = Path(os.environ.get("APPDATA", "")) / "npm" / "node_modules" / "agent-browser" / "bin" / "agent-browser-win32-x64.exe"
    if local.is_file():
        return str(local)
    executable = shutil.which("agent-browser")
    if not executable:
        return ""
    return executable


def _read_cdp_cookies(port):
    """Directly fetch cookies via Chrome DevTools Protocol over WebSocket in under 50ms."""
    import urllib.request
    import socket
    import base64
    from urllib.parse import urlparse
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{int(port)}/json/version", timeout=3) as r:
            ver = json.load(r)
            ws_url = ver.get("webSocketDebuggerUrl")
    except Exception:
        return []
    if not ws_url:
        return []
    try:
        u = urlparse(ws_url)
        s = socket.create_connection((u.hostname, u.port), timeout=4)
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        req = (f"GET {u.path} HTTP/1.1\r\n"
               f"Host: {u.hostname}:{u.port}\r\n"
               "Upgrade: websocket\r\n"
               "Connection: Upgrade\r\n"
               f"Sec-WebSocket-Key: {key}\r\n"
               "Sec-WebSocket-Version: 13\r\n\r\n")
        s.sendall(req.encode("utf-8"))
        resp = s.recv(4096)
        if b" 101 " not in resp:
            s.close()
            return []
        msg = json.dumps({"id": 1, "method": "Storage.getCookies"}).encode("utf-8")
        payload_len = len(msg)
        header = bytearray([0x81])
        if payload_len < 126:
            header.append(0x80 | payload_len)
        elif payload_len <= 65535:
            header.append(0x80 | 126)
            header.extend(payload_len.to_bytes(2, "big"))
        else:
            header.append(0x80 | 127)
            header.extend(payload_len.to_bytes(8, "big"))
        mask = os.urandom(4)
        header.extend(mask)
        masked = bytearray(b ^ mask[i % 4] for i, b in enumerate(msg))
        s.sendall(header + masked)
        
        data = bytearray()
        s.settimeout(4)
        while True:
            chunk = s.recv(65536)
            if not chunk:
                break
            data.extend(chunk)
            if len(data) >= 2:
                l = data[1] & 0x7f
                idx = 2
                if l == 126:
                    if len(data) < 4:
                        continue
                    idx = 4
                    l = int.from_bytes(data[2:4], "big")
                elif l == 127:
                    if len(data) < 10:
                        continue
                    idx = 10
                    l = int.from_bytes(data[2:10], "big")
                if len(data) >= idx + l:
                    payload = data[idx:idx+l]
                    s.close()
                    res = json.loads(payload.decode("utf-8"))
                    raw = res.get("result", {}).get("cookies", [])
                    return muse_cookies(raw)
        s.close()
    except Exception:
        pass
    return []


def _read_browser_cookies(port):
    if not _probe_browser(port):
        return []
    return _read_cdp_cookies(port)


def _verify_candidate(header):
    from muse_cli.gateway import Gateway
    finished = threading.Event()
    outcome = {}
    def verify():
        gateway = None
        try:
            gateway = Gateway(header, vm_id=None)
            sessions = gateway.call_json("sessions.list", timeout=30)
            if not isinstance(sessions.get("sessions"), list):
                raise RuntimeError("MUSE_LOGIN_VERIFY_FAILED")
            outcome["vm_id"] = gateway.vm_id
        except Exception as exc:
            outcome["error"] = exc
        finally:
            if gateway is not None:
                try:
                    gateway.close()
                except Exception:
                    pass
            finished.set()
    # This runs only in the isolated auth worker. A blocked SDK receive must
    # not keep the account lock held after the worker returns and exits.
    threading.Thread(target=verify, daemon=True).start()
    if not finished.wait(VERIFY_TIMEOUT_SECONDS):
        raise RuntimeError("MUSE_LOGIN_VERIFY_TIMEOUT")
    if "error" in outcome:
        raise outcome["error"]
    return outcome["vm_id"]


def export_session(port, productions_dir, account_id=None):
    import muse_accounts
    jar = muse_cookies(_read_browser_cookies(int(port)))
    if not any(c["name"] == "hatch_sess" and c["value"] for c in jar):
        return {"ok": True, "ready": False, "status": "WAITING_FOR_LOGIN",
                "message": "Đăng nhập tài khoản trong cửa sổ Muse; tool sẽ tự kết nối sau khi đăng nhập xong."}
    header = "; ".join(c["name"] + "=" + c["value"] for c in jar)
    try:
        vm_id = _verify_candidate(header)
    except Exception:
        return {"ok": True, "ready": False, "status": "WAITING_FOR_LOGIN",
                "message": "Phiên trên cửa sổ Muse chưa xác minh được. Hoàn tất đăng nhập rồi thử kết nối lại."}

    lines = ["# Netscape HTTP Cookie File"]
    for c in jar:
        domain = c["domain"]
        lines.append("\t".join([domain, "TRUE" if domain.startswith(".") else "FALSE", c.get("path", "/"),
                                 "TRUE" if c.get("secure") else "FALSE", str(int(c.get("expires", 0) or 0)), c["name"], c["value"]]))
    cookie_str = "\n".join(lines) + "\n"

    target_id = account_id or muse_accounts.get_active_id() or "account_1"
    account = muse_accounts.get_account(target_id)
    old_vm = (account or {}).get("vm_id")
    if old_vm and vm_id != old_vm:
        for receipt_path in Path(productions_dir).rglob("muse_job.json"):
            try:
                receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if receipt.get("state") in ("accepted", "submission_uncertain") and receipt.get("account_vm_id") == old_vm:
                raise RuntimeError("MUSE_PENDING_ACCOUNT_LOCKED: Tài khoản đang có cảnh chưa hoàn tất. Hoàn tất cảnh trước khi đổi phiên đăng nhập.")
    if not muse_accounts.get_account(target_id):
        target_id = muse_accounts.create_account(f"Tài khoản {target_id}")["id"]

    muse_accounts.save_account_session(target_id, cookie_str, vm_id=vm_id)

    # save_account_session synchronizes only the active account; do not overwrite
    # the active/default session when a different account finishes signing in.

    acc = muse_accounts.get_account(target_id)
    acc_name = (acc.get("name") if acc else None) or target_id
    return {"ok": True, "ready": True, "status": "READY", "account_id": target_id,
            "message": f"Đã đăng nhập và xác minh '{acc_name}'. Sẵn sàng sản xuất ảnh và video."}


def _chrome_path():
    for root in (os.environ.get("PROGRAMFILES", ""), os.environ.get("PROGRAMFILES(X86)", ""), os.environ.get("LOCALAPPDATA", "")):
        p = Path(root) / "Google" / "Chrome" / "Application" / "chrome.exe"
        if p.is_file():
            return p
    found = shutil.which("chrome")
    return Path(found) if found else None


def _probe_browser(port):
    try:
        s = socket.create_connection(("127.0.0.1", int(port)), timeout=0.15)
        s.close()
    except Exception:
        return False
    try:
        with urlopen("http://127.0.0.1:%d/json/version" % int(port), timeout=1) as r:
            return bool(json.load(r).get("webSocketDebuggerUrl"))
    except Exception:
        return False


def _owns_browser(pid, profile):
    if os.name != "nt":
        return False
    command = "(Get-CimInstance Win32_Process -Filter 'ProcessId = %d').CommandLine | ConvertTo-Json -Compress" % int(pid)
    p = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", command], capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=8, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    try:
        line = json.loads(p.stdout)
        if not isinstance(line, str):
            return False
        argc = ctypes.c_int()
        parser = ctypes.windll.shell32.CommandLineToArgvW
        parser.argtypes = [ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_int)]
        parser.restype = ctypes.POINTER(ctypes.c_wchar_p)
        argv = parser(line, ctypes.byref(argc))
        try:
            return any(str(argv[i]).lower().startswith("--user-data-dir=") and
                       Path(str(argv[i]).split("=", 1)[1]).resolve() == Path(profile).resolve() for i in range(argc.value))
        finally:
            ctypes.windll.kernel32.LocalFree(ctypes.cast(argv, ctypes.c_void_p))
    except Exception:
        return False


def _show_window(pid):
    if os.name != "nt":
        return False
    try:
        from studio_flow_accounts import _attach_desktop
        _attach_desktop()
        from ctypes import wintypes
        user = ctypes.windll.user32
        found = []
        callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        def visit(hwnd, unused):
            owner = wintypes.DWORD()
            user.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
            if owner.value == int(pid) and user.IsWindowVisible(hwnd):
                user.ShowWindowAsync(hwnd, 9)
                user.SetForegroundWindow(hwnd)
                found.append(True)
            return True
        user.EnumWindows(callback_type(visit), 0)
        return bool(found)
    except Exception:
        return False


def _launch_browser(chrome, args):
    try:
        from studio_flow_accounts import _attach_desktop
        _attach_desktop()
    except Exception:
        pass
    p = subprocess.Popen([str(chrome)] + args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return p.pid


_ACTIVE_BRIDGES = {}


class LocalProxyBridge:
    """Lightweight local loopback HTTP forwarder that transparently injects Proxy-Authorization."""
    def __init__(self, remote_proxy_url: str):
        import urllib.parse
        import base64
        import socket
        import select
        import threading

        u = urllib.parse.urlparse(remote_proxy_url)
        self.remote_host = u.hostname
        self.remote_port = u.port or 80
        self.user = u.username
        self.pword = u.password
        self.auth_header = None
        if self.user and self.pword:
            cred = f"{self.user}:{self.pword}".encode("utf-8")
            self.auth_header = b"Proxy-Authorization: Basic " + base64.b64encode(cred) + b"\r\n"

        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_sock.bind(("127.0.0.1", 0))
        self.local_port = self.server_sock.getsockname()[1]
        self.server_sock.listen(50)
        self.running = True
        self.thread = threading.Thread(target=self._accept_loop, daemon=True)
        self.thread.start()

    def _accept_loop(self):
        import threading
        while self.running:
            try:
                client_sock, _ = self.server_sock.accept()
                t = threading.Thread(target=self._handle_client, args=(client_sock,), daemon=True)
                t.start()
            except Exception:
                break

    def _handle_client(self, client_sock):
        import socket
        import select
        remote_sock = None
        try:
            client_sock.settimeout(15.0)
            req = b""
            while b"\r\n\r\n" not in req:
                chunk = client_sock.recv(4096)
                if not chunk:
                    client_sock.close()
                    return
                req += chunk

            header_part, rest = req.split(b"\r\n\r\n", 1)
            lines = header_part.split(b"\r\n")
            first_line = lines[0]
            parts = first_line.split()
            if not parts:
                client_sock.close()
                return

            method = parts[0].decode("ascii", errors="ignore").upper()

            remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_sock.settimeout(15.0)
            remote_sock.connect((self.remote_host, self.remote_port))

            if method == "CONNECT":
                new_headers = [first_line]
                if self.auth_header:
                    new_headers.append(self.auth_header.rstrip(b"\r\n"))
                for line in lines[1:]:
                    if not line.lower().startswith(b"proxy-authorization:"):
                        new_headers.append(line)
                new_req = b"\r\n".join(new_headers) + b"\r\n\r\n"
                remote_sock.sendall(new_req)

                resp = b""
                while b"\r\n\r\n" not in resp:
                    chunk = remote_sock.recv(4096)
                    if not chunk:
                        break
                    resp += chunk

                if b"200" not in resp.split(b"\r\n")[0]:
                    client_sock.sendall(resp)
                    client_sock.close()
                    remote_sock.close()
                    return

                client_sock.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")
            else:
                new_headers = [first_line]
                if self.auth_header:
                    new_headers.append(self.auth_header.rstrip(b"\r\n"))
                for line in lines[1:]:
                    if not line.lower().startswith(b"proxy-authorization:"):
                        new_headers.append(line)
                new_req = b"\r\n".join(new_headers) + b"\r\n\r\n" + rest
                remote_sock.sendall(new_req)

            client_sock.setblocking(False)
            remote_sock.setblocking(False)
            sockets = [client_sock, remote_sock]

            while True:
                r, _, x = select.select(sockets, [], sockets, 60.0)
                if x or not r:
                    break
                for s in r:
                    data = s.recv(32768)
                    if not data:
                        return
                    out = remote_sock if s is client_sock else client_sock
                    out.sendall(data)
        except Exception:
            pass
        finally:
            try:
                client_sock.close()
            except Exception:
                pass
            if remote_sock:
                try:
                    remote_sock.close()
                except Exception:
                    pass

    def close(self):
        self.running = False
        try:
            self.server_sock.close()
        except Exception:
            pass


def _prepare_chrome_proxy_args(proxy_url: str | None, aid: str | None = None) -> list[str]:
    """Prepares Chrome CLI arguments using a zero-credential local loopback forwarder."""
    if not proxy_url:
        return []
    try:
        from urllib.parse import urlparse
        u = urlparse(proxy_url)
        if not u.hostname:
            return [f"--proxy-server={proxy_url}"]

        # If proxy requires username/password, route through local bridge to bypass Chrome auth dialog
        if u.username and u.password:
            key = aid or proxy_url
            old_bridge = _ACTIVE_BRIDGES.get(key)
            if old_bridge:
                try:
                    old_bridge.close()
                except Exception:
                    pass
            bridge = LocalProxyBridge(proxy_url)
            _ACTIVE_BRIDGES[key] = bridge
            print(f"[MUSE_PROXY] 🌐 LocalProxyBridge 127.0.0.1:{bridge.local_port} -> {u.hostname}:{u.port}", flush=True)
            return [f"--proxy-server=http://127.0.0.1:{bridge.local_port}"]
        else:
            clean_proxy = f"{u.scheme or 'http'}://{u.hostname}:{u.port}" if u.port else f"{u.scheme or 'http'}://{u.hostname}"
            return [f"--proxy-server={clean_proxy}"]
    except Exception as exc:
        print(f"[MUSE_PROXY_ERR] Lỗi cấu hình bridge proxy Chrome: {exc}", flush=True)
        return [f"--proxy-server={proxy_url}"]


class LoginManager:
    def __init__(self, home, profile_root=None):
        self.home = Path(home)
        self.root = Path(profile_root) if profile_root else Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "StoryboardAI" / "MuseLogin"
        self.lock = threading.Lock()

    def _acc_paths(self, account_id: str | None = None):
        import muse_accounts
        aid = account_id or muse_accounts.get_active_id() or "account_1"
        profile_dir = self.root / aid / "ChromeProfile"
        state_path = self.root / aid / "browser.json"
        lock_path = self.root / aid / "browser_start.lock"
        return aid, profile_dir, state_path, lock_path

    def _state(self, account_id: str | None = None):
        _, _, state_path, _ = self._acc_paths(account_id)
        try:
            return json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def status(self, account_id: str | None = None):
        if not account_id:
            for p in self.root.glob("*/browser.json"):
                try:
                    data = json.loads(p.read_text(encoding="utf-8"))
                    if data.get("status") == "WAITING_FOR_LOGIN" and data.get("port"):
                        if _probe_browser(data.get("port")):
                            account_id = data.get("account_id") or p.parent.name
                            break
                        else:
                            data["status"] = "IDLE"
                            _private_text(p, json.dumps(data))
                except Exception:
                    pass
        aid, _, _, _ = self._acc_paths(account_id)
        d = self._state(aid)
        return {"account_id": aid, "login_id": d.get("login_id", ""), "status": d.get("status", "IDLE"),
                "opened": bool(d.get("login_id")), "ready": d.get("status") == "READY"}

    def start(self, account_id: str | None = None, account_name: str | None = None):
        import muse_accounts
        from muse_gateway_worker import render_lock

        if not account_id:
            if account_name:
                acc = muse_accounts.create_account(account_name)
                account_id = acc["id"]
            else:
                account_id = muse_accounts.get_active_id() or "account_1"
        else:
            if not muse_accounts.get_account(account_id):
                muse_accounts.create_account(account_name or f"Tài khoản {account_id}")

        aid, profile, state_path, lock_path = self._acc_paths(account_id)
        profile.parent.mkdir(parents=True, exist_ok=True)

        with self.lock, render_lock(lock_path, timeout=2):
            chrome = _chrome_path()
            if chrome is None:
                raise RuntimeError("MUSE_CHROME_MISSING: Chưa tìm thấy Google Chrome để mở đăng nhập Muse.")
            d = self._state(aid)
            connected = bool(d.get("port") and _probe_browser(d["port"]))
            if connected:
                if not _owns_browser(d.get("pid", 0), profile):
                    raise RuntimeError("MUSE_LOGIN_BROWSER_CONFLICT: Không xác minh được cửa sổ Muse riêng; giữ nguyên các trình duyệt đang mở.")
                if not _show_window(d["pid"]):
                    raise RuntimeError("MUSE_LOGIN_WINDOW_NOT_VISIBLE: Chưa đưa được cửa sổ Muse ra màn hình. Kiểm tra cửa sổ Chrome của Muse.")
                if d.get("entry_url") != LOGIN_ENTRY_URL:
                    _launch_browser(chrome, ["--user-data-dir=" + str(profile),
                                            "--profile-directory=Default", "--new-tab", LOGIN_ENTRY_URL])
                reused = True
            else:
                if d.get("pid") and _owns_browser(d["pid"], profile):
                    raise RuntimeError("MUSE_LOGIN_BROWSER_STARTING: Cửa sổ Muse đã mở nhưng chưa sẵn sàng kết nối. Chờ vài giây rồi thử lại; không mở thêm cửa sổ.")
                profile.mkdir(parents=True, exist_ok=True)
                with socket.socket() as sock:
                    sock.bind(("127.0.0.1", 0))
                    port = sock.getsockname()[1]
                acc_obj = muse_accounts.get_account(aid)
                proxy_val = (acc_obj or {}).get("proxy")
                args = ["--remote-debugging-address=127.0.0.1", "--remote-debugging-port=" + str(port),
                        "--remote-allow-origins=*",
                        "--user-data-dir=" + str(profile), "--profile-directory=Default", "--no-first-run",
                        "--no-default-browser-check", "--new-window", "--window-size=1100,800"]
                if proxy_val:
                    args.extend(_prepare_chrome_proxy_args(proxy_val, aid))
                args.append(LOGIN_ENTRY_URL)
                d = {"port": port, "pid": _launch_browser(chrome, args), "account_id": aid}
                deadline = time.monotonic() + 15
                while not _probe_browser(port):
                    if time.monotonic() >= deadline:
                        _private_text(state_path, json.dumps(d))
                        raise RuntimeError("MUSE_LOGIN_BROWSER_STARTING: Cửa sổ Muse đang khởi động. Bấm Đăng nhập Muse lần nữa sau vài giây.")
                    time.sleep(.3)
                try:
                    _show_window(d["pid"])
                except Exception:
                    pass
                reused = False
            d.update(login_id=d.get("login_id") or uuid.uuid4().hex, started=time.time(), status="WAITING_FOR_LOGIN", entry_url=LOGIN_ENTRY_URL, account_id=aid)
            _private_text(state_path, json.dumps(d))
            acc = muse_accounts.get_account(aid)
            name_label = (acc.get("name") if acc else None) or aid
            return {**self.status(aid), "ok": True, "reused": reused, "account_id": aid,
                    "message": f"Đăng nhập tài khoản '{name_label}' trong cửa sổ Muse vừa mở. Tool sẽ tự kiểm tra và kết nối."}

    def complete(self, login_id, worker, account_id: str | None = None):
        with self.lock:
            if not account_id:
                for p in self.root.glob("*/browser.json"):
                    try:
                        data = json.loads(p.read_text(encoding="utf-8"))
                        if login_id and data.get("login_id") == login_id:
                            account_id = data.get("account_id") or p.parent.name
                            break
                        if data.get("status") == "WAITING_FOR_LOGIN" and data.get("port") and _probe_browser(data.get("port")):
                            account_id = data.get("account_id") or p.parent.name
                            break
                    except Exception:
                        pass
            aid, profile, state_path, _ = self._acc_paths(account_id)
            d = self._state(aid)
            if not d.get("port") or not _probe_browser(d.get("port", 0)):
                raise RuntimeError("MUSE_LOGIN_BROWSER_CLOSED: Cửa sổ đăng nhập Muse đã đóng hoặc chưa mở. Bấm Đăng nhập Muse để mở lại.")
            if not login_id or login_id != d.get("login_id"):
                raise RuntimeError("MUSE_LOGIN_STALE: Phiên đăng nhập đã thay đổi. Mở lại đúng tài khoản Muse rồi xác nhận.")
            result = worker("auth-export", {"port": d["port"], "productions_dir": str(self.home / "productions"),
                            "account_id": aid,
                            "lock_path": str(self.home / "runtime" / f"muse_render_{aid}.lock")}, timeout=120)
            d["status"] = "READY" if result.get("ready") else "WAITING_FOR_LOGIN"
            _private_text(state_path, json.dumps(d))
            return {**result, "login_id": login_id or d.get("login_id", ""), "account_id": aid}