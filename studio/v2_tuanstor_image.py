"""Storyboard image generation using the user's V2 Tuấn Stor gateway.

READ-ONLY access to V2/.env. No key copied or printed.
Only the independently configured Storyboard Studio files may be modified.
Uses the image-generation endpoint confirmed by a real successful test.
"""
from __future__ import annotations

import base64
import io
import os
import uuid
from pathlib import Path
from urllib.parse import urlsplit

import requests
from PIL import Image, ImageOps

V2_ENV=Path(r"D:\YOUTUBE_SEO_PRO_V2\.env")
ALLOWED_BASE="https://tuansuapi.store/v1"
SUPPORTED_IMAGE_MODELS={
    "gemini-3.1-flash-image-preview",
    "gemini-3-pro-image-preview",
    "gpt-image-2",
    "gpt-image-2.5-flare",
    "gpt-image-2.5-sunburst",
}
MAX_BYTES=16*1024*1024

class V2ImageError(RuntimeError): pass

def config():
    try:
        from . import tuansuapi_provider
    except (ImportError, ValueError):
        import tuansuapi_provider
    cfg = tuansuapi_provider.get_gateway_config()
    url = cfg.get("base_url") or ALLOWED_BASE
    key = cfg.get("api_key")
    model = cfg.get("image_model") or "gemini-3.1-flash-image-preview"
    if not key:
        raise V2ImageError("The Tuấn Stor key is missing; configure in Studio Settings or V2 .env")
    return url, key, model

def is_ready():
    try:
        config()
        return True
    except V2ImageError:
        return False

def make_image(prompt, output, reference_path=None, *, session=None, timeout=110):
    url,key,model=config()
    text=prompt.strip()
    if not 20<=len(text)<=20000:
        raise V2ImageError("Image prompt is empty or invalid")
    if reference_path and Path(reference_path).is_file():
        # OpenAI images generations text-only contract cannot pass a reference image.
        # Retain narrative consistency via detailed scene/bible prompt, don't pretend img2img works.
        text += "\nMaintain the established recurring character designs, distinct silhouettes and clothing."
    if "whiteboard" in text.lower():
        text += ("\nWhiteboard line-art only, crisp black ink on white. "
                 "Landscape cinematic 16:9 visual, no text, no hands, no drawing pens.")
    else:
        text += "\nLandscape cinematic 16:9 visual, masterpiece composition, highly detailed, no watermark, no text."
    # This exact shape was verified to return a valid image on this V2 provider.
    payload={"model":model, "prompt":text, "n":1, "size":"1024x1024"}
    client=session or requests.Session()
    try:
        response=client.post(url+"/images/generations",
            headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"},
            json=payload,timeout=timeout,allow_redirects=False)
    except requests.RequestException as e:
        raise V2ImageError("Tuấn Stor request timed out or network connection failed") from e
    if response.status_code!=200:
        # Do not print the upstream body or its headers; they can echo user secrets.
        raise V2ImageError("Tuấn Stor returned HTTP "+str(response.status_code)+" when creating image")
    try:
        data=response.json()
        entries=data.get("data",[])
        if not isinstance(entries,list) or not entries or not isinstance(entries[0],dict):
            raise ValueError("Image response not in expected synchronous OpenAI image format")
        item=entries[0]
        if isinstance(item.get("b64_json"),str):
            encoded=item["b64_json"]
            if len(encoded)>MAX_BYTES*2:
                raise ValueError("Image response is too large")
            binary=base64.b64decode(encoded,validate=True)
        elif isinstance(item.get("url"),str):
            # For the verified model we expect base64. Do not follow untrusted URLs by default.
            raise ValueError("Provider returned a URL rather than expected base64 image; not downloading automatically")
        else:
            raise ValueError("No image found in API response")
        if len(binary)>MAX_BYTES:
            raise ValueError("Image exceeds size limit")
        with Image.open(io.BytesIO(binary)) as original:
            original.load()
            if original.width<256 or original.height<256:
                raise ValueError("Image resolution too low")
            # Never distort the original 1:1 source. Pad to 16:9 for the whiteboard.
            rgb=original.convert("RGB")
            if abs(rgb.width/rgb.height-16/9)>0.01:
                rgb=ImageOps.pad(rgb,(1536,864),color="white",
                     method=Image.Resampling.LANCZOS,centering=(0.5,0.5))
            target=Path(output)
            target.parent.mkdir(parents=True,exist_ok=True)
            temp=target.with_name(target.stem+"."+uuid.uuid4().hex+".png")
            rgb.save(temp,format="PNG")
            os.replace(temp,target)
    except Exception as e:
        raise V2ImageError("Invalid Tuấn Stor image response; the scene was not marked complete") from e
    print("[TUAN_STOR_V2_IMAGE_PASS] model="+model+" size="+str(rgb.width)+"x"+str(rgb.height),flush=True)
    return str(target)
