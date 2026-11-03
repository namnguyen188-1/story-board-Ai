"""Multi-Account Management & Round-Robin Scene Dispatching for Muse AI.

Provides isolated cookie sessions, profile directories, account pool registry,
and scene-by-scene round-robin load balancing with automatic failover.
"""
from __future__ import annotations

import json
import os
import shutil
import time
import uuid
from pathlib import Path
from typing import Any

HOME = Path(__file__).resolve().parent
RUNTIME_DIR = HOME / "runtime"
REGISTRY_PATH = RUNTIME_DIR / "muse_accounts.json"
PROFILES_ROOT = RUNTIME_DIR / "muse_profiles"
LOCAL_APP_DATA = Path(os.environ.get("LOCALAPPDATA", str(Path.home())))
CHROME_PROFILES_ROOT = LOCAL_APP_DATA / "StoryboardAI" / "MuseProfiles"


def _atomic_write_json(path: Path, data: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f"{path.name}.{uuid.uuid4().hex}.tmp")
    with temp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp, path)


def _get_default_muse_cookies_path() -> Path:
    return Path(os.path.expanduser("~/.config/muse-cli/cookies.txt"))


def _get_default_muse_config_path() -> Path:
    return Path(os.path.expanduser("~/.config/muse-cli/config.json"))


def load_registry() -> dict[str, Any]:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    PROFILES_ROOT.mkdir(parents=True, exist_ok=True)

    data = None
    if REGISTRY_PATH.is_file():
        try:
            data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = None

    if not isinstance(data, dict):
        data = {
            "version": 1,
            "active_id": "account_1",
            "dispatch_mode": "round_robin",  # "round_robin" (chia đều mỗi scene 1 tài khoản) | "active_only"
            "accounts": []
        }

    # Auto-reconciliation: Always scan PROFILES_ROOT to ensure no existing profile is ever lost
    existing_ids = {a["id"] for a in data.get("accounts", [])}
    discovered = False
    idx = len(existing_ids) + 1

    if PROFILES_ROOT.is_dir():
        for p in sorted(PROFILES_ROOT.iterdir(), key=lambda x: x.stat().st_mtime if x.is_dir() else 0):
            if not p.is_dir():
                continue
            acc_id = p.name
            if acc_id not in existing_ids:
                ck_file = p / ".config" / "muse-cli" / "cookies.txt"
                cfg_file = p / ".config" / "muse-cli" / "config.json"
                has_cookies = ck_file.is_file() and ck_file.stat().st_size > 50
                vm_id = None
                if cfg_file.is_file():
                    try:
                        cfg_data = json.loads(cfg_file.read_text(encoding="utf-8"))
                        vm_id = cfg_data.get("vm_id")
                    except Exception:
                        pass
                acc_name = f"Tài khoản Muse {idx}"
                if acc_id == "account_1":
                    acc_name = "Tài khoản Muse 1 (Mặc định)"
                data.setdefault("accounts", []).append({
                    "id": acc_id,
                    "name": acc_name,
                    "status": "READY" if has_cookies else "NEED_LOGIN",
                    "created_at": p.stat().st_ctime,
                    "vm_id": vm_id,
                    "tokens": 1000000000,
                    "tokens_used": 0
                })
                existing_ids.add(acc_id)
                idx += 1
                discovered = True

    # Auto-migration: if accounts list is still empty, import existing ~/.config/muse-cli session as account_1
    if not data.get("accounts"):
        def_cookies = _get_default_muse_cookies_path()
        if def_cookies.is_file() and def_cookies.stat().st_size > 50:
            acc_id = "account_1"
            acc_dir = PROFILES_ROOT / acc_id / ".config" / "muse-cli"
            acc_dir.mkdir(parents=True, exist_ok=True)
            acc_cookies = acc_dir / "cookies.txt"
            acc_config = acc_dir / "config.json"

            try:
                shutil.copy2(def_cookies, acc_cookies)
                def_cfg_path = _get_default_muse_config_path()
                cfg_content = {}
                if def_cfg_path.is_file():
                    try:
                        cfg_content = json.loads(def_cfg_path.read_text(encoding="utf-8"))
                    except Exception:
                        pass
                cfg_content["cookies_file"] = str(acc_cookies)
                _atomic_write_json(acc_config, cfg_content)

                data["accounts"].append({
                    "id": acc_id,
                    "name": "Tài khoản Muse 1 (Mặc định)",
                    "status": "READY",
                    "created_at": time.time(),
                    "vm_id": cfg_content.get("vm_id")
                })
                data["active_id"] = acc_id
                discovered = True
            except Exception as e:
                print(f"[MUSE_ACCOUNTS_WARN] Auto-migration failed: {e}", flush=True)

    if discovered:
        _atomic_write_json(REGISTRY_PATH, data)

    return data


