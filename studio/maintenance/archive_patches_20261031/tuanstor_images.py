"""Optional provider for storyboard images.

No assumptions about TuanStor's host: the endpoint must be explicitly configured.
This adapter speaks a commonly used OpenAI Images-style JSON contract ONLY.
It deliberately refuses to send requests if the provider's protocol isn't configured.
"""
from __future__ import annotations
import base64
import io
import ipaddress
import os
import time
import uuid
from pathlib import Path
from urllib.parse import urlparse

import requests
from PIL import Image, ImageOps

ROOT=Path(__file__).resolve().parent
MAX_IMAGE_BYTES=16 * 1024 * 1024

class ImageProviderError(RuntimeError):
    pass

def get_setting(name: str) -> str:
    path=ROOT / ".env"
    if not path.is_file():
        return ""
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line=line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val=line.split("=", 1)
        if key.strip()==name:
            return val.strip().strip('"').strip("'")
    return ""

def configure(updates: dict[str,str]):
    """Preserve Gemini credentials while changing only selected provider settings."""
    allowed={"TUANSTOR_IMAGE_ENDPOINT","TUANSTOR_IMAGE_MODEL",
             "TUANSTOR_API_KEY","TUANSTOR_IMAGE_SIZE","TUANSTOR_AUTH_HEADER"}
    if not updates or not set(updates).issubset(allowed):
        raise ValueError("Only isolated image provider settings may be changed")
    path=ROOT/".env"
    current=path.read_text(encoding="utf-8-sig") if path.exists() else ""
    lines=[]
    done=set()
    for line in current.splitlines():
        key=line.split("=",1)[0].strip()
        if key in updates:
            if key in done:
                continue
            lines.append(key+"="+updates[key])
            done.add(key)
        else:
            lines.append(line)
    for key,val in updates.items():
        if key not in done:
            lines.append(key+"="+val)
    for value in updates.values():
        if "\n" in value or "\r" in value:
            raise ValueError("Invalid setting value")
    temp=path.with_name(".env.tmp."+uuid.uuid4().hex)
    temp.write_text("\n".join(lines).rstrip()+"\n",encoding="utf-8")
    os.replace(temp,path)

def is_safe_https(url: str) -> bool:
    parsed=urlparse(url)
    if parsed.scheme!="https" or not parsed.hostname or parsed.username or parsed.password:
        return False
    if parsed.port not in (None,443):
        return False
    host=parsed.hostname.lower().rstrip(".")
    if host in ("localhost",) or host.endswith(".local"):
        return False
    try:
        ip=ipaddress.ip_address(host)
        return ip.is_global
    except ValueError:
        return "." in host

def _decode_image(payload: dict, session, timeout: int) -> bytes:
    data=payload.get("data")
    item=data[0] if isinstance(data,list) and data else None
    if item is None:
        item=payload
    if not isinstance(item,dict):
        raise ImageProviderError("No image payload in API response")
    b64=item.get("b64_json") or item.get("image_base64") or payload.get("b64_json")
    if b64:
        if not isinstance(b64,str):
            raise ImageProviderError("Invalid base64 image field")
        if b64.startswith("data:"):
            b64=b64.split(",",1)[-1]
        if len(b64)>MAX_IMAGE_BYTES*2:
            raise ImageProviderError("Image response exceeds size limit")
        try:
            raw=base64.b64decode(b64,validate=True)
        except Exception as e:
            raise ImageProviderError("Invalid base64 image data") from e
        if len(raw)>MAX_IMAGE_BYTES:
            raise ImageProviderError("Decoded image exceeds size limit")
        return raw
    url=item.get("url") or payload.get("url") or payload.get("result_url")
    if not isinstance(url,str) or not is_safe_https(url):
        raise ImageProviderError("No supported b64_json or secure HTTPS image URL in provider response")
    try:
        resp=session.get(url,timeout=timeout,stream=True,allow_redirects=False)
        resp.raise_for_status()
        if 300<=resp.status_code<400:
            raise ImageProviderError("Image redirects are blocked")
        chunks=[]
        count=0
        for chunk in resp.iter_content(64*1024):
            count+=len(chunk)
            if count>MAX_IMAGE_BYTES:
                raise ImageProviderError("Remote image exceeds size limit")
            chunks.append(chunk)
        return b"".join(chunks)
    except requests.RequestException as e:
        raise ImageProviderError("Failed downloading image from provider") from e

def generate_image(prompt: str, output_path: str | Path, reference_path: str | None = None,
                   session=None, timeout: int=150) -> Path:
    """Send a single JSON request. No automatic paid retry or silent provider switch."""
    endpoint=get_setting("TUANSTOR_IMAGE_ENDPOINT")
    model=get_setting("TUANSTOR_IMAGE_MODEL")
    key=get_setting("TUANSTOR_API_KEY")
    size=get_setting("TUANSTOR_IMAGE_SIZE")
    auth=get_setting("TUANSTOR_AUTH_HEADER") or "Authorization"
    if not endpoint or not model or not key:
        raise ImageProviderError("Tuấn Stor is not configured: provide its exact image endpoint, model ID and private API key")
    if not is_safe_https(endpoint):
        raise ImageProviderError("Tuấn Stor endpoint must be a public HTTPS URL (no localhost/private IP)")
    if auth not in ("Authorization","x-api-key","X-API-Key"):
        raise ImageProviderError("Only Authorization/Bearer or X-API-Key auth is supported")
    headers={"Content-Type":"application/json"}
    headers[auth] = "Bearer "+key if auth=="Authorization" else key
    full_prompt=prompt
    if reference_path and Path(reference_path).is_file():
        # The current JSON contract has no safe reference-image field.
        # A separate image-edit adapter is required for true image-to-image.
        full_prompt += ("\nStay consistent with the previously established character "
                        "costumes, art style, line weight and color palette. "
                        "Generate a new, distinct scene. Do not draw hands or pens.")
    body={"model":model,"prompt":full_prompt,"n":1}
    if size:
        body["size"]=size
    http=session or requests.Session()
    try:
        response=http.post(endpoint,json=body,headers=headers,timeout=timeout,allow_redirects=False)
    except requests.RequestException as e:
        raise ImageProviderError("Tuấn Stor image connection failed (network or timeout)") from e
    if response.status_code not in (200,201):
        # Do not echo upstream response (might contain credentials or submitted prompts).
        raise ImageProviderError(f"Tuấn Stor image API returned HTTP {response.status_code}; check endpoint, model, credits and supported protocol")
    try:
        result=response.json()
    except ValueError as e:
        raise ImageProviderError("Tuấn Stor response is not JSON (verify API protocol)") from e
    raw=_decode_image(result,http,timeout)
    try:
        with Image.open(io.BytesIO(raw)) as original:
            original.load()
            rgb=original.convert("RGB")
            if rgb.width<256 or rgb.height<256:
                raise ImageProviderError("Generated image resolution is too small")
            # Preserve the original artwork and avoid stretching faces/characters.
            ratio=16/9
            if abs(rgb.width/rgb.height-ratio)>0.02:
                canvas=ImageOps.pad(rgb,(1536,864),method=Image.Resampling.LANCZOS,color="white")
            else:
                canvas=rgb
            target=Path(output_path)
            target.parent.mkdir(parents=True,exist_ok=True)
            tmp=target.with_name(target.stem+"."+uuid.uuid4().hex+".png")
            canvas.save(tmp,format="PNG")
            os.replace(tmp,target)
            return target
    except ImageProviderError:
        raise
    except Exception as e:
        raise ImageProviderError("API did not return a usable image") from e
