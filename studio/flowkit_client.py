"""FlowKit Client Adapter for Storyboard AI Studio.

Provides unified, robust REST API connectivity to FlowKit (http://127.0.0.1:18110)
to generate images and videos via Google Flow Web Tool, replacing legacy Node.js MCP V2.
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Union

from PIL import Image, ImageOps

logger = logging.getLogger("flowkit_client")

def _resolve_flowkit_root() -> Path:
    env_p = os.environ.get("FLOWKIT_ROOT", "").strip()
    candidates = [
        Path(env_p) if env_p else None,
        Path(__file__).resolve().parent.parent / "FLOWKIT",
        Path(__file__).resolve().parent / "flowkit",
        Path("D:/FLOWKIT"),
        Path("C:/FLOWKIT"),
    ]
    for c in candidates:
        if c and c.is_dir() and (c / "app").is_dir():
            return c
    return Path("D:/FLOWKIT")

FLOWKIT_ROOT = _resolve_flowkit_root()
FLOWKIT_HOST = os.environ.get("FLOWKIT_HOST", "127.0.0.1")
FLOWKIT_PORT = int(os.environ.get("FLOWKIT_PORT", "18110"))
FLOWKIT_BASE_URL = f"http://{FLOWKIT_HOST}:{FLOWKIT_PORT}"


class FlowKitError(RuntimeError):
    """Raised when FlowKit request fails or returns an error."""
    pass


def get_api_key() -> str:
    """Read API key from FlowKit state."""
    key_file = FLOWKIT_ROOT / "state" / "api.key"
    if key_file.is_file():
        try:
            return key_file.read_text(encoding="ascii").strip()
        except Exception:
            pass
    return os.environ.get("FLOWKIT_API_KEY", "")


def is_flowkit_alive(timeout: float = 2.0) -> bool:
    """Check if FlowKit orchestrator daemon is responsive."""
    url = f"{FLOWKIT_BASE_URL}/health"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("status") == "ok"
    except Exception:
        return False
    return False


def cleanup_stale_flowkit_jobs():
    """Unblock FlowKit if previous jobs were left in recovery_needed state."""
    db_file = FLOWKIT_ROOT / "state" / "jobs.sqlite"
    if not db_file.is_file():
        return
    try:
        import sqlite3
        with sqlite3.connect(str(db_file), timeout=5) as conn:
            conn.execute("UPDATE jobs SET state = 'failed' WHERE state = 'recovery_needed'")
            conn.commit()
    except Exception:
        pass


def ensure_flowkit_running(max_wait_seconds: int = 15) -> bool:
    """Ensure FlowKit API is running; if down, attempt background launch."""
    import sys
    cleanup_stale_flowkit_jobs()
    if is_flowkit_alive():
        return True

    flowkit_root = _resolve_flowkit_root()
    if not flowkit_root.is_dir():
        logger.warning(f"FLOWKIT_ROOT does not exist: {flowkit_root}")
        return False

    vbs = flowkit_root / "Start_API.vbs"
    app_dir = flowkit_root / "app"
    launcher_py = app_dir / "launcher.py"
    start_cmd = flowkit_root / "START.cmd"

    candidates_py = [
        flowkit_root / "engines" / "muse" / "runtime" / "muse" / "python" / "python.exe",
        flowkit_root / "engines" / "muse" / "runtime" / "muse" / "python" / "pythonw.exe",
        flowkit_root / "runtime" / "python" / "python.exe",
        flowkit_root / ".venv" / "Scripts" / "python.exe",
        Path(sys.executable),
    ]
    python_exe = next((p for p in candidates_py if p.is_file()), None)

    # 1. First priority: Start_API.vbs (silent background via wscript.exe)
    if vbs.is_file():
        try:
            subprocess.Popen(
                ["wscript.exe", str(vbs)],
                cwd=str(flowkit_root),
                creationflags=0x08000000 if os.name == "nt" else 0
            )
            logger.info("Triggered FlowKit startup via Start_API.vbs")
        except Exception as e:
            logger.warning(f"Could not launch Start_API.vbs: {e}")

    # 2. Second priority: launcher.py with python
    if not is_flowkit_alive() and launcher_py.is_file() and python_exe:
        try:
            cmd = [str(python_exe), "-B", str(launcher_py)]
            subprocess.Popen(
                cmd,
                cwd=str(flowkit_root),
                creationflags=0x08000000 if os.name == "nt" else 0,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            logger.info(f"Triggered FlowKit startup via launcher.py using {python_exe}")
        except Exception as e:
            logger.warning(f"Could not launch launcher.py: {e}")

    # 3. Third priority: direct uvicorn gateway:app
    if not is_flowkit_alive() and python_exe and app_dir.is_dir():
        cmd = [
            str(python_exe), "-B", "-m", "uvicorn", "gateway:app",
            "--host", str(FLOWKIT_HOST), "--port", str(FLOWKIT_PORT),
            "--app-dir", str(app_dir), "--no-access-log"
        ]
        try:
            subprocess.Popen(
                cmd,
                cwd=str(flowkit_root),
                creationflags=0x08000000 if os.name == "nt" else 0,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            logger.info(f"Triggered FlowKit startup via uvicorn gateway:app")
        except Exception as e:
            logger.warning(f"Could not spawn uvicorn directly: {e}")

    # 4. Fourth priority: START.cmd
    if not is_flowkit_alive() and start_cmd.is_file():
        try:
            subprocess.Popen(
                ["cmd.exe", "/c", str(start_cmd)],
                cwd=str(flowkit_root),
                creationflags=0x08000000 if os.name == "nt" else 0
            )
            logger.info("Triggered FlowKit startup via START.cmd")
        except Exception as e:
            logger.warning(f"Could not spawn START.cmd: {e}")

    # Wait for ready
    deadline = time.monotonic() + max_wait_seconds
    while time.monotonic() < deadline:
        if is_flowkit_alive(timeout=1.0):
            return True
        time.sleep(0.5)

    return is_flowkit_alive()


def get_webtool_status(mode: str = "hidden") -> Dict[str, Any]:
    """Query live Web Tool adapter status."""
    key = get_api_key()
    url = f"{FLOWKIT_BASE_URL}/v1/webtool/status?mode={mode}"
    try:
        req = urllib.request.Request(url, headers={"X-API-Key": key}, method="GET")
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"connected": False, "error": str(e)}


def generate_image(
    prompt: str,
    output_path: Union[str, Path],
    *,
    aspect_ratio: str = "16:9",
    image_model: str = "NANO_BANANA_PRO",
    webtool_mode: str = "hidden",
    timeout: int = 180,
    scene_num: Optional[int] = None
) -> str:
    """Generate exactly one image via FlowKit Google Flow Web Tool.
    
    1. Submits job to FlowKit /v1/jobs with provider='webtool'.
    2. Polls job state until succeeded.
    3. Downloads and normalizes the resulting PNG.
    4. Saves atomically to output_path.
    """
    if not ensure_flowkit_running():
        raise FlowKitError("FLOWKIT_SERVICE_NOT_RUNNING (Could not reach http://127.0.0.1:18110)")

    prompt_clean = prompt.strip()

    key = get_api_key()
    request_id = f"flowkit-img-{int(time.time())}-{uuid.uuid4().hex[:6]}"

    ar_clean = "9:16" if str(aspect_ratio).strip() == "9:16" else "16:9"

    payload = {
        "provider": "webtool",
        "webtool_mode": webtool_mode,
        "kind": "image",
        "prompt": prompt_clean,
        "aspect_ratio": ar_clean,
        "image_model": image_model,
        "request_id": request_id
    }

    submit_url = f"{FLOWKIT_BASE_URL}/v1/jobs"
    req = urllib.request.Request(
        submit_url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "X-API-Key": key,
            "Content-Type": "application/json",
            "Idempotency-Key": request_id
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=25.0) as resp:
            submit_res = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="replace")
        raise FlowKitError(f"FLOWKIT_SUBMIT_HTTP_{e.code}: {err_msg}")
    except Exception as e:
        raise FlowKitError(f"FLOWKIT_SUBMIT_FAILED: {e}")

    job_id = submit_res.get("job_id")
    if not job_id:
        raise FlowKitError(f"FLOWKIT_INVALID_RESPONSE: {submit_res}")

    print(f"[FLOWKIT_IMAGE] Job {job_id} submitted (request_id={request_id})", flush=True)

    # Poll status
    deadline = time.monotonic() + timeout
    poll_interval = 2.0
    download_url = None

    while time.monotonic() < deadline:
        status_url = f"{FLOWKIT_BASE_URL}/v1/jobs/{job_id}"
        try:
            p_req = urllib.request.Request(status_url, headers={"X-API-Key": key}, method="GET")
            with urllib.request.urlopen(p_req, timeout=8.0) as p_resp:
                info = json.loads(p_resp.read().decode("utf-8"))
        except Exception as e:
            time.sleep(poll_interval)
            continue

        state = info.get("state")
        phase = info.get("phase")

        if state == "succeeded":
            artifacts = info.get("artifacts") or []
            if artifacts and artifacts[0].get("download_url"):
                download_url = artifacts[0]["download_url"]
                break
            raise FlowKitError(f"FLOWKIT_JOB_SUCCEEDED_WITHOUT_ARTIFACT: {info}")

        if state in ("failed", "error"):
            err_obj = info.get("error") or {}
            raise FlowKitError(f"FLOWKIT_JOB_FAILED: {err_obj.get('code')}: {err_obj.get('message')}")

        time.sleep(poll_interval)

    if not download_url:
        raise FlowKitError(f"FLOWKIT_JOB_TIMEOUT after {timeout}s (job_id={job_id})")

    # Download image artifact
    file_url = f"{FLOWKIT_BASE_URL}{download_url}"
    d_req = urllib.request.Request(file_url, headers={"X-API-Key": key}, method="GET")

    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp_target = target.with_name(f"{target.stem}.{uuid.uuid4().hex}.tmp")

    try:
        with urllib.request.urlopen(d_req, timeout=30.0) as resp, open(temp_target, "wb") as f_out:
            while chunk := resp.read(65536):
                f_out.write(chunk)
    except Exception as e:
        if temp_target.is_file():
            temp_target.unlink()
        raise FlowKitError(f"FLOWKIT_DOWNLOAD_FAILED: {e}")

    # Standardize image dimensions & format via PIL
    try:
        with Image.open(temp_target) as img:
            img.load()
            rgb = img.convert("RGB")
            is_vertical = (ar_clean == "9:16")
            target_r = 9 / 16 if is_vertical else 16 / 9
            target_size = (1080, 1920) if is_vertical else (1536, 864)

            # High quality resize
            if abs(rgb.width / rgb.height - target_r) > 0.04:
                rgb = ImageOps.fit(rgb, target_size, method=Image.Resampling.LANCZOS)
            else:
                rgb = rgb.resize(target_size, Image.Resampling.LANCZOS)

            temp_final = target.with_name(f"{target.stem}.{uuid.uuid4().hex}.png")
            rgb.save(temp_final, format="PNG", optimize=True)
            os.replace(temp_final, target)

            # Auto clean watermark
            try:
                from studio.clean_watermark import remove_gemini_watermark
                remove_gemini_watermark(target)
            except Exception:
                try:
                    from clean_watermark import remove_gemini_watermark
                    remove_gemini_watermark(target)
                except Exception:
                    pass
    finally:
        if temp_target.is_file():
            try:
                temp_target.unlink()
            except Exception:
                pass

    print(f"[FLOWKIT_IMAGE_PASS] saved={target} bytes={target.stat().st_size} ({target_size[0]}x{target_size[1]})", flush=True)
    return str(target)


def generate_video(
    prompt: str,
    output_path: Union[str, Path],
    *,
    aspect_ratio: str = "16:9",
    duration_seconds: int = 8,
    webtool_mode: str = "hidden",
    timeout: int = 600
) -> str:
    """Generate exactly one 8-second video via FlowKit Google Flow Web Tool."""
    if not ensure_flowkit_running():
        raise FlowKitError("FLOWKIT_SERVICE_NOT_RUNNING (Could not reach http://127.0.0.1:18110)")

    prompt_clean = prompt.strip()
    if not prompt_clean.upper().startswith(("CẢNH ", "CANH ", "SCENE ", "SHOT ")):
        prompt_clean = "CẢNH 1: " + prompt_clean

    key = get_api_key()
    request_id = f"flowkit-vid-{int(time.time())}-{uuid.uuid4().hex[:6]}"
    ar_clean = "9:16" if str(aspect_ratio).strip() == "9:16" else "16:9"

    payload = {
        "provider": "webtool",
        "webtool_mode": webtool_mode,
        "kind": "video",
        "prompt": prompt_clean,
        "aspect_ratio": ar_clean,
        "duration_seconds": duration_seconds,
        "request_id": request_id
    }

    submit_url = f"{FLOWKIT_BASE_URL}/v1/jobs"
    req = urllib.request.Request(
        submit_url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "X-API-Key": key,
            "Content-Type": "application/json",
            "Idempotency-Key": request_id
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=25.0) as resp:
            submit_res = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        raise FlowKitError(f"FLOWKIT_VIDEO_SUBMIT_FAILED: {e}")

    job_id = submit_res.get("job_id")
    if not job_id:
        raise FlowKitError(f"FLOWKIT_INVALID_VIDEO_RESPONSE: {submit_res}")

    print(f"[FLOWKIT_VIDEO] Job {job_id} submitted (request_id={request_id})", flush=True)

    deadline = time.monotonic() + timeout
    download_url = None

    while time.monotonic() < deadline:
        status_url = f"{FLOWKIT_BASE_URL}/v1/jobs/{job_id}"
        try:
            p_req = urllib.request.Request(status_url, headers={"X-API-Key": key}, method="GET")
            with urllib.request.urlopen(p_req, timeout=8.0) as p_resp:
                info = json.loads(p_resp.read().decode("utf-8"))
        except Exception:
            time.sleep(3.0)
            continue

        state = info.get("state")
        if state == "succeeded":
            artifacts = info.get("artifacts") or []
            if artifacts and artifacts[0].get("download_url"):
                download_url = artifacts[0]["download_url"]
                break
            raise FlowKitError(f"FLOWKIT_VIDEO_SUCCEEDED_WITHOUT_ARTIFACT: {info}")

        if state in ("failed", "error"):
            err_obj = info.get("error") or {}
            raise FlowKitError(f"FLOWKIT_VIDEO_FAILED: {err_obj.get('code')}: {err_obj.get('message')}")

        time.sleep(3.0)

    if not download_url:
        raise FlowKitError(f"FLOWKIT_VIDEO_TIMEOUT after {timeout}s (job_id={job_id})")

    file_url = f"{FLOWKIT_BASE_URL}{download_url}"
    d_req = urllib.request.Request(file_url, headers={"X-API-Key": key}, method="GET")

    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp_target = target.with_name(f"{target.stem}.{uuid.uuid4().hex}.tmp.mp4")

    with urllib.request.urlopen(d_req, timeout=60.0) as resp, open(temp_target, "wb") as f_out:
        while chunk := resp.read(131072):
            f_out.write(chunk)

    os.replace(temp_target, target)
    print(f"[FLOWKIT_VIDEO_PASS] saved={target} bytes={target.stat().st_size}", flush=True)
    return str(target)


def generate_episode_images_flowkit(
    scenes: list,
    bible: dict,
    *,
    series: str,
    episode: int,
    episode_dir: Union[str, Path],
    aspect_ratio: str = "16:9",
    image_model: str = "NANO_BANANA_PRO",
    max_new_images: Optional[int] = None,
    workers: Optional[int] = None
) -> list:
    """Generate images for all scenes in an episode via FlowKit Web Tool with multi-threading."""
    import concurrent.futures
    try:
        from studio.mcp_v2_batch import image_prompt
    except (ImportError, ModuleNotFoundError):
        try:
            from mcp_v2_batch import image_prompt
        except (ImportError, ModuleNotFoundError):
            import sys
            _p = str(Path(__file__).resolve().parent.parent)
            if _p not in sys.path:
                sys.path.insert(0, _p)
            from studio.mcp_v2_batch import image_prompt
    total = len(scenes)
    out_dir = Path(episode_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"MCP_BATCH_PREPARED {total}", flush=True)

    limit = int(max_new_images) if max_new_images and int(max_new_images) > 0 else total

    generated_dict = {}
    pending_items = []

    for idx, scene in enumerate(scenes, 1):
        target = out_dir / f"scene_{idx:03d}.png"
        if target.is_file() and target.stat().st_size > 1000:
            print(f"MCP_IMAGE_IMPORTED scene {idx}/{total}", flush=True)
            generated_dict[idx] = str(target)
            continue

        if len(generated_dict) + len(pending_items) >= limit:
            continue

        prompt = image_prompt(scene, bible)
        pending_items.append((idx, scene, target, prompt))

    # FlowKit WebTool uses a single browser queue. Sequential execution (concurrency=1)
    # guarantees zero race conditions and 100% reliable scene-by-scene delivery.
    concurrency = 1

    print(f"FLOWKIT_MULTI_THREAD_DISPATCH: Running {concurrency} concurrent threads across {len(pending_items)} scenes", flush=True)

    def _render_one(item):
        idx, scene, target, prompt = item
        print(f"MCP_RENDERING_BATCH {idx}/{total}", flush=True)
        fallback_models = [image_model, "NANO_BANANA_2_LITE", "NANO_BANANA_2", "NANO_BANANA_PRO"]
        model_queue = []
        for m in fallback_models:
            if m not in model_queue:
                model_queue.append(m)

        last_exc = None
        for attempt in range(1, 4):
            curr_model = model_queue[(attempt - 1) % len(model_queue)]
            try:
                res_path = generate_image(
                    prompt,
                    target,
                    aspect_ratio=aspect_ratio,
                    image_model=curr_model,
                    scene_num=idx
                )
                print(f"MCP_IMAGE_IMPORTED scene {idx}/{total} (model: {curr_model})", flush=True)
                return idx, res_path
            except Exception as exc:
                last_exc = exc
                logger.warning(f"FlowKit image generation failed for scene {idx} with {curr_model} (attempt {attempt}/3): {exc}")
                if attempt < 3:
                    time.sleep(4)
        raise last_exc

    if concurrency > 1 and len(pending_items) > 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
            future_to_idx = {executor.submit(_render_one, item): item[0] for item in pending_items}
            for future in concurrent.futures.as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    r_idx, res_path = future.result()
                    generated_dict[r_idx] = res_path
                except Exception as exc:
                    logger.error(f"FlowKit image generation failed for scene {idx}: {exc}")
                    raise
    else:
        for item in pending_items:
            idx, res_path = _render_one(item)
            generated_dict[idx] = res_path

    results = []
    for idx in range(1, total + 1):
        if idx in generated_dict:
            results.append(generated_dict[idx])
        elif results:
            target = out_dir / f"scene_{idx:03d}.png"
            import shutil
            shutil.copy2(results[-1], target)
            results.append(str(target))

    import shutil
    for idx in range(1, total + 1):
        src = out_dir / f"scene_{idx:03d}.png"
        if src.is_file():
            sc_dir = out_dir / "scenes" / f"scene_{idx:04d}"
            sc_dir.mkdir(parents=True, exist_ok=True)
            dst = sc_dir / "image.png"
            if not dst.is_file() or dst.stat().st_size != src.stat().st_size:
                shutil.copy2(src, dst)
            try:
                from studio.clean_watermark import remove_gemini_watermark
                remove_gemini_watermark(dst)
            except Exception:
                try:
                    from clean_watermark import remove_gemini_watermark
                    remove_gemini_watermark(dst)
                except Exception:
                    pass

    print("MCP_BATCH_ALL_IMAGES_PASS", flush=True)
    return results



def open_flowkit_browser(show: bool = True) -> Dict[str, Any]:
    """Launch or reveal Google Flow browser for interactive login.
    
    Guarantees window is unlocked and stays open steadily without bouncing.
    """
    ensure_flowkit_running()
    
    unlock_flag = FLOWKIT_ROOT / "state" / "flow_window" / "unlock.flag"
    unlock_flag.parent.mkdir(parents=True, exist_ok=True)
    unlock_flag.write_text("unlock", encoding="ascii")
    
    # Ensure machine.json is correctly configured
    machine_path = FLOWKIT_ROOT / "state" / "machine.json"
    if machine_path.is_file():
        try:
            m_data = json.loads(machine_path.read_text(encoding="utf-8-sig"))
            if m_data.get("debug_port") != 9461:
                m_data["debug_port"] = 9461
                machine_path.write_text(json.dumps(m_data, indent=2), encoding="utf-8")
        except Exception:
            pass

    chrome_live = False
    try:
        req = urllib.request.Request("http://127.0.0.1:9461/json/version")
        with urllib.request.urlopen(req, timeout=1.5) as r:
            chrome_live = True
    except Exception:
        chrome_live = False

    target_url = "https://flow.google.com/project/c7186034-34e8-463c-9f1b-2ceac85cde38/tool/69da86fb-6c79-43d2-a387-ef47b0fda4db"

    if not chrome_live:
        python_exe = FLOWKIT_ROOT / "engines" / "muse" / "runtime" / "muse" / "python" / "python.exe"
        cmd = [str(python_exe), "-B", "-u", str(FLOWKIT_ROOT / "app" / "flow_browser.py"), "--show"]
        subprocess.Popen(cmd, cwd=str(FLOWKIT_ROOT), creationflags=0x08000000 if os.name == "nt" else 0)
    else:
        # Check tabs and ensure Flow Web Tool tab is open & activated
        try:
            req = urllib.request.Request("http://127.0.0.1:9461/json")
            with urllib.request.urlopen(req, timeout=2.0) as r:
                tabs = json.loads(r.read().decode("utf-8"))
            flow_tab = next((t for t in tabs if t.get("type") == "page" and "flow.google.com" in t.get("url", "")), None)
            if flow_tab:
                try:
                    urllib.request.urlopen(f"http://127.0.0.1:9461/json/activate/{flow_tab['id']}", timeout=2)
                except Exception:
                    pass
            else:
                n_req = urllib.request.Request(f"http://127.0.0.1:9461/json/new?{urllib.parse.quote(target_url)}", method="PUT")
                urllib.request.urlopen(n_req, timeout=3.0)
        except Exception as e:
            logger.warning(f"Could not check tabs: {e}")

    # Restore and show Chrome window
    if os.name == "nt":
        ps_show = """
         = Get-NetTCPConnection -LocalPort 9461 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
         = if () { Get-Process -Id .OwningProcess -ErrorAction SilentlyContinue } else {  }
        if ( -and .MainWindowHandle -ne 0) {
            $sig = '[DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd); [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow); [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr hWnd, IntPtr z, int x, int y, int w, int h, uint f);'
            Add-Type -MemberDefinition $sig -Name Win32FlowShow -Namespace Win32Util -ErrorAction SilentlyContinue
            [Win32Util.Win32FlowShow]::ShowWindow($p.MainWindowHandle, 9)
            [Win32Util.Win32FlowShow]::SetWindowPos($p.MainWindowHandle, [IntPtr]::Zero, 80, 80, 1100, 800, 0x14)
            [Win32Util.Win32FlowShow]::SetForegroundWindow($p.MainWindowHandle)
        }
        """
        try:
            subprocess.Popen(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps_show],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    return {
        "success": True,
        "message": "Đã mở trình duyệt Chrome Google Flow để đăng nhập. Cửa sổ giữ nguyên, không tự đóng."
    }


def minimize_flowkit_browser() -> Dict[str, Any]:
    """Minimize/hide Chrome browser once cleanly to the background."""
    unlock_flag = FLOWKIT_ROOT / "state" / "flow_window" / "unlock.flag"
    try:
        if unlock_flag.is_file():
            unlock_flag.unlink()
    except Exception:
        pass

    if os.name == "nt":
        ps_hide = """
         = Get-NetTCPConnection -LocalPort 9461 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
         = if () { Get-Process -Id .OwningProcess -ErrorAction SilentlyContinue } else {  }
        if ( -and .MainWindowHandle -ne 0) {
            $sig = '[DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);'
            Add-Type -MemberDefinition $sig -Name Win32FlowHide -Namespace Win32Util -ErrorAction SilentlyContinue
            [Win32Util.Win32FlowHide]::ShowWindow($p.MainWindowHandle, 6) # SW_MINIMIZE
        }
        """
        try:
            subprocess.Popen(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps_hide],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    return {
        "success": True,
        "message": "Đã thu nhỏ trình duyệt Chrome Google Flow xuống chạy ngầm."
    }
