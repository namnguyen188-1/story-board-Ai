"""Small, secure in-app asset review API for cinematic_drama only.
No arbitrary file paths from the browser; authorization uses exact episode assets.
"""
from __future__ import annotations
import json,re
from pathlib import Path
from urllib.parse import quote
from PIL import Image
from cinematic_engine.drama_asset_first import (
  _images_pass,validate_assets,bind_scene,AssetGateError,sha,atomic_write
)

def resolve_episode(production_root:Path,series:str,episode)->Path:
    from series_studio import slug
    name=str(series or "").strip()
    if not name or len(name)>160:raise ValueError("INVALID_SERIES")
    number=int(episode)
    if not 1<=number<=999:raise ValueError("INVALID_EPISODE")
    root=Path(production_root).resolve()
    # Both supported legacy and canonical series folders are retained.
    candidates=[root/slug(name)/f"episode_{number:03d}",
                root/name/f"episode_{number:03d}"]
    for p in candidates:
        p=p.resolve()
        if p.is_relative_to(root) and p.is_dir() and (p/"00_ASSET_PACK"/"asset_bible.json").is_file():
            return p
    raise FileNotFoundError("DRAMA_ASSET_BIBLE_NOT_READY")

def _manifest(ep:Path)->dict:
    p=ep/"00_ASSET_PACK"/"asset_bible.json"
    doc=json.loads(p.read_text(encoding="utf-8"))
    if doc.get("production_mode")!="cinematic_drama":raise ValueError("NOT_MULTI_ROLE_DRAMA")
    return doc

def _scene_num(value):
    n=int(value)
    if not 1<=n<=9999:raise ValueError("SCENE_INVALID")
    return n

def _find(ep:Path,kind:str,id:str)->tuple[dict,Path]:
    m=_manifest(ep)
    if kind in ("characters","locations","props"):
        item=m[kind].get(str(id))
        if not item:raise KeyError("ASSET_NOT_FOUND")
        folder=(ep/"00_ASSET_PACK"/item["folder"]).resolve()
        if not folder.is_relative_to((ep/"00_ASSET_PACK").resolve()):
            raise ValueError("UNSAFE_ASSET_PATH")
        return item,folder
    if kind=="scene":
        n=_scene_num(id)
        item=m["scenes"].get(f"scene_{n:04d}")
        if not item:raise KeyError("SCENE_NOT_FOUND")
        return item,ep/"scenes"/f"scene_{n:04d}"
    raise ValueError("UNKNOWN_ASSET_KIND")

def photo(ep:Path,kind:str,id:str)->Path:
    item,folder=_find(ep,kind,id)
    if kind=="scene":p=folder/"scene_master.png"
    else:
        p=folder/"muse_original_4views.png"
        if not p.is_file():p=Path(next(iter(item["views"].values()))["path"])
    p=p.resolve()
    if not p.is_relative_to(ep.resolve()) or not p.is_file() or p.suffix.lower() not in (".png",".jpg",".jpeg"):
        raise FileNotFoundError("ASSET_IMAGE_NOT_READY")
    if p.stat().st_size>12*1024*1024:raise ValueError("IMAGE_TOO_LARGE")
    return p