def save_registry(data: dict[str, Any]) -> None:
    _atomic_write_json(REGISTRY_PATH, data)


def get_account_profile_home(account_id: str) -> Path:
    return PROFILES_ROOT / account_id


def get_account_cli_dir(account_id: str) -> Path:
    return get_account_profile_home(account_id) / ".config" / "muse-cli"


def list_accounts() -> list[dict[str, Any]]:
    reg = load_registry()
    active_id = reg.get("active_id", "")
    result = []
    for acc in reg.get("accounts", []):
        acc_id = acc["id"]
        cli_dir = get_account_cli_dir(acc_id)
        cookies_file = cli_dir / "cookies.txt"
        has_cookies = cookies_file.is_file() and cookies_file.stat().st_size > 50

        # Sync ready status based on cookies presence
        status = acc.get("status", "NEED_LOGIN")
        if not has_cookies:
            status = "NEED_LOGIN"

        tokens = int(acc.get("tokens", 1000000000))
        tokens_used = int(acc.get("tokens_used", 0))

        result.append({
            "id": acc_id,
            "name": acc.get("name") or f"Tài khoản {acc_id}",
            "status": status,
            "active": acc_id == active_id,
            "ready": status == "READY",
            "tokens": tokens,
            "tokens_used": tokens_used,
            "proxy": acc.get("proxy"),
            "created_at": acc.get("created_at", 0),
            "vm_id": acc.get("vm_id")
        })
    return result


def get_active_id() -> str:
    reg = load_registry()
    return str(reg.get("active_id", ""))


def get_dispatch_mode() -> str:
    reg = load_registry()
    return str(reg.get("dispatch_mode", "round_robin"))


def set_dispatch_mode(mode: str) -> str:
    mode = "round_robin" if mode == "round_robin" else "active_only"
    reg = load_registry()
    reg["dispatch_mode"] = mode
    save_registry(reg)
    return mode


def select_account(account_id: str) -> bool:
    reg = load_registry()
    if any(a["id"] == account_id for a in reg.get("accounts", [])):
        reg["active_id"] = account_id
        save_registry(reg)
        _sync_active_to_system_default(account_id)
        return True
    return False


def get_account(account_id: str) -> dict[str, Any] | None:
    reg = load_registry()
    for acc in reg.get("accounts", []):
        if acc["id"] == account_id:
            profile_home = get_account_profile_home(account_id)
            cli_dir = get_account_cli_dir(account_id)
            return {
                **acc,
                "profile_home": profile_home,
                "cookies_file": cli_dir / "cookies.txt",
                "config_file": cli_dir / "config.json"
            }
    return None


def get_ready_accounts() -> list[dict[str, Any]]:
    accs = list_accounts()
    ready_ids = [a["id"] for a in accs if a["ready"]]
    result = []
    for aid in ready_ids:
        acc = get_account(aid)
        if acc:
            result.append(acc)
    return result


