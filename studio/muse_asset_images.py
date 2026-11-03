"""Muse CLI image sheet adapter for multi-role preproduction (not Muse video).
Real generation only, exactly one submit per asset fingerprint. Durable receipts.
Run using Studio's Muse Python runtime, which has muse_cli installed.
"""
from __future__ import annotations
import hashlib,json,os,re,subprocess,sys,time,uuid
from pathlib import Path
from PIL import Image
from muse_gateway_worker import GatewayAPI,download,atomic_json,workspace_path
from cinematic_engine.drama_asset_first import sha,VIEW_SPEC

MUSE_PY = Path(r"D:\STORYBOARD_AI\studio\runtime\muse\python\python.exe")

def _instruction(asset:dict,kind:str,tag:str)->str:
    targets=VIEW_SPEC[kind]
    views={
     "characters":"1 FRONT FULL BODY, 2 THREE-QUARTER LEFT FULL BODY, 3 STRICT SIDE PROFILE FULL BODY, 4 REAR FULL BODY",
     "locations":"1 WIDE MASTER, 2 REVERSE CAMERA VIEW, 3 LEFT CAMERA VIEW, 4 RIGHT CAMERA VIEW of the identical architecture",
     "props":"1 FRONT VIEW, 2 THREE-QUARTER VIEW, 3 EXTREME CLOSE-UP DETAIL, 4 REAR VIEW of the identical physical prop",
    }[kind]
    profile=asset.get("profile") or {}
    name=asset["name"]
    identity=profile.get("appearance_lock") or profile.get("appearance") or profile.get("description") or profile.get("spec") or name
    outfit=profile.get("attire") or profile.get("wardrobe") or profile.get("wardrobe_by_act") or ""
    isolation = ({
      "characters": "CHARACTER DESIGN: ONLY the described single actor in each panel. Same real face, full-body, exact locked outfit. Neutral studio backdrop.",
      "locations": "EMPTY ENVIRONMENT / ARCHITECTURE ONLY. ABSOLUTELY NO PEOPLE OR HUMAN SILHOUETTES IN ANY OF FOUR PANELS. No visitors, travelers, models, mannequins, characters, faces or bodies. The location must show only architecture/terrain/landmarks with stable physical placement. Every panel uses a genuinely distinct camera position in the same empty place.",
      "props": "ISOLATED PRODUCT PHOTOGRAPHY OF THE SINGLE PHYSICAL OBJECT ONLY, suspended or placed on a neutral gray seamless backdrop in all four panels. NO HUMAN, MODEL, HANDS, CLOTHING, ACTORS, WEARERS OR FACES; no costume demonstrations. The item alone must occupy 60-80 percent of each panel. 4 distinct angles of the SAME SINGLE OBJECT. Do not depict a person holding, carrying, wearing or operating it.",
    })[kind]
    return (
     "Use the real Muse image-generation tool to generate EXACTLY ONE image (not video) for STORYBOARD AI. "
     +isolation+" "
     "It MUST be a 2-by-2 grid containing FOUR distinct photographic camera angles, reading left-to-right and top-to-bottom: "
     +views+". Subject: "+str(name)+". Identity/design specification: "+str(identity)+". Outfit: "+str(outfit)+". "
     "Maintain the EXACT same identity, colors, material, shape, scene geometry and props across all four panels. "
     "For CHARACTER model sheets: show COMPLETE FULL-BODY from the top of the head to shoe soles in EVERY one of the four panels; leave 10 percent padding above the head and below the feet; NEVER crop at waist, knees, ankles, arms or toes, NEVER show a portrait or half body. Each panel must contain one entire standing person. "
     "Do not fill the panel with an oversized human. Keep 4 human silhouettes at identical full-height scale in their respective panels. "
     "Neutral grey background for actor/prop sheets, no background actors. For rooms, no people. "
     "Actual four perspectives, NEVER repeat or horizontally mirror a single photo. "
     "Generate an actual readable PNG file and SAVE it at /home/hatch/workspace/storyboard_preproduction/"
     +tag+".png . Only ONE generation attempt. "
     "Reply with exact saved file path only. If image tool unavailable report IMAGE_TOOL_NOT_AVAILABLE, "
     "do not invent an output path. No videos."
    )

def _probe_image(api,path):
    try:
        stat=api.call("fs.stat",{"path":path})
        return stat if stat.get("kind")=="file" and 20000<stat.get("size",0)<24*1024*1024 else None
    except Exception:
        return None

