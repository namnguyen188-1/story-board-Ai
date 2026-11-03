# -*- coding: utf-8 -*-
import sys
import os

sys.stdout.reconfigure(encoding="utf-8")

def patch_muse_login():
    path = os.path.join("studio", "muse_login.py")
    with open(path, "r", encoding="utf-8") as f:
        code = f.read()

    bridge_code = '''_ACTIVE_BRIDGES = {}


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
            self.auth_header = b"Proxy-Authorization: Basic " + base64.b64encode(cred) + b"\\r\\n"

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
            while b"\\r\\n\\r\\n" not in req:
                chunk = client_sock.recv(4096)
                if not chunk:
                    client_sock.close()
                    return
                req += chunk

            header_part, rest = req.split(b"\\r\\n\\r\\n", 1)
            lines = header_part.split(b"\\r\\n")
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
                    new_headers.append(self.auth_header.rstrip(b"\\r\\n"))
                for line in lines[1:]:
                    if not line.lower().startswith(b"proxy-authorization:"):
                        new_headers.append(line)
                new_req = b"\\r\\n".join(new_headers) + b"\\r\\n\\r\\n"
                remote_sock.sendall(new_req)

                resp = b""
                while b"\\r\\n\\r\\n" not in resp:
                    chunk = remote_sock.recv(4096)
                    if not chunk:
                        break
                    resp += chunk

                if b"200" not in resp.split(b"\\r\\n")[0]:
                    client_sock.sendall(resp)
                    client_sock.close()
                    remote_sock.close()
                    return

                client_sock.sendall(b"HTTP/1.1 200 Connection established\\r\\n\\r\\n")
            else:
                new_headers = [first_line]
                if self.auth_header:
                    new_headers.append(self.auth_header.rstrip(b"\\r\\n"))
                for line in lines[1:]:
                    if not line.lower().startswith(b"proxy-authorization:"):
                        new_headers.append(line)
                new_req = b"\\r\\n".join(new_headers) + b"\\r\\n\\r\\n" + rest
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
'''

    # Replace existing _prepare_chrome_proxy_args implementation
    start_marker = "def _prepare_chrome_proxy_args"
    class_marker = "class LoginManager:"
    if start_marker in code:
        idx1 = code.find(start_marker)
        idx2 = code.find(class_marker)
        code = code[:idx1] + bridge_code + "\n\n" + code[idx2:]
        print("[✓] Replaced _prepare_chrome_proxy_args with LocalProxyBridge in muse_login.py")

    # Update call in start()
    old_call = "args.extend(_prepare_chrome_proxy_args(proxy_val, profile))"
    new_call = "args.extend(_prepare_chrome_proxy_args(proxy_val, aid))"
    if old_call in code:
        code = code.replace(old_call, new_call)
        print("[✓] Updated call to _prepare_chrome_proxy_args(proxy_val, aid)")

    with open(path, "w", encoding="utf-8") as f:
        f.write(code)

if __name__ == "__main__":
    patch_muse_login()
