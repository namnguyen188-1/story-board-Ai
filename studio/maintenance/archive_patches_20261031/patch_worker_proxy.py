# -*- coding: utf-8 -*-
import sys
import os

sys.stdout.reconfigure(encoding="utf-8")

def patch_gateway_worker():
    path = os.path.join("studio", "muse_gateway_worker.py")
    with open(path, "r", encoding="utf-8") as f:
        code = f.read()

    old_target = """        elif args.action == "status":
            request = json.loads(Path(args.request).read_text(encoding="utf-8")) if args.request else {}
            if request.get("account_home"):
                os.environ["USERPROFILE"] = str(request["account_home"])
            api = GatewayAPI()"""

    new_target = """        elif args.action == "status":
            request = json.loads(Path(args.request).read_text(encoding="utf-8")) if args.request else {}
            if request.get("account_home"):
                os.environ["USERPROFILE"] = str(request["account_home"])
            acc_id = request.get("account_id")
            if acc_id:
                try:
                    import muse_accounts
                    proxy_url = muse_accounts.get_account_proxy(acc_id)
                    if proxy_url:
                        os.environ["HTTP_PROXY"] = proxy_url
                        os.environ["HTTPS_PROXY"] = proxy_url
                        os.environ["ALL_PROXY"] = proxy_url
                    else:
                        for k in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"):
                            os.environ.pop(k, None)
                except Exception:
                    pass
            api = GatewayAPI()"""

    if old_target in code:
        code = code.replace(old_target, new_target)
        print("[✓] Patched proxy support for status action in muse_gateway_worker.py")
    else:
        # Check CRLF
        old_target_crlf = old_target.replace("\n", "\r\n")
        new_target_crlf = new_target.replace("\n", "\r\n")
        if old_target_crlf in code:
            code = code.replace(old_target_crlf, new_target_crlf)
            print("[✓] Patched proxy support for status action in muse_gateway_worker.py (CRLF)")
        else:
            print("[!] old_target not found in muse_gateway_worker.py")

    with open(path, "w", encoding="utf-8") as f:
        f.write(code)

if __name__ == "__main__":
    patch_gateway_worker()