def get_account_for_scene(scene_number: int, exclude_ids: list[str] | None = None) -> dict[str, Any] | None:
    """Returns the allocated Muse account for the given scene number.
    
    If dispatch_mode == 'round_robin', distributes scenes evenly across all ready accounts:
      Scene 1 -> Account 1
      Scene 2 -> Account 2
      Scene 3 -> Account 3
      ...
    If dispatch_mode == 'active_only', returns the currently active account.
    Supports auto-failover by excluding accounts in exclude_ids.
    """
    exclude = set(exclude_ids or [])
    reg = load_registry()
    mode = reg.get("dispatch_mode", "round_robin")
    ready = [a for a in get_ready_accounts() if a["id"] not in exclude]

    if not ready:
        # Fallback to any ready account ignoring exclusions if all failed
        ready = get_ready_accounts()
        if not ready:
            return None

    # Prioritize accounts with remaining tokens > 0
    with_tokens = [a for a in ready if int(a.get("tokens", 50)) > 0]
    candidate_pool = with_tokens if with_tokens else ready

    if mode == "round_robin":
        # Round-robin distribution: (scene_number - 1) % len(candidate_pool)
        idx = max(0, int(scene_number) - 1) % len(candidate_pool)
        return candidate_pool[idx]
    else:
        # Active only
        active_id = reg.get("active_id", "")
        for acc in candidate_pool:
            if acc["id"] == active_id:
                return acc
        return candidate_pool[0]


def create_account(name: str = "") -> dict[str, Any]:
    reg = load_registry()
    accounts = reg.get("accounts", [])
    count = len(accounts) + 1
    acc_id = f"account_{uuid.uuid4().hex[:8]}"
    acc_name = name.strip() or f"Tài khoản Muse {count}"

    cli_dir = get_account_cli_dir(acc_id)
    cli_dir.mkdir(parents=True, exist_ok=True)

    new_acc = {
        "id": acc_id,
        "name": acc_name,
        "status": "NEED_LOGIN",
        "created_at": time.time(),
        "vm_id": None
    }
    accounts.append(new_acc)
    if not reg.get("active_id"):
        reg["active_id"] = acc_id
    save_registry(reg)
    return new_acc


def rename_account(account_id: str, new_name: str) -> bool:
    new_name = str(new_name or "").strip()
    if not new_name:
        return False
    reg = load_registry()
    for acc in reg.get("accounts", []):
        if acc["id"] == account_id:
            acc["name"] = new_name
            save_registry(reg)
            return True
    return False


def set_account_tokens(account_id: str, tokens: int) -> bool:
    """Set the exact remaining token/credit count for an account."""
    try:
        tokens = max(0, int(tokens))
    except (ValueError, TypeError):
        return False
    reg = load_registry()
    for acc in reg.get("accounts", []):
        if acc["id"] == account_id:
            acc["tokens"] = tokens
            save_registry(reg)
            return True
    return False


def decrement_account_token(account_id: str, count: int = 1) -> int:
    """Decrement token count when a video scene is generated."""
    reg = load_registry()
    current = 0
    for acc in reg.get("accounts", []):
        if acc["id"] == account_id:
            current = max(0, int(acc.get("tokens", 1000000000)) - count)
            acc["tokens"] = current
            acc["tokens_used"] = int(acc.get("tokens_used", 0)) + count
            save_registry(reg)
            return current
    return current


def delete_account(account_id: str) -> bool:
    reg = load_registry()
    accounts = reg.get("accounts", [])
    remaining = [a for a in accounts if a["id"] != account_id]
    if len(remaining) == len(accounts):
        return False

    reg["accounts"] = remaining
    if reg.get("active_id") == account_id:
        reg["active_id"] = remaining[0]["id"] if remaining else ""
    save_registry(reg)

    # Clean up profile home directory
    try:
        shutil.rmtree(get_account_profile_home(account_id), ignore_errors=True)
    except Exception:
        pass
    return True


def save_account_session(account_id: str, cookies_content: str, vm_id: str | None = None) -> bool:
    """Saves verified cookies into account's isolated config directory."""
    cli_dir = get_account_cli_dir(account_id)
    cli_dir.mkdir(parents=True, exist_ok=True)
    cookies_path = cli_dir / "cookies.txt"
    config_path = cli_dir / "config.json"

    cookies_path.write_text(cookies_content.strip() + "\n", encoding="utf-8")
    cfg = {
        "cookies_file": str(cookies_path),
        "node_id": uuid.uuid4().hex[:16]
    }
    if vm_id:
        cfg["vm_id"] = vm_id
    _atomic_write_json(config_path, cfg)

    # Update account status in registry
    reg = load_registry()
    for acc in reg.get("accounts", []):
        if acc["id"] == account_id:
            acc["status"] = "READY"
            if vm_id:
                acc["vm_id"] = vm_id
            break
    save_registry(reg)

    # If this is active account, sync to system default ~/.config/muse-cli for cli tool compatibility
    if reg.get("active_id") == account_id:
        _sync_active_to_system_default(account_id)
    return True


