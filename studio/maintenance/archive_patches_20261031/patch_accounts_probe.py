# -*- coding: utf-8 -*-
import sys
import os
import concurrent.futures

sys.stdout.reconfigure(encoding="utf-8")

def update_muse_accounts():
    path = os.path.join("studio", "muse_accounts.py")
    with open(path, "r", encoding="utf-8") as f:
        code = f.read()

    new_assign_code = '''def probe_proxy(proxy_url: str, target_url: str = "https://muse.ai", timeout: float = 4.0) -> bool:
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
    }'''

    target = "def assign_proxies_to_accounts(proxies: list[str]) -> dict[str, Any]:"
    if target in code:
        # Find where import_proxies_from_file begins
        end_idx = code.find("def import_proxies_from_file", code.find(target))
        code = code[:code.find(target)] + new_assign_code + "\n\n\n" + code[end_idx:]
        print("[✓] Patched assign_proxies_to_accounts with auto-probe & filter in muse_accounts.py")

    with open(path, "w", encoding="utf-8") as f:
        f.write(code)

if __name__ == "__main__":
    update_muse_accounts()
