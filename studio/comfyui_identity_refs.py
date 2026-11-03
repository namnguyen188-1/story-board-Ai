"""Local ComfyUI IP-Adapter conditioning for approved character reference photos."""
from __future__ import annotations
import hashlib
import json
import shutil
import urllib.request
from pathlib import Path
from PIL import Image

class CharacterIdentityUnavailable(RuntimeError):
    pass

def apply_character_references(workflow: dict, references: list, comfy_root: Path,
                               host: str, timeout: float = 8.0) -> dict:
    originals = [Path(p).resolve() for p in references if p]
    if not originals:
        return workflow
    unique=[]
    for p in originals:
        if not p.is_file():
            raise CharacterIdentityUnavailable("COMFY_CHARACTER_REFERENCE_MISSING: "+str(p))
        if p not in unique:
            unique.append(p)
    for folder,name in [
        ("ipadapter","ip-adapter-plus_sdxl_vit-h.safetensors"),
        ("clip_vision","clip_vision_h.safetensors"),
    ]:
        if not (comfy_root/"models"/folder/name).is_file():
            raise CharacterIdentityUnavailable("COMFY_IPADAPTER_MODEL_MISSING: "+name)
    try:
        with urllib.request.urlopen("http://"+host+"/object_info",timeout=timeout) as resp:
            classes=json.load(resp)
    except Exception as e:
        raise CharacterIdentityUnavailable("COMFY_IPADAPTER_SERVER_UNAVAILABLE") from e
    for cls in ("IPAdapterModelLoader","CLIPVisionLoader","IPAdapterAdvanced","LoadImage"):
        if cls not in classes:
            raise CharacterIdentityUnavailable("COMFY_IPADAPTER_NODE_UNAVAILABLE: "+cls)
    dest_dir=comfy_root/"input"
    dest_dir.mkdir(parents=True,exist_ok=True)
    prepared=[]
    for p in unique:
        with Image.open(p) as im:
            im.verify()
        digest=hashlib.sha256(p.read_bytes()).hexdigest()[:20]
        name="sb_character_"+digest+p.suffix.lower()
        dest=dest_dir/name
        if not dest.is_file() or dest.stat().st_size!=p.stat().st_size:
            shutil.copy2(p,dest)
        prepared.append(name)
    wf=dict(workflow)
    wf["19"]={"class_type":"CLIPVisionLoader","inputs":{"clip_name":"clip_vision_h.safetensors"}}
    wf["20"]={"class_type":"IPAdapterModelLoader","inputs":{"ipadapter_file":"ip-adapter-plus_sdxl_vit-h.safetensors"}}
    previous=["4",0]
    # Preserve both references independently rather than declaring them text
    # instructions. Human QC still needed for face/wardrobe accuracy.
    for idx,name in enumerate(prepared):
        img_id=str(21+idx*2)
        apply_id=str(22+idx*2)
        wf[img_id]={"class_type":"LoadImage","inputs":{"image":name}}
        wf[apply_id]={"class_type":"IPAdapterAdvanced","inputs":{
            "model":previous,
            "ipadapter":["20",0],
            "clip_vision":["19",0],
            "image":[img_id,0],
            "weight":0.55 if idx==0 else 0.35,
            "weight_type":"linear",
            "combine_embeds":"concat",
            "start_at":0.0,"end_at":0.90,
            "embeds_scaling":"V only"}}
        previous=[apply_id,0]
    wf["3"]=dict(wf["3"])
    wf["3"]["inputs"]=dict(wf["3"]["inputs"])
    wf["3"]["inputs"]["model"]=previous
    return wf
