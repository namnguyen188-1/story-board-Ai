"""Muse real scene-still generation, conditioned on approved cast/location/prop
asset references using explicit workspace uploads. Never asserts image conditioning
just from upload; returned scene must be visually reviewed before video.
"""
from __future__ import annotations
import base64,hashlib,json,os,subprocess,time,uuid
from pathlib import Path
from PIL import Image
from muse_gateway_worker import GatewayAPI,download,atomic_json
from cinematic_engine.drama_asset_first import bind_scene,sha

MUSE_PY=Path(r"D:\STORYBOARD_AI\studio\runtime\muse\python\python.exe")

def _upload(api,p:Path,remote:str):
    data=p.read_bytes()
    if not data or len(data)>8*1024*1024:raise ValueError("INVALID_REFERENCE_FILE_SIZE")
    for offset in range(0,len(data),22000):
        chunk=data[offset:offset+22000]
        api.call("fs.write",{"path":remote,"data_base64":base64.b64encode(chunk).decode("ascii"),
            "overwrite":offset==0,"append":offset!=0,"create_parent":offset==0})
    stat=api.call("fs.stat",{"path":remote})
    if stat.get("kind")!="file" or stat.get("size")!=len(data):
        raise RuntimeError("MUSE_SCENE_REFERENCE_UPLOAD_INCOMPLETE")
    return {"remote_path":remote,"sha256":sha(p),"bytes":len(data)}

def _pick_refs(binding):
    result=[]
    chosen={"characters":["front","three_quarter"],"locations":["master_wide","side_angle"],
            "props":["front","three_quarter"]}
    for kind,rows in binding["assets"].items():
        for row in rows:
            for view in chosen[kind]:
                if view in row["views"]:
                    result.append({"kind":kind,"id":row["id"],"view":view,
                                   "local_path":row["views"][view]["path"]})
    return result

def _status_file(api,path):
    try:
        v=api.call("fs.stat",{"path":path})
        if v.get("kind")=="file" and 30000<v.get("size",0)<20*1024*1024:return v
    except Exception:pass
    return None