def _sync_active_to_system_default(account_id: str) -> None:
    try:
        cli_dir = get_account_cli_dir(account_id)
        acc_cookies = cli_dir / "cookies.txt"
        if acc_cookies.is_file():
            sys_dir = Path(os.path.expanduser("~/.config/muse-cli"))
            sys_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(acc_cookies, sys_dir / "cookies.txt")
            acc_cfg = cli_dir / "config.json"
            if acc_cfg.is_file():
                shutil.copy2(acc_cfg, sys_dir / "config.json")
    except Exception as e:
        print(f"[MUSE_ACCOUNTS_WARN] Sync to system default failed: {e}", flush=True)



def parse_cookie_input(raw: str) -> list[dict[str, Any]]:
    raw = (raw or "").strip()
    if not raw:
        return []

    # 1. Try JSON array / object
    if raw.startswith("[") or raw.startswith("{"):
        try:
            data = json.loads(raw)
            items = data if isinstance(data, list) else data.get("cookies", data.get("items", []))
            jar = []
            for c in items:
                if isinstance(c, dict) and c.get("name") and c.get("value"):
                    d = str(c.get("domain") or ".muse.ai").lower()
                    jar.append({
                        "name": str(c["name"]).strip(),
                        "value": str(c["value"]).strip(),
                        "domain": d,
                        "path": str(c.get("path") or "/"),
                        "secure": bool(c.get("secure", True)),
                        "expires": int(float(c.get("expires") or 0))
                    })
            if jar:
                return jar
        except Exception:
            pass

    # 2. Try cURL header format (-H 'cookie: ...' or -H "cookie: ...")
    if "curl " in raw.lower() and "-h " in raw.lower():
        import re
        m = re.search(r"-H\s+['\"]cookie:\s*([^'\"]+)['\"]", raw, re.IGNORECASE)
        if m:
            raw = m.group(1).strip()

    # 3. Try Netscape format
    lines = raw.splitlines()
    netscape_jar = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) >= 7:
            netscape_jar.append({
                "domain": parts[0].strip(),
                "secure": parts[3].upper() == "TRUE",
                "path": parts[2].strip() or "/",
                "expires": int(float(parts[4])) if parts[4].replace(".", "", 1).isdigit() else 0,
                "name": parts[5].strip(),
                "value": parts[6].strip()
            })
        elif len(parts) >= 6:
            netscape_jar.append({
                "domain": parts[0].strip(),
                "secure": True,
                "path": parts[2].strip() or "/",
                "expires": 0,
                "name": parts[4].strip(),
                "value": parts[5].strip()
            })
    if netscape_jar:
        return netscape_jar

    # 4. Try raw key=value; key=value header format (e.g. copied from DevTools Application/Network)
    cleaned = raw.replace("\r\n", "; ").replace("\n", "; ")
    header_jar = []
    for token in cleaned.split(";"):
        token = token.strip()
        if "=" in token:
            k, v = token.split("=", 1)
            k = k.strip()
            v = v.strip()
            if k and v:
                header_jar.append({
                    "name": k,
                    "value": v,
                    "domain": ".muse.ai",
                    "path": "/",
                    "secure": True,
                    "expires": 0
                })
    return header_jar


def format_netscape_cookies(jar: list[dict[str, Any]]) -> str:
    lines = ["# Netscape HTTP Cookie File"]
    for c in jar:
        domain = c.get("domain", ".muse.ai")
        if not domain.startswith("."):
            domain = "." + domain
        lines.append("\t".join([
            domain,
            "TRUE",
            c.get("path", "/"),
            "TRUE" if c.get("secure", True) else "FALSE",
            str(int(c.get("expires", 0) or 0)),
            c["name"],
            c["value"]
        ]))
    return "\n".join(lines) + "\n"


