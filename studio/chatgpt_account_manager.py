"""ChatGPT Web Account & Multi-Account Lifecycle Manager for Storyboard AI Studio Pro.
Supports multiple ChatGPT accounts with isolated Chrome profiles, auto-launch,
auto-close to keep RAM free, and automatic rotation on image quota limits.
"""
from __future__ import annotations

import importlib
import json
from pathlib import Path
import sys
import time
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FLOWKIT_APP = PROJECT_ROOT / "flowkit" / "app"
if not FLOWKIT_APP.is_dir():
    FLOWKIT_APP = Path("D:/FLOWKIT/app")
if str(FLOWKIT_APP) not in sys.path:
    sys.path.insert(0, str(FLOWKIT_APP))

import chatgpt_browser

CDP_PORT = 9468
CHATGPT_PROFILE = PROJECT_ROOT / "profiles" / "chatgpt_web"
LOGIN_STATE_FILE = CHATGPT_PROFILE / "login_state.json"


def _read_login_state() -> Dict[str, Any]:
    prof_dir, _, _ = chatgpt_browser.get_active_profile()
    state_file = prof_dir / "login_state.json"
    if state_file.exists():
        try:
            return json.loads(state_file.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_login_state(data: Dict[str, Any]):
    try:
        _, _, acc_id = chatgpt_browser.get_active_profile()
        patch = {}
        if "logged_in" in data:
            patch["logged_in"] = bool(data["logged_in"])
        if data.get("email"):
            patch["email"] = str(data["email"])
        chatgpt_browser.update_account_state(acc_id, **patch)
    except Exception:
        pass


def open_chatgpt_login_ui() -> Dict[str, Any]:
    try:
        from engine_orchestrator import close_engine_browser
        close_engine_browser("flow")
        time.sleep(0.5)
    except Exception:
        pass

    importlib.reload(chatgpt_browser)
    return chatgpt_browser.open_chatgpt_browser(show=True)


def add_chatgpt_account_ui() -> Dict[str, Any]:
    try:
        from engine_orchestrator import close_engine_browser
        close_engine_browser("flow")
        time.sleep(0.4)
    except Exception:
        pass

    importlib.reload(chatgpt_browser)
    return chatgpt_browser.add_chatgpt_account(show=True)


def select_chatgpt_account_ui(account_id: str) -> Dict[str, Any]:
    importlib.reload(chatgpt_browser)
    return chatgpt_browser.select_chatgpt_account(account_id, close_others=True)


def rotate_chatgpt_account_ui(reason: str = "Manual rotation") -> Dict[str, Any]:
    importlib.reload(chatgpt_browser)
    next_acc = chatgpt_browser.rotate_chatgpt_account(reason=reason, cooldown_seconds=0)
    if next_acc:
        return {
            "success": True,
            "account": next_acc,
            "message": f"Đã chuyển sang {next_acc.get('label')} (Cổng {next_acc.get('port')}).",
        }
    return {
        "success": False,
        "message": "Chưa có tài khoản ChatGPT dự phòng nào khác. Bấm '➕ Thêm TK' để thêm tài khoản mới!",
    }


def delete_chatgpt_account_ui(account_id: str = "") -> Dict[str, Any]:
    importlib.reload(chatgpt_browser)
    return chatgpt_browser.delete_chatgpt_account(account_id=account_id or None)


def lock_chatgpt_ui() -> Dict[str, Any]:
    importlib.reload(chatgpt_browser)
    chatgpt_browser.lock_chatgpt_browser()
    return {
        "success": True,
        "message": "Đã thu nhỏ cửa sổ ChatGPT Web xuống thanh tác vụ an toàn.",
    }


def close_chatgpt_ui() -> Dict[str, Any]:
    importlib.reload(chatgpt_browser)
    ok = chatgpt_browser.close_chatgpt_browser()
    return {
        "success": ok,
        "message": "Đã đóng hoàn toàn trình duyệt Chrome ChatGPT để giải phóng bộ nhớ RAM.",
    }


def get_chatgpt_ui_status() -> Dict[str, Any]:
    importlib.reload(chatgpt_browser)
    accounts = chatgpt_browser.list_accounts()
    active_acc = chatgpt_browser.get_active_account()
    active_id = str(active_acc.get("id") or "cgpt_1")
    active_label = str(active_acc.get("label") or "Tài khoản 1")
    active_port = int(active_acc.get("port") or CDP_PORT)

    running_port = chatgpt_browser.get_running_port()
    alive = running_port is not None
    effective_port = int(running_port or active_port)

    # Identify which account owns the currently running browser
    running_acc = next((a for a in accounts if int(a.get("port") or 0) == effective_port), active_acc)
    running_id = str(running_acc.get("id") or active_id)
    running_label = str(running_acc.get("label") or active_label)

    logged_in = bool(running_acc.get("logged_in", False))
    if alive:
        try:
            import chatgpt_webtool
            importlib.reload(chatgpt_webtool)
            chk = chatgpt_webtool.check_chatgpt_login_status(port=effective_port)
            if chk.get("ok"):
                logged_in = bool(chk.get("logged_in", False))
                email = str(chk.get("email") or "").strip()
                chatgpt_browser.update_account_state(
                    running_id,
                    logged_in=logged_in,
                    email=email or None,
                )
                accounts = chatgpt_browser.list_accounts()
        except Exception:
            pass

    total_accounts = len(accounts)
    ready_count = sum(1 for a in accounts if a.get("logged_in"))
    summary_suffix = (
        f" · {ready_count}/{total_accounts} TK sẵn sàng"
        if total_accounts > 1
        else " · 1 TK"
    )

    if alive:
        status_text = (
            f"✓ Đang mở {running_label} (Cổng {effective_port}{summary_suffix})"
            if logged_in
            else f"⏳ Đang mở {running_label} (Cổng {effective_port}) — Chờ đăng nhập"
        )
        badge = f"🟢 Sẵn sàng ({ready_count}/{total_accounts})" if (logged_in and total_accounts > 1) else ("🟢 Sẵn sàng" if logged_in else "🟡 Chờ đăng nhập")
    elif ready_count > 0:
        logged_in = True
        status_text = (
            f"✓ Đã kết nối {ready_count}/{total_accounts} tài khoản (Tự xoay khi hết lượt)"
            if total_accounts > 1
            else "✓ Đã kết nối (Tự động bật khi tạo ảnh)"
        )
        badge = f"🟢 {ready_count} TK sẵn sàng" if total_accounts > 1 else "🟢 Sẵn sàng"
    else:
        logged_in = False
        status_text = f"Chưa kết nối (Cổng {active_port}{summary_suffix})"
        badge = "⚪ Chưa kết nối"

    safe_accounts = [
        {
            "id": a.get("id"),
            "label": a.get("label"),
            "port": a.get("port"),
            "email": a.get("email", ""),
            "logged_in": bool(a.get("logged_in", False)),
            "cooldown_until": a.get("cooldown_until", 0),
            "active": a.get("id") == active_id,
        }
        for a in accounts
    ]

    return {
        "online": alive,
        "logged_in": logged_in,
        "port": effective_port,
        "active_id": active_id,
        "active_label": active_label,
        "total_accounts": total_accounts,
        "ready_accounts": ready_count,
        "accounts": safe_accounts,
        "status_text": status_text,
        "badge": badge,
    }