def generate_scene(episode_dir:Path,scene:dict,*,timeout_s:int=210)->dict:
    ep=Path(episode_dir)
    binding=bind_scene(ep,scene,verify_scene_image=False)
    sn=int(scene["scene_number"])
    folder=ep/"scenes"/f"scene_{sn:04d}"
    folder.mkdir(parents=True,exist_ok=True)
    receipt_file=folder/"muse_scene_image_receipt.json"
    img=folder/"scene_master.png"
    proof=folder/"scene_master.json"
    sig=hashlib.sha256((binding["binding_sha256"]+"|"+str(scene.get("visual_setup") or "")).encode()).hexdigest()
    if img.is_file() and proof.is_file():
        old=json.loads(proof.read_text(encoding="utf-8"))
        if old.get("request_sha256")==sig and old.get("scene_image_sha256")==sha(img):
            return old
    receipt=json.loads(receipt_file.read_text(encoding="utf-8")) if receipt_file.is_file() else {}
    if receipt and (receipt.get("fingerprint")!=sig or receipt.get("state") in ("CAPABILITY_UNAVAILABLE", "ERROR")):
        if not (img.is_file() and img.stat().st_size > 1000):
            receipt = {}
        else:
            raise RuntimeError("MUSE_SCENE_MASTER_CHANGED: old receipt needs review before resubmit")
    api=GatewayAPI()
    try:
        if not receipt:
            start=api.call("session.start",{"method":"/api/session/start",
                 "params":{"origin":"fresh","lifecycle":"persistent","title":"Storyboard scene-image "+str(sn)}})
            sid=start.get("session_id") or start.get("id") or (start.get("session") or {}).get("session_id")
            if not sid:raise RuntimeError("MUSE_SCENE_IMAGE_NO_SESSION")
            tag="sbsceneimg"+uuid.uuid4().hex[:18]
            remote_output="workspace/storyboard_scene_images/"+tag+".png"
            receipt={"fingerprint":sig,"session_id":sid,"tag":tag,
                    "remote_output":remote_output,"state":"PREPARING_REFERENCES"}
            atomic_json(receipt_file,receipt)
            refs=_pick_refs(binding)
            remote_refs=[]
            for i,ref in enumerate(refs):
                p=Path(ref["local_path"])
                rem=f"workspace/storyboard_scene_refs/{tag}/{ref['kind']}_{ref['id']}_{ref['view']}.png"
                item=_upload(api,p,rem)
                item.update(kind=ref["kind"],asset_id=ref["id"],view=ref["view"])
                remote_refs.append(item)
            receipt["remote_references"]=remote_refs
            receipt["state"]="SUBMISSION_UNCERTAIN"
            atomic_json(receipt_file,receipt)
            formatted_refs="\n".join(f"- {r['kind']}/{r['asset_id']}/{r['view']}: /home/hatch/{r['remote_path']}"
                                    for r in remote_refs)
            prompt=(
              "Generate EXACTLY ONE actual 16:9 cinematic SCENE STILL IMAGE using the Muse image-generation tool. "
              "NOT a character sheet, NOT text to video. Match the approved actor, location and hero-prop references uploaded below: \n"
              +formatted_refs+
              "\nVisual story shot: "+str(scene.get("visual_setup") or scene.get("summary") or "")+
              "\nLocation: "+str(scene.get("setting") or "")+
              "\nCharacters: "+", ".join(map(str,scene.get("characters_present") or []))+
              "\nPhysical START STATE: "+str(scene.get("start_state") or "")+
              "\nMust preserve identity/wardrobe, actual architectural layout, and prop shape, color and placement. "
              "Avoid adding people or props. Carefully use the reference images as image inputs if the tool supports them. "
              "Store ONE final generated PNG at /home/hatch/"+remote_output+
              ". If image reference conditioning is unavailable, report this explicitly, do not invent proof. "
              "Return the actual local PNG file path. No extra variants; no videos.")
            env=os.environ.copy();env.update(MUSE_NO_UPDATE_CHECK="1",PYTHONUTF8="1",PYTHONIOENCODING="utf-8")
            try:
                p=subprocess.run([str(MUSE_PY),"-m","muse_cli","send",prompt,
                    "--thread",sid,"--wait","1"],capture_output=True,text=True,
                    encoding="utf-8",errors="replace",timeout=110,env=env,
                    creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
                receipt["cli_status"]=p.returncode
            except subprocess.TimeoutExpired:
                receipt["cli_status"]="timeout_uncertain"
            receipt["state"]="ACCEPTANCE_UNCONFIRMED"
            atomic_json(receipt_file,receipt)
        deadline=time.monotonic()+timeout_s
        while time.monotonic()<deadline:
            stat=_status_file(api,receipt["remote_output"])
            if stat:
                result=download(api,receipt["remote_output"],img)
                from cinematic_engine.drama_scene_aspect import frame_to_widescreen
                aspect_info=frame_to_widescreen(img)
                with Image.open(img) as im:
                    if min(im.size)<512:raise RuntimeError("MUSE_SCENE_IMAGE_TOO_SMALL")
                    im.verify()
                final={"status":"GENERATED_NEEDS_SCENE_VISUAL_QC",
                      "approved":False,"binding_sha256":binding["binding_sha256"],
                      "request_sha256":sig,"scene_image_sha256":sha(img),
                      "scene_image_path":str(img),"source":"Muse generated scene still",
                      "aspect_adaptation":aspect_info,
                      "remote_source":receipt["remote_output"],
                      "references_uploaded":receipt.get("remote_references",[])}
                atomic_json(proof,final)
                receipt["state"]="IMAGE_DOWNLOADED";atomic_json(receipt_file,receipt)
                return final
            history=api.call("chat.history",{"session_id":receipt["session_id"],"limit":20})
            reply=" ".join(str((v.get("payload") or {}).get("display_text") or v.get("display_text") or "")
                          for v in history.get("chat_events",[]) if v.get("event_name")=="message.assistant")
            if "IMAGE_TOOL_NOT_AVAILABLE" in reply or "IMAGE_REFERENCE_NOT_SUPPORTED" in reply:
                receipt["state"]="CAPABILITY_UNAVAILABLE";atomic_json(receipt_file,receipt)
                raise RuntimeError("MUSE_SCENE_IMAGE_CAPABILITY_UNAVAILABLE")
            time.sleep(5)
        receipt["state"]="PENDING_REMOTE";atomic_json(receipt_file,receipt)
        raise RuntimeError("MUSE_SCENE_IMAGE_PENDING: reuse receipt, do not resend")
    finally:
        api.close()