def import_raw_cookies(account_id: str | None, raw_input: str, name: str = "") -> dict[str, Any]:
    jar = parse_cookie_input(raw_input)
    if not jar:
        raise ValueError("Không tìm thấy thông tin cookie nào trong nội dung đã dán.")

    sess = next((c for c in jar if c.get("name") == "hatch_sess" and c.get("value")), None)
    if not sess:
        raise ValueError("Thiếu cookie 'hatch_sess'. Vui lòng copy chuỗi cookie có chứa 'hatch_sess='.")

    if not account_id:
        acc = create_account(name or "Tài khoản Muse mới")
        target_id = acc["id"]
    else:
        target_id = account_id
        if not get_account(target_id):
            create_account(name or f"Tài khoản {target_id}")

    header = "; ".join(c["name"] + "=" + c["value"] for c in jar)
    import muse_video_provider
    verify_res = muse_video_provider.verify_muse_header(header)
    if not verify_res.get("ok"):
        raise RuntimeError(verify_res.get("error") or "Không xác minh được phiên Muse. Hãy kiểm tra lại tài khoản.")

    vm_id = verify_res.get("vm_id")
    cookie_str = format_netscape_cookies(jar)
    save_account_session(target_id, cookie_str, vm_id=vm_id)

    acc = get_account(target_id)
    acc_name = (acc.get("name") if acc else None) or target_id
    return {
        "ok": True,
        "ready": True,
        "account_id": target_id,
        "vm_id": vm_id,
        "name": acc_name,
        "message": f"Đã lưu và xác minh thành công '{acc_name}'. Sẵn sàng sản xuất video!"
    }


# ---------------------------------------------------------------------------
# PROXY AUTO-MAPPING & MANAGEMENT
# ---------------------------------------------------------------------------

def parse_proxy_string(raw: str) -> str:
    """Normalizes any standard proxy string format into standard URI:
    - ip:port -> http://ip:port
    - ip:port:user:pass -> http://user:pass@ip:port
    - user:pass@ip:port -> http://user:pass@ip:port
    - socks5://... -> socks5://...
    """
    s = str(raw or "").strip()
    if not s:
        return ""
    if s.startswith("http://") or s.startswith("https://") or s.startswith("socks5://"):
        return s
    parts = s.split(":")
    if len(parts) == 4:
        # ip:port:user:pass
        ip, port, user, pw = parts
        return f"http://{user}:{pw}@{ip}:{port}"
    elif len(parts) == 2:
        # ip:port
        return f"http://{parts[0]}:{parts[1]}"
    elif "@" in s:
        return f"http://{s}"
    return s


def probe_proxy(proxy_url: str, target_url: str = "https://muse.ai", timeout: float = 4.0) -> bool:
    """Quickly tests if a proxy can connect to target_url without timeout or block."""
    try:
        from curl_cffi import requests as rq
        r = rq.get(target_url, proxy=proxy_url, impersonate="chrome", timeout=timeout)
        return r.status_code in (200, 301, 302, 401, 403)
    except Exception:
        try:
            import urllib.request
            handler = urllib.request.ProxyHandler({"http": proxy_url, "https": proxy_url})
            opener = urllib.request.build_opener(handler)
            req = urllib.request.Request(target_url, headers={"User-Agent": "Mozilla/5.0"})
            with opener.open(req, timeout=timeout) as resp:
                return resp.status in (200, 301, 302, 401, 403)
        except Exception:
            return False