def snapshot(ep:Path,series:str,episode:int)->dict:
    m=_manifest(ep)
    q=validate_assets(ep,m)
    rows=[]
    for kind in ("characters","locations","props"):
        for entity_id,item in m[kind].items():
            valid,reason,hashes=_images_pass(item,ep/"00_ASSET_PACK")
            try:img=photo(ep,kind,entity_id)
            except (ValueError,FileNotFoundError):img=None
            rows.append({"kind":kind,"id":entity_id,"title":item.get("name") or entity_id,
                         "approved":valid,"state":reason,
                         "image_url":(f"/api/drama/assets/photo?series={quote(series)}&episode={episode}"
                            f"&kind={kind}&id={quote(entity_id)}") if img else None})
    for key,scene in m.get("scenes",{}).items():
        n=int(scene["scene_number"])
        folder=ep/"scenes"/f"scene_{n:04d}"
        proof=folder/"scene_master.json"
        # Show only generated scene stills. Unrendered placeholders for 66
        # scenes overwhelm the actual 17 master assets in the review dialog.
        if not (folder/"scene_master.png").is_file() and not proof.is_file():
            continue
        accepted=False;reason="SCENE_IMAGE_NOT_RENDERED"
        if proof.is_file() and (folder/"scene_master.png").is_file():
            try:
                p=json.loads(proof.read_text(encoding="utf-8"))
                ref=json.loads((folder/"scene_asset_binding.json").read_text(encoding="utf-8"))
                accepted=(p.get("approved") is True and
                          p.get("binding_sha256")==ref.get("binding_sha256") and
                          p.get("scene_image_sha256")==sha(folder/"scene_master.png"))
                reason="APPROVED" if accepted else "AWAITING_SCENE_REVIEW"
            except (OSError,ValueError,KeyError):
                reason="SCENE_IMAGE_PROOF_INVALID"
        rows.append({"kind":"scene","id":str(n),"title":f"Cảnh {n:02d}",
                     "approved":accepted,"state":reason,
                     "image_url":f"/api/drama/assets/photo?series={quote(series)}&episode={episode}&kind=scene&id={n}"
                                 if (folder/"scene_master.png").is_file() else None})
    return {"ok":True,"series":series,"episode":episode,"qc":q,"assets":rows,
            "message":"Duyệt đúng bộ ảnh thật; không chấp thuận ảnh sai hoặc giả 4 góc."}

def review(ep:Path,kind:str,id:str,approve:bool)->dict:
    item,folder=_find(ep,kind,id)
    root=ep/"00_ASSET_PACK"
    if kind=="scene":
        proof=folder/"scene_master.json"
        if not proof.is_file() or not (folder/"scene_master.png").is_file():
            raise FileNotFoundError("SCENE_IMAGE_NOT_READY")
        p=json.loads(proof.read_text(encoding="utf-8"))
        if p.get("source")!="Muse generated scene still":raise ValueError("IMAGE_SOURCE_NOT_PROVEN")
        sc=json.loads((ep/"drama_plan.json").read_text(encoding="utf-8"))["scenes"][_scene_num(id)-1]
        binding=bind_scene(ep,sc,verify_scene_image=False)
        if p.get("binding_sha256")!=binding["binding_sha256"] or p.get("scene_image_sha256")!=sha(folder/"scene_master.png"):
            raise ValueError("SCENE_IMAGE_STALE")
        p.update(approved=bool(approve),reviewer="Storyboard UI explicit human action")
        atomic_write(proof,p)
        if approve:bind_scene(ep,sc,verify_scene_image=True)
        return {"ok":True,"kind":kind,"id":id,"approved":bool(approve)}
    checks={}
    for view,data in item["views"].items():
        file=Path(data["path"])
        if not file.is_file() or file.stat().st_size<8000:raise ValueError("MISSING_ANGLE_"+view)
        with Image.open(file) as im:
            if min(im.size)<256:raise ValueError("LOW_RESOLUTION_"+view)
            im.verify()
        checks[view]=sha(file)
    if len(set(checks.values()))!=len(checks):raise ValueError("DUPLICATE_VIEW_IMAGE")
    atomic_write(folder/"approval.json",{
        "approved":bool(approve),"spec_sha256":item["spec_sha256"],"view_sha256":checks,
        "reviewer":"Storyboard UI explicit human action",
        "review_scope":"user reviewed master image sheet"})
    valid,why,_=_images_pass(item,root)
    if approve and not valid:raise ValueError("ASSET_APPROVAL_FAILED_"+why)
    validate_assets(ep)
    return {"ok":True,"kind":kind,"id":id,"approved":bool(approve)}