def generate_sheet(asset:dict,kind:str,episode_dir:Path,*,timeout_s:int=180)->dict:
    if kind not in VIEW_SPEC:raise ValueError("INVALID_ASSET_KIND")
    ep=Path(episode_dir)
    base=ep/"00_ASSET_PACK"/asset["folder"]
    base.mkdir(parents=True,exist_ok=True)
    sheet=base/"muse_original_4views.png"
    receipt_file=base/"muse_sheet_receipt.json"
    if sheet.is_file() and sheet.stat().st_size>20000:
        return _import_sheet(sheet,asset,kind,base,receipt_file,already_downloaded=True)
    receipt=json.loads(receipt_file.read_text(encoding="utf-8")) if receipt_file.is_file() else {}
    fingerprint=hashlib.sha256((asset["spec_sha256"]+"|"+kind).encode()).hexdigest()
    if receipt and receipt.get("fingerprint")!=fingerprint:
        raise RuntimeError("MUSE_ASSET_SPEC_CHANGED: keep original receipt for review; do not resubmit")
    api=GatewayAPI()
    try:
        if not receipt:
            start=api.call("session.start",{"method":"/api/session/start",
                "params":{"origin":"fresh","lifecycle":"persistent",
                          "title":"Storyboard master "+kind+"/"+asset["id"]}})
            sid=start.get("session_id") or start.get("id") or (start.get("session") or {}).get("session_id")
            if not sid:raise RuntimeError("MUSE_ASSET_SESSION_MISSING")
            tag="sbasset"+uuid.uuid4().hex[:20]
            receipt={"fingerprint":fingerprint,"kind":kind,"asset_id":asset["id"],"session_id":sid,
                     "tag":tag,"remote_path":"workspace/storyboard_preproduction/"+tag+".png",
                     "state":"SUBMISSION_UNCERTAIN"}
            atomic_json(receipt_file,receipt)
            # No retries: a CLI timeout may still mean the request was accepted.
            if not MUSE_PY.is_file(): raise RuntimeError("MUSE_PYTHON_MISSING")
            env=os.environ.copy()
            env.update(MUSE_NO_UPDATE_CHECK="1",PYTHONUTF8="1",PYTHONIOENCODING="utf-8")
            try:
                p=subprocess.run([str(MUSE_PY),"-m","muse_cli","send",
                    _instruction(asset,kind,tag),"--thread",sid,"--wait","1"],
                    capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=110,env=env,
                    creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
                receipt["cli_return_code"]=p.returncode
            except subprocess.TimeoutExpired:
                receipt["cli_return_code"]="timeout_uncertain"
            receipt["state"]="ACCEPTANCE_UNCONFIRMED"
            atomic_json(receipt_file,receipt)
        # Resume with original receipt: do not submit a second request.
        deadline=time.monotonic()+timeout_s
        while time.monotonic()<deadline:
            stat=_probe_image(api,receipt["remote_path"])
            if stat:
                download(api,receipt["remote_path"],sheet)
                receipt["state"]="DOWNLOADED"
                receipt["image_sha256"]=sha(sheet)
                receipt["remote_size"]=stat["size"]
                atomic_json(receipt_file,receipt)
                return _import_sheet(sheet,asset,kind,base,receipt_file)
            history=api.call("chat.history",{"session_id":receipt["session_id"],"limit":15})
            lines=[str((x.get("payload") or {}).get("display_text") or x.get("display_text") or "")
                for x in history.get("chat_events",[]) if x.get("event_name")=="message.assistant"]
            low=" ".join(lines).lower()
            if "image_tool_not_available" in low or "cannot generate image" in low:
                receipt["state"]="IMAGE_CAPABILITY_UNAVAILABLE";atomic_json(receipt_file,receipt)
                raise RuntimeError("MUSE_IMAGE_CAPABILITY_UNAVAILABLE: "+asset["id"])
            time.sleep(5)
        receipt["state"]="PENDING_REMOTE";atomic_json(receipt_file,receipt)
        raise RuntimeError("MUSE_IMAGE_JOB_PENDING: resume original session, do not submit again")
    finally:
        api.close()

def _import_sheet(sheet:Path,asset:dict,kind:str,base:Path,receipt_file:Path,
                  *,already_downloaded:bool=False)->dict:
    # Cropping FOUR genuinely generated panels is allowed; synthetic mirroring,
    # blurring, and cloning the same source into four supposed views are not.
    with Image.open(sheet) as im:
        im.load()
        w,h=im.size
        if w<1000 or h<640:
            raise RuntimeError("MUSE_IMAGE_GRID_RESOLUTION_LOW")
        cells=[
          (0,0,w//2,h//2),(w//2,0,w,h//2),
          (0,h//2,w//2,h),(w//2,h//2,w,h),
        ]
        generated={}
        for i,view in enumerate(VIEW_SPEC[kind]):
            target=Path(asset["views"][view]["path"])
            crop=im.crop(cells[i]).convert("RGB")
            crop.save(target,format="PNG")
            generated[view]=sha(target)
    if len(set(generated.values()))!=len(generated):
        raise RuntimeError("MUSE_IMAGE_ANGLES_DUPLICATED")
    result={"status":"GENERATED_NEEDS_VISUAL_QC","kind":kind,"asset_id":asset["id"],
            "sheet":str(sheet),"sheet_sha256":sha(sheet),"source":"Muse live image",
            "images":generated,"approved":False}
    atomic_json(base/"generation_proof.json",result)
    return result