def assign_proxies_to_accounts(proxies: list[str], filter_live: bool = True) -> dict[str, Any]:
    """Automatically maps a list of proxies to Muse accounts.
    - If filter_live is True, concurrently tests each proxy against https://muse.ai and skips dead/blocked IPs.
    - Distributes live proxies sequentially across accounts (Round-robin if fewer proxies than accounts).
    """
    cleaned = [parse_proxy_string(p) for p in proxies if p.strip() and not p.strip().startswith("#")]
    if not cleaned:
        raise ValueError("Danh sách proxy trống hoặc không có dòng nào hợp lệ.")

    live_proxies = []
    dead_proxies = []

    if filter_live:
        print(f"[MUSE_PROXY] Đang kiểm tra song song {len(cleaned)} proxy với máy chủ Muse.ai...", flush=True)
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(cleaned), 10)) as executor:
            future_to_proxy = {executor.submit(probe_proxy, p, "https://muse.ai", 4.5): p for p in cleaned}
            for fut in concurrent.futures.as_completed(future_to_proxy):
                p = future_to_proxy[fut]
                try:
                    if fut.result():
                        live_proxies.append(p)
                    else:
                        dead_proxies.append(p)
                except Exception:
                    dead_proxies.append(p)
    else:
        live_proxies = cleaned

    if not live_proxies:
        raise RuntimeError(
            f"Tất cả {len(cleaned)} proxy đều không kết nối được tới máy chủ Muse.ai "
            f"(Bị timeout/drop gói tin do máy chủ Muse.ai chặn dải IP này, hoặc sai cổng/mật khẩu). "
            f"Vui lòng kiểm tra lại nhà cung cấp proxy hoặc dùng IP trực tiếp."
        )

    reg = load_registry()
    accounts = reg.get("accounts", [])
    if not accounts:
        raise RuntimeError("Chưa có tài khoản Muse nào trong hệ thống để gán proxy.")

    num_live = len(live_proxies)
    mapped = []

    for i, acc in enumerate(accounts):
        chosen_proxy = live_proxies[i % num_live]
        acc["proxy"] = chosen_proxy

        # Sync to local config.json in profile
        cli_dir = get_account_cli_dir(acc["id"])
        cli_dir.mkdir(parents=True, exist_ok=True)
        cfg_file = cli_dir / "config.json"
        cfg_data = {}
        if cfg_file.is_file():
            try:
                cfg_data = json.loads(cfg_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        cfg_data["proxy"] = chosen_proxy
        _atomic_write_json(cfg_file, cfg_data)

        mapped.append({
            "account_id": acc["id"],
            "account_name": acc.get("name") or acc["id"],
            "proxy": chosen_proxy
        })

    save_registry(reg)

    msg = f"Đã kiểm tra {len(cleaned)} proxy: {num_live} proxy kết nối tốt với Muse.ai"
    if dead_proxies:
        msg += f" (Đã tự động loại bỏ {len(dead_proxies)} proxy bị timeout/chặn)"
    msg += f". Đã phân bổ tối ưu cho toàn bộ {len(accounts)} tài khoản!"

    return {
        "ok": True,
        "total_accounts": len(accounts),
        "total_proxies": len(cleaned),
        "live_proxies_count": num_live,
        "dead_proxies_count": len(dead_proxies),
        "mapping": mapped,
        "message": msg
    }


def import_proxies_from_file(file_path: Path | str | None = None) -> dict[str, Any]:
    """Reads proxies from a text file (default: studio/proxies.txt) and auto-assigns."""
    target_p = Path(file_path) if file_path else (HOME / "proxies.txt")
    if not target_p.is_file():
        raise FileNotFoundError(f"Không tìm thấy tệp danh sách proxy: {target_p}")

    lines = target_p.read_text(encoding="utf-8", errors="replace").splitlines()
    return assign_proxies_to_accounts(lines)


def remove_all_proxies() -> dict[str, Any]:
    """Removes proxy settings from all accounts."""
    reg = load_registry()
    for acc in reg.get("accounts", []):
        acc.pop("proxy", None)
        cli_dir = get_account_cli_dir(acc["id"])
        cfg_file = cli_dir / "config.json"
        if cfg_file.is_file():
            try:
                cfg_data = json.loads(cfg_file.read_text(encoding="utf-8"))
                cfg_data.pop("proxy", None)
                _atomic_write_json(cfg_file, cfg_data)
            except Exception:
                pass
    save_registry(reg)
    return {"ok": True, "message": "Đã xóa toàn bộ cấu hình proxy của các tài khoản."}


def get_account_proxy(account_id: str) -> str | None:
    acc = get_account(account_id)
    return acc.get("proxy") if acc else None
