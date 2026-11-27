"""ChatGPT Web Automation & Image Extractor for Storyboard AI / FlowKit.
Operates via Chrome DevTools Protocol (CDP) on the active ChatGPT account port (9468+).
Compatible with modern ProseMirror contenteditable prompt boxes, multilingual UI,
and automatic multi-account rotation on daily image quota limits.
"""
from __future__ import annotations

import base64
import io
import json
from pathlib import Path
import shutil
import tempfile
import time
from typing import Dict, Any, Optional
import urllib.request

from PIL import Image

try:
    from websockets.sync.client import connect
except ImportError:
    connect = None

CDP_PORT = 9468
_CDP_MSG_COUNTER = 10


def _next_msg_id() -> int:
    global _CDP_MSG_COUNTER
    _CDP_MSG_COUNTER += 1
    return _CDP_MSG_COUNTER


def _resolve_port(port: Optional[int] = None) -> int:
    if port is not None:
        return int(port)
    try:
        import chatgpt_browser
        running = chatgpt_browser.get_running_port()
        if running:
            return int(running)
        _, active_port, _ = chatgpt_browser.get_active_profile()
        return int(active_port)
    except Exception:
        return CDP_PORT


def get_chatgpt_tab(port: Optional[int] = None) -> Optional[Dict[str, Any]]:
    target_port = _resolve_port(port)
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{target_port}/json", timeout=2.0) as r:
            tabs = json.loads(r.read().decode("utf-8"))
        for t in tabs:
            url = str(t.get("url", ""))
            if "chatgpt.com" in url and t.get("type") == "page":
                return t
        for t in tabs:
            if t.get("type") == "page":
                return t
    except Exception:
        pass
    return None


def execute_cdp_command(
    ws_url: str,
    method: str,
    params: Optional[Dict[str, Any]] = None,
    msg_id: Optional[int] = None,
    timeout: float = 20.0,
) -> Dict[str, Any]:
    if not connect:
        raise RuntimeError("WEBSOCKETS_LIBRARY_MISSING")
    req_id = int(msg_id) if msg_id is not None else _next_msg_id()
    payload = {"id": req_id, "method": method, "params": params or {}}
    with connect(ws_url, open_timeout=6, close_timeout=4, max_size=64 * 1024 * 1024) as ws:
        ws.send(json.dumps(payload))
        deadline = time.time() + float(timeout)
        while time.time() < deadline:
            resp_raw = ws.recv(timeout=max(0.5, deadline - time.time()))
            resp = json.loads(resp_raw)
            if resp.get("id") == req_id:
                return resp
        raise TimeoutError(f"CDP command timed out: {method}")


def check_chatgpt_login_status(port: Optional[int] = None) -> Dict[str, Any]:
    tab = get_chatgpt_tab(port=port)
    if not tab:
        return {"ok": False, "error": "NO_CHATGPT_TAB"}
    ws_url = tab.get("webSocketDebuggerUrl")
    if not ws_url:
        return {"ok": False, "error": "NO_WS_URL"}

    js_check = """
    (() => {
        const promptEl = document.querySelector('div[contenteditable="true"]') || document.querySelector('#prompt-textarea');
        const loginBtn = document.querySelector('button[data-testid="login-button"]') || document.querySelector('a[href*="/login"]');
        const signupBtn = document.querySelector('button[data-testid="signup-button"]') || document.querySelector('a[href*="/signup"]');

        const textSample = document.body.innerText || '';
        const hasSidebarOrMenu = textSample.includes('Trò chuyện mới') ||
                                 textSample.includes('New chat') ||
                                 textSample.includes('Thư viện') ||
                                 textSample.includes('Khám phá') ||
                                 textSample.includes('Đã ghim') ||
                                 document.cookie.includes('oai-client-session') ||
                                 document.cookie.includes('_account');

        const is_logged_in = (!!promptEl || hasSidebarOrMenu) && !loginBtn;
        let email = '';
        const m = textSample.match(/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}/);
        if (m) email = m[0];
        return {
            has_prompt: !!promptEl,
            has_login_btn: !!loginBtn,
            has_signup_btn: !!signupBtn,
            has_sidebar: hasSidebarOrMenu,
            logged_in: is_logged_in,
            email: email,
            url: window.location.href,
            title: document.title
        };
    })()
    """
    try:
        res = execute_cdp_command(ws_url, "Runtime.evaluate", {"expression": js_check, "returnByValue": True})
        val = res.get("result", {}).get("result", {}).get("value", {})
        logged_in = bool(val.get("logged_in", False))
        return {
            "ok": True,
            "logged_in": logged_in,
            "email": val.get("email") or "",
            "details": val,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _ensure_fresh_chat(ws_url: str, current_url: str) -> None:
    """Starts from a clean https://chatgpt.com/ composer and waits for full profile/ProseMirror hydration."""
    cur = (current_url or "").lower()
    if "/c/" in cur or "chatgpt.com" not in cur:
        try:
            execute_cdp_command(ws_url, "Page.navigate", {"url": "https://chatgpt.com/"})
            time.sleep(1.5)
        except Exception:
            pass
    js_ready = """
    (() => {
        const txt = (document.body && document.body.innerText) || '';
        if (txt.includes('Loading profile')) return false;
        const el =
            document.querySelector('div.ProseMirror[contenteditable="true"]') ||
            document.querySelector('#prompt-textarea:not(#pending-home-input)') ||
            document.querySelector('div[contenteditable="true"][role="textbox"]');
        if (!el || el.id === 'pending-home-input') return false;
        const rect = el.getBoundingClientRect();
        return rect.width > 40 && rect.height > 12;
    })()
    """
    for _ in range(36):
        try:
            r = execute_cdp_command(ws_url, "Runtime.evaluate", {"expression": js_ready, "returnByValue": True})
            if r.get("result", {}).get("result", {}).get("value"):
                time.sleep(0.8)
                return
        except Exception:
            pass
        time.sleep(0.5)


def _validate_image_bytes(raw: bytes) -> Optional[tuple[int, int]]:
    if not raw or len(raw) < 5000:
        return None
    try:
        with Image.open(io.BytesIO(raw)) as im:
            im.load()
            w, h = im.size
        if w >= 256 and h >= 256:
            return (w, h)
    except Exception:
        return None
    return None


def _extract_image_bytes(ws_url: str, target_src: str) -> Optional[bytes]:
    """Downloads exact image bytes via authenticated in-browser fetch, native Chrome download, canvas, or HTTP."""
    # 1. Authenticated in-browser fetch (preserves full original PNG/JPEG/WebP without canvas taint)
    js_fetch_b64 = f"""
    (async () => {{
        const target = {json.dumps(target_src)};
        try {{
            const resp = await fetch(target, {{ credentials: 'include' }});
            if (!resp.ok) return {{ ok: false, err: 'http_' + resp.status }};
            const blob = await resp.blob();
            const dataUrl = await new Promise((resolve, reject) => {{
                const fr = new FileReader();
                fr.onloadend = () => resolve(fr.result);
                fr.onerror = reject;
                fr.readAsDataURL(blob);
            }});
            return {{ ok: true, dataUrl }};
        }} catch (e) {{
            return {{ ok: false, err: String(e) }};
        }}
    }})()
    """
    try:
        res = execute_cdp_command(ws_url, "Runtime.evaluate", {
            "expression": js_fetch_b64,
            "awaitPromise": True,
            "returnByValue": True,
        }, timeout=25.0)
        d_val = res.get("result", {}).get("result", {}).get("value", {}) or {}
        if d_val.get("ok") and d_val.get("dataUrl"):
            _, b64_data = str(d_val["dataUrl"]).split(",", 1)
            raw = base64.b64decode(b64_data)
            if _validate_image_bytes(raw):
                return raw
    except Exception:
        pass

    # 2. Native Chrome Download button / Browser.setDownloadBehavior (handles cross-origin oaiusercontent cleanly)
    tmp_dl = Path(tempfile.mkdtemp(prefix="cgpt_dl_"))
    try:
        try:
            execute_cdp_command(ws_url, "Browser.setDownloadBehavior", {
                "behavior": "allow",
                "downloadPath": str(tmp_dl),
                "eventsEnabled": False,
            })
        except Exception:
            execute_cdp_command(ws_url, "Page.setDownloadBehavior", {
                "behavior": "allow",
                "downloadPath": str(tmp_dl),
            })
        js_trigger_dl = f"""
        (() => {{
            const target = {json.dumps(target_src)};
            const turns = Array.from(document.querySelectorAll('[data-message-author-role="assistant"]'));
            const scope = turns.length ? turns[turns.length - 1] : document;
            const dlBtn = Array.from(scope.querySelectorAll('button, a')).find(el => {{
                const lbl = ((el.getAttribute('aria-label') || '') + ' ' + (el.getAttribute('data-testid') || '') + ' ' + (el.innerText || '')).toLowerCase();
                return lbl.includes('download') || lbl.includes('tải xuống') || lbl.includes('tải ảnh') || el.hasAttribute('download');
            }});
            if (dlBtn) {{
                dlBtn.click();
                return 'clicked_btn';
            }}
            const a = document.createElement('a');
            a.href = target;
            a.download = 'chatgpt_thumbnail.png';
            document.body.appendChild(a);
            a.click();
            a.remove();
            return 'clicked_anchor';
        }})()
        """
        execute_cdp_command(ws_url, "Runtime.evaluate", {"expression": js_trigger_dl, "returnByValue": True})
        for _ in range(24):
            time.sleep(0.5)
            files = [p for p in tmp_dl.iterdir() if p.is_file() and not p.name.endswith((".crdownload", ".tmp"))]
            if files:
                newest = max(files, key=lambda p: p.stat().st_mtime)
                raw = newest.read_bytes()
                if _validate_image_bytes(raw):
                    return raw
    except Exception:
        pass
    finally:
        shutil.rmtree(tmp_dl, ignore_errors=True)

    # 3. Canvas extraction fallback
    js_canvas = f"""
    (async () => {{
        const img = Array.from(document.querySelectorAll('img')).find(i => i.src === {json.dumps(target_src)});
        if (!img) return {{ ok: false }};
        try {{
            const canvas = document.createElement('canvas');
            canvas.width = img.naturalWidth;
            canvas.height = img.naturalHeight;
            canvas.getContext('2d').drawImage(img, 0, 0);
            return {{ ok: true, dataUrl: canvas.toDataURL('image/png') }};
        }} catch (e) {{
            return {{ ok: false, err: String(e) }};
        }}
    }})()
    """
    try:
        res = execute_cdp_command(ws_url, "Runtime.evaluate", {
            "expression": js_canvas,
            "awaitPromise": True,
            "returnByValue": True,
        }, timeout=20.0)
        d_val = res.get("result", {}).get("result", {}).get("value", {}) or {}
        if d_val.get("ok") and d_val.get("dataUrl"):
            _, b64_data = str(d_val["dataUrl"]).split(",", 1)
            raw = base64.b64decode(b64_data)
            if _validate_image_bytes(raw):
                return raw
    except Exception:
        pass

    # 4. Direct HTTP GET fallback (signed CDN URLs that don't require cookies)
    try:
        if target_src.startswith("http"):
            req = urllib.request.Request(target_src, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                raw = r.read()
            if _validate_image_bytes(raw):
                return raw
    except Exception:
        pass
    return None


def _get_top_conversation_id(ws_url: str) -> str:
    """Returns the most recent conversation UUID visible in ChatGPT sidebar/API, or ''."""
    js_top = """
    (async () => {
        try {
            const s = await fetch('/api/auth/session', { credentials: 'include' }).then(r => r.json());
            const token = (s && s.accessToken) ? String(s.accessToken) : '';
            const headers = token ? { 'Authorization': 'Bearer ' + token } : {};
            const r = await fetch('/backend-api/conversations?offset=0&limit=1', { credentials: 'include', headers });
            if (!r.ok) return '';
            const data = await r.json();
            const first = (Array.isArray(data && data.items) && data.items[0]) || null;
            return first && first.id ? String(first.id) : '';
        } catch (e) {
            return '';
        }
    })()
    """
    try:
        res = execute_cdp_command(
            ws_url,
            "Runtime.evaluate",
            {"expression": js_top, "awaitPromise": True, "returnByValue": True},
            timeout=10.0,
        )
        return str(res.get("result", {}).get("result", {}).get("value") or "").strip()
    except Exception:
        return ""


def _delete_chatgpt_conversation(ws_url: str, conv_id: str) -> bool:
    """Deletes (hides) the specified temporary thumbnail conversation ID from ChatGPT Web."""
    cid = str(conv_id or "").strip()
    if not cid:
        return False
    js_del = f"""
    (async () => {{
        const cid = {json.dumps(cid)};
        try {{
            const s = await fetch('/api/auth/session', {{ credentials: 'include' }}).then(r => r.json());
            const token = (s && s.accessToken) ? String(s.accessToken) : '';
            const headers = {{ 'Content-Type': 'application/json' }};
            if (token) headers['Authorization'] = 'Bearer ' + token;
            const r = await fetch('/backend-api/conversation/' + encodeURIComponent(cid), {{
                method: 'PATCH',
                credentials: 'include',
                headers,
                body: JSON.stringify({{ is_visible: false }})
            }});
            return {{ ok: r.ok, status: r.status }};
        }} catch (e) {{
            return {{ ok: false, err: String(e) }};
        }}
    }})()
    """
    try:
        res = execute_cdp_command(
            ws_url,
            "Runtime.evaluate",
            {"expression": js_del, "awaitPromise": True, "returnByValue": True},
            timeout=12.0,
        )
        val = res.get("result", {}).get("result", {}).get("value", {}) or {}
        return bool(val.get("ok"))
    except Exception:
        return False


def _cleanup_generated_conversation(ws_url: str, pre_conv_id: str = "") -> Optional[str]:
    """Resolves the newly created conversation ID for this thumbnail job and deletes it cleanly."""
    conv_id = ""
    try:
        r = execute_cdp_command(
            ws_url,
            "Runtime.evaluate",
            {
                "expression": "(window.location.pathname.match(/\\/c\\/([a-zA-Z0-9-]+)/) || [])[1] || ''",
                "returnByValue": True,
            },
            timeout=6.0,
        )
        conv_id = str(r.get("result", {}).get("result", {}).get("value") or "").strip()
    except Exception:
        conv_id = ""

    if not conv_id:
        top_id = _get_top_conversation_id(ws_url)
        if top_id and top_id != str(pre_conv_id or "").strip():
            conv_id = top_id

    if conv_id and _delete_chatgpt_conversation(ws_url, conv_id):
        print(f"[CHATGPT_WEBTOOL] 🗑️ Đã tự động xóa đoạn chat tạo thumbnail ({conv_id}) cho gọn tài khoản.", flush=True)
        return conv_id
    return None


def _generate_once(prompt: str, out_file: Path, timeout_seconds: int = 180) -> Dict[str, Any]:
    import chatgpt_browser

    _, active_port, acc_id = chatgpt_browser.get_active_profile()
    tab = get_chatgpt_tab(port=active_port)
    if not tab:
        chatgpt_browser.open_chatgpt_browser(show=False)
        for _ in range(20):
            time.sleep(0.5)
            tab = get_chatgpt_tab(port=active_port)
            if tab:
                break

    if not tab:
        return {"ok": False, "error": "CHATGPT_TAB_NOT_FOUND"}
    ws_url = tab.get("webSocketDebuggerUrl")
    if not ws_url:
        return {"ok": False, "error": "NO_WS_DEBUGGER_URL"}

    # Ensure Chrome stays hidden while running background automation
    try:
        chatgpt_browser._hide_chatgpt_window(port=active_port)
    except Exception:
        pass

    # Ensure clean prompt page (avoid stale threads/banners)
    _ensure_fresh_chat(ws_url, str(tab.get("url") or ""))
    try:
        chatgpt_browser._hide_chatgpt_window(port=active_port)
    except Exception:
        pass
    tab = get_chatgpt_tab(port=active_port) or tab
    ws_url = tab.get("webSocketDebuggerUrl") or ws_url

    # 1. Check login
    status = check_chatgpt_login_status(port=active_port)
    if not status.get("ok") or not status.get("logged_in"):
        chatgpt_browser.update_account_state(acc_id, logged_in=False, last_error="NOT_LOGGED_IN")
        return {
            "ok": False,
            "error": "CHATGPT_NOT_LOGGED_IN",
            "message": "Tài khoản ChatGPT Web chưa đăng nhập. Vui lòng bấm Đăng Nhập trên Storyboard AI trước khi tạo ảnh.",
        }

    if status.get("email"):
        chatgpt_browser.update_account_state(acc_id, logged_in=True, email=status["email"])
    else:
        chatgpt_browser.update_account_state(acc_id, logged_in=True)

    # 2. Capture pre-existing images, assistant turns, and previous top conversation ID
    pre_conv_id = _get_top_conversation_id(ws_url)
    js_count_pre = """
    (() => {
        return {
            imgs: Array.from(document.querySelectorAll('img')).map(i => i.src),
            msgCount: document.querySelectorAll('[data-message-author-role="assistant"]').length
        };
    })()
    """
    pre_res = execute_cdp_command(ws_url, "Runtime.evaluate", {"expression": js_count_pre, "returnByValue": True})
    pre_val = pre_res.get("result", {}).get("result", {}).get("value", {}) or {}
    pre_images = set(pre_val.get("imgs", []) or [])
    pre_msg_count = int(pre_val.get("msgCount") or 0)

    # 3. Focus real hydrated composer element (never #pending-home-input) and clear stale text
    js_focus_clear = """
    (() => {
        const el =
            document.querySelector('div.ProseMirror[contenteditable="true"]') ||
            document.querySelector('#prompt-textarea:not(#pending-home-input)') ||
            document.querySelector('div[contenteditable="true"][role="textbox"]');
        if (!el || el.id === 'pending-home-input') return { ok: false };
        const rect = el.getBoundingClientRect();
        el.focus();
        if (el.tagName === 'TEXTAREA') {
            el.value = '';
        } else {
            const sel = window.getSelection();
            const range = document.createRange();
            range.selectNodeContents(el);
            sel.removeAllRanges();
            sel.addRange(range);
            document.execCommand('delete', false, null);
        }
        return {
            ok: true,
            cx: Math.round(rect.left + Math.max(10, rect.width / 2)),
            cy: Math.round(rect.top + Math.max(8, rect.height / 2)),
        };
    })()
    """
    fc_res = execute_cdp_command(ws_url, "Runtime.evaluate", {"expression": js_focus_clear, "returnByValue": True})
    fc_val = fc_res.get("result", {}).get("result", {}).get("value", {}) or {}
    if not fc_val.get("ok"):
        return {"ok": False, "error": "CHATGPT_COMPOSER_NOT_READY", "message": "Ô nhập prompt ChatGPT Web chưa tải xong."}

    # Real mouse click at composer center ensures Chrome keyboard focus lands inside ProseMirror
    cx, cy = int(fc_val.get("cx") or 500), int(fc_val.get("cy") or 380)
    try:
        execute_cdp_command(ws_url, "Input.dispatchMouseEvent", {"type": "mousePressed", "x": cx, "y": cy, "button": "left", "clickCount": 1})
        execute_cdp_command(ws_url, "Input.dispatchMouseEvent", {"type": "mouseReleased", "x": cx, "y": cy, "button": "left", "clickCount": 1})
    except Exception:
        pass
    time.sleep(0.25)

    # 4. Normalize single-block prompt so embedded newlines cannot prematurely trigger Enter in ProseMirror
    clean_prompt = " ".join(str(prompt or "").replace("\r", " ").splitlines()).strip()
    execute_cdp_command(ws_url, "Input.insertText", {"text": clean_prompt})
    time.sleep(0.8)

    # Verify prompt text actually landed in composer (fallback if React hydration reset it)
    js_verify_text = """
    (() => {
        const el =
            document.querySelector('div.ProseMirror[contenteditable="true"]') ||
            document.querySelector('#prompt-textarea:not(#pending-home-input)') ||
            document.querySelector('div[contenteditable="true"][role="textbox"]');
        if (!el) return 0;
        return ((el.innerText || el.textContent || el.value || '').trim()).length;
    })()
    """
    vr = execute_cdp_command(ws_url, "Runtime.evaluate", {"expression": js_verify_text, "returnByValue": True})
    typed_len = int(vr.get("result", {}).get("result", {}).get("value") or 0)
    if typed_len < min(20, len(clean_prompt)):
        execute_cdp_command(ws_url, "Runtime.evaluate", {"expression": js_focus_clear, "returnByValue": True})
        time.sleep(0.3)
        execute_cdp_command(ws_url, "Input.insertText", {"text": clean_prompt})
        time.sleep(0.8)

    # 5. Click active send button (waiting up to 3s for React button state update) or press Enter fallback
    js_send = """
    (() => {
        const candidates = [
            document.querySelector('button[data-testid="send-button"]'),
            document.querySelector('button[data-testid="fruitjuice-send-button"]'),
            ...Array.from(document.querySelectorAll('form button, button[aria-label*="Send"], button[aria-label*="Gửi"]')).filter(b => {
                const lbl = ((b.getAttribute('aria-label') || '') + ' ' + (b.getAttribute('data-testid') || '') + ' ' + (b.innerText || '')).toLowerCase();
                return lbl.includes('send') || lbl.includes('gửi') || b.type === 'submit';
            })
        ].filter(Boolean);
        const sendBtn = candidates.find(b => !b.disabled && b.getAttribute('aria-disabled') !== 'true');
        if (sendBtn) {
            sendBtn.click();
            return { ok: true, method: 'click' };
        }
        return { ok: false };
    })()
    """
    send_val = {}
    for _ in range(6):
        send_res = execute_cdp_command(ws_url, "Runtime.evaluate", {"expression": js_send, "returnByValue": True})
        send_val = send_res.get("result", {}).get("result", {}).get("value", {}) or {}
        if send_val.get("ok"):
            break
        time.sleep(0.5)
    if not send_val.get("ok"):
        execute_cdp_command(ws_url, "Input.dispatchKeyEvent", {"type": "rawKeyDown", "windowsVirtualKeyCode": 13, "unmodifiedText": "\r", "text": "\r"})
        execute_cdp_command(ws_url, "Input.dispatchKeyEvent", {"type": "keyUp", "windowsVirtualKeyCode": 13})

    print(f"[CHATGPT_WEBTOOL] Đã gửi prompt đầy đủ lên {acc_id} (Cổng {active_port}), đang chờ ChatGPT tạo ảnh hoàn thiện...", flush=True)

    # 6. Wait for COMPLETED image generation (never save progressive blurred preview early)
    start_time = time.time()
    last_img_url = None
    last_img_dims = (0, 0)
    stable_hits = 0
    finished_text_since = None
    retried_submit = False
    limit_phrases = [
        "reached the daily limit",
        "reached your daily limit",
        "limit for creating images",
        "image creation limit",
        "you've hit the free plan limit",
        "free plan limit for",
        "too many requests",
        "rate limit",
        "try again later",
        "resets after",
        "đạt giới hạn",
        "giới hạn tạo ảnh",
        "hết lượt",
        "thử lại sau",
        "nâng cấp lên plus",
        "upgrade to plus",
    ]
    refusal_phrases = [
        "cannot generate",
        "can't generate",
        "unable to generate",
        "violates our content policy",
        "content policy",
        "không thể tạo hình",
        "vi phạm chính sách",
    ]
    creating_hints = ("creating image", "generating image", "getting started", "đang tạo hình", "đang tạo ảnh")

    js_poll = f"""
    (() => {{
        const turns = Array.from(document.querySelectorAll('[data-message-author-role="assistant"], article[data-testid^="conversation-turn-"]'));
        const newTurns = turns.slice({pre_msg_count});
        const newTurnImgs = newTurns.flatMap(t => Array.from(t.querySelectorAll('img')));
        const allImgs = Array.from(document.querySelectorAll('img'));
        const candidates = [];
        for (const img of [...newTurnImgs, ...allImgs]) {{
            if (candidates.includes(img)) continue;
            const src = img.src || '';
            const alt = (img.alt || '').toLowerCase();
            if (src.includes('avatar') || src.includes('gravatar') || src.includes('favicon')) continue;
            const isGenSrc = src.includes('oaiusercontent.com') || src.includes('/backend-api/estuary') ||
                             src.includes('dalle') || alt.includes('generated') || src.startsWith('blob:') ||
                             newTurnImgs.includes(img);
            if (isGenSrc && img.naturalWidth >= 256 && img.naturalHeight >= 256) {{
                candidates.push(img);
            }}
        }}
        const latestImg = candidates.length > 0 ? candidates[candidates.length - 1] : null;
        const stopBtn = document.querySelector('button[data-testid="stop-button"], button[aria-label*="Stop"], button[aria-label*="Dừng"]');
        const isStreaming = !!stopBtn || !!document.querySelector('.result-streaming');
        const userTurnsCount = document.querySelectorAll('[data-message-author-role="user"]').length;
        const compEl = document.querySelector('div.ProseMirror[contenteditable="true"]') || document.querySelector('#prompt-textarea:not(#pending-home-input)');
        const composerLen = compEl ? ((compEl.innerText || compEl.textContent || compEl.value || '').trim().length) : 0;
        const latestTurnText = newTurns.length > 0 ? (newTurns[newTurns.length - 1].innerText || '') : '';
        const banners = Array.from(document.querySelectorAll('[role="alert"], .text-token-text-error, [data-testid*="limit"]'))
            .map(el => el.innerText || '').join(' ');
        const combinedText = (latestTurnText + ' ' + banners).toLowerCase();
        return {{
            found: !!latestImg,
            complete: !!(latestImg && latestImg.complete),
            src: latestImg ? latestImg.src : '',
            width: latestImg ? latestImg.naturalWidth : 0,
            height: latestImg ? latestImg.naturalHeight : 0,
            isStreaming: isStreaming,
            hasNewTurn: newTurns.length > 0 || userTurnsCount > 0,
            composerLen: composerLen,
            combinedText: combinedText.slice(0, 700),
            pageTextTail: (document.body.innerText || '').slice(-900).toLowerCase()
        }};
    }})()
    """

    while time.time() - start_time < timeout_seconds:
        time.sleep(3.0)
        poll_res = execute_cdp_command(ws_url, "Runtime.evaluate", {"expression": js_poll, "returnByValue": True})
        val = poll_res.get("result", {}).get("result", {}).get("value", {}) or {}
        elapsed = time.time() - start_time

        # Fail-fast if prompt remained stuck unsent in composer (re-try Submit once at 12s, abort by 27s)
        if not val.get("hasNewTurn") and not val.get("isStreaming") and not val.get("found"):
            if elapsed >= 12.0 and not retried_submit:
                retried_submit = True
                if int(val.get("composerLen") or 0) < 20:
                    execute_cdp_command(ws_url, "Runtime.evaluate", {"expression": js_focus_clear, "returnByValue": True})
                    time.sleep(0.25)
                    execute_cdp_command(ws_url, "Input.insertText", {"text": clean_prompt})
                    time.sleep(0.7)
                execute_cdp_command(ws_url, "Runtime.evaluate", {"expression": js_send, "returnByValue": True})
                execute_cdp_command(ws_url, "Input.dispatchKeyEvent", {"type": "rawKeyDown", "windowsVirtualKeyCode": 13, "unmodifiedText": "\r", "text": "\r"})
                execute_cdp_command(ws_url, "Input.dispatchKeyEvent", {"type": "keyUp", "windowsVirtualKeyCode": 13})
                continue
            elif elapsed >= 27.0:
                return {"ok": False, "error": "CHATGPT_SUBMIT_FAILED", "detail": "Prompt did not submit in ChatGPT composer"}
        err_text = str(val.get("combinedText") or "") + " " + str(val.get("pageTextTail") or "")
        if any(phrase in err_text for phrase in limit_phrases):
            print(f"[CHATGPT_WEBTOOL] ⚠️ Phát hiện giới hạn lượt tạo ảnh trên {acc_id}: {err_text[:140]}", flush=True)
            return {
                "ok": False,
                "error": "CHATGPT_IMAGE_LIMIT",
                "limit_detected": True,
                "detail": err_text[:200],
            }

        is_streaming = bool(val.get("isStreaming"))
        candidate = str(val.get("src") or "")
        w = int(val.get("width") or 0)
        h = int(val.get("height") or 0)

        if val.get("found") and val.get("complete") and candidate and (candidate not in pre_images or len(pre_images) == 0):
            if not is_streaming:
                if last_img_url == candidate and last_img_dims == (w, h):
                    stable_hits += 1
                else:
                    last_img_url = candidate
                    last_img_dims = (w, h)
                    stable_hits = 1
                if stable_hits >= 1:
                    # Wait briefly once so any final post-stream download hook renders cleanly
                    time.sleep(1.5)
                    print(f"[CHATGPT_WEBTOOL] Phát hiện ảnh hoàn thiện từ ChatGPT: {w}x{h}", flush=True)
                    break
            else:
                last_img_url = candidate
                last_img_dims = (w, h)
            continue

        if val.get("hasNewTurn") and not is_streaming and not val.get("found"):
            turn_txt = str(val.get("combinedText") or "")
            if any(rp in turn_txt for rp in refusal_phrases):
                return {"ok": False, "error": "CHATGPT_CONTENT_REFUSAL", "detail": turn_txt[:220]}
            if not any(ch in turn_txt for ch in creating_hints) and len(turn_txt.strip()) > 30:
                if finished_text_since is None:
                    finished_text_since = time.time()
                elif time.time() - finished_text_since > 20.0:
                    return {"ok": False, "error": "CHATGPT_TEXT_ONLY_RESPONSE", "detail": turn_txt[:220]}
        else:
            finished_text_since = None

    if not last_img_url:
        return {"ok": False, "error": "IMAGE_GENERATION_TIMEOUT"}

    # 7. Download & validate image bytes
    img_bytes = _extract_image_bytes(ws_url, last_img_url)
    if not img_bytes:
        return {"ok": False, "error": "DOWNLOAD_FAILED: Unable to extract generated image from ChatGPT tab"}

    out_file.write_bytes(img_bytes)
    dims = _validate_image_bytes(img_bytes) or last_img_dims
    print(f"[CHATGPT_WEBTOOL] Đã tải ảnh hoàn thiện về {out_file} ({len(img_bytes)} bytes, {dims[0]}x{dims[1]})", flush=True)

    # 8. Delete the temporary ChatGPT conversation thread now that the image is safely saved on disk
    deleted_conv_id = _cleanup_generated_conversation(ws_url, pre_conv_id=pre_conv_id)

    return {
        "ok": True,
        "output_file": str(out_file),
        "backend": "chatgpt_web",
        "account_id": acc_id,
        "width": dims[0],
        "height": dims[1],
        "deleted_conversation_id": deleted_conv_id,
    }


def _acquire_chatgpt_global_lock(lock_file: Path, wait_timeout: float = 220.0) -> bool:
    """Serializes ChatGPT Web tab automation across threads and subprocesses."""
    import os
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + max(5.0, float(wait_timeout))
    while True:
        try:
            fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            try:
                os.write(fd, f"{os.getpid()} {time.time()}\n".encode("ascii", "ignore"))
            finally:
                os.close(fd)
            return True
        except FileExistsError:
            try:
                if time.time() - lock_file.stat().st_mtime > 240.0:
                    lock_file.unlink(missing_ok=True)
                    continue
            except Exception:
                pass
            if time.time() >= deadline:
                return False
            time.sleep(0.5)
        except Exception:
            return True


def _release_chatgpt_global_lock(lock_file: Path) -> None:
    try:
        lock_file.unlink(missing_ok=True)
    except Exception:
        pass


def generate_thumbnail_via_chatgpt_web(
    prompt: str,
    output_path: Path | str,
    timeout_seconds: int = 180,
) -> Dict[str, Any]:
    """Automates sending prompt to ChatGPT Web with automatic multi-account rotation on quota limits.
    Automatically starts Chrome on-demand and closes Chrome when done to keep desktop clean.
    Serialized by a global file lock so concurrent requests never hijack the same ChatGPT tab.
    """
    out_file = Path(output_path).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)
    lock_file = Path(__file__).resolve().parent.parent.parent / "profiles" / ".chatgpt_web.lock"
    acquired = _acquire_chatgpt_global_lock(lock_file, wait_timeout=float(timeout_seconds) + 60.0)
    if not acquired:
        return {"ok": False, "error": "CHATGPT_BUSY_TIMEOUT", "message": "ChatGPT Web đang xử lý ảnh khác, vui lòng thử lại sau."}

    try:
        import chatgpt_browser
        max_attempts = max(1, len(chatgpt_browser.list_accounts()))
        last_res: Dict[str, Any] = {"ok": False, "error": "UNKNOWN"}

        for attempt in range(max_attempts):
            last_res = _generate_once(prompt, out_file, timeout_seconds=timeout_seconds)
            if last_res.get("ok"):
                return last_res

            err_code = str(last_res.get("error") or "")
            rotatable = (
                "CHATGPT_IMAGE_LIMIT",
                "CHATGPT_NOT_LOGGED_IN",
                "CHATGPT_COMPOSER_NOT_READY",
                "CHATGPT_SUBMIT_FAILED",
                "IMAGE_GENERATION_TIMEOUT",
            )
            if (err_code in rotatable or err_code.startswith("DOWNLOAD_FAILED")) and attempt + 1 < max_attempts:
                cooldown = 21600 if err_code == "CHATGPT_IMAGE_LIMIT" else 300
                next_acc = chatgpt_browser.rotate_chatgpt_account(reason=err_code, cooldown_seconds=cooldown)
                if next_acc:
                    print(
                        f"[CHATGPT_WEBTOOL] 🔄 Chuyển sang {next_acc.get('label')} (Cổng {next_acc.get('port')}) và thử lại...",
                        flush=True,
                    )
                    continue
            return last_res

        return last_res
    finally:
        try:
            import chatgpt_browser
            chatgpt_browser.close_chatgpt_browser()
        except Exception:
            pass
        _release_chatgpt_global_lock(lock_file)
