"""Submit ONE actual idea-mode multi-role drama production via the live Storyboard AI UI backend.
Durable receipt before POST. No auto-retry when request status is uncertain.
"""
from pathlib import Path
from urllib import request,error
import json,sys,time,datetime,hashlib
sys.path.insert(0,r"D:\STORYBOARD_AI\studio")
from series_studio import slug
STUDIO=Path(r"D:\STORYBOARD_AI\studio")
SERIES="THIÊN SƯ: HUYỀN PHÙ TRẤN QUỶ"
TITLE="Tập 1: Đèn Lồng Thức Giấc"
prompt_path=Path(r"D:\STORYBOARD_AI\tools\THIEN_SU_HUYEN_PHU_TRAN_QUY_EP01_IDEA_20261031.txt")
root=STUDIO/"productions"/slug(SERIES)
ep=root/"episode_001"
receipt=root/"EP01_SUBMISSION_RECEIPT.json"
prompt=prompt_path.read_text(encoding="utf-8")
assert "CHỈ SẢN XUẤT TẬP 1" in prompt
root.mkdir(parents=True,exist_ok=True)
bible={
 "series":SERIES,"series_id":slug(SERIES),"series_format":"7 x 10-12 minute connected fantasy mystery episodes",
 "planned_episodes":7,"target_minutes_each":11.0,"language":"Vietnamese",
 "production_mode":"cinematic_drama","image_provider":"muse_video",
 "episode_arcs":[
  {"episode":1,"title":"Đèn Lồng Thức Giấc","event":"The lamps turn on in abandoned Hồng Đăng; Thanh Y finds the master's warning; Vô Cảnh appears."},
  {"episode":2,"title":"Oán Khí Trong Miếu Cũ","event":"Thanh Y allies with Vô Cảnh, investigates shrine and first curse evidence."},
  {"episode":3,"title":"Đêm Tế Lễ Đã Mất","event":"Hidden ritual ledger reveals villagers' fate and conflicting testimony."},
  {"episode":4,"title":"Hồn Giữ Miếu","event":"Old village guardian names the lantern keeper."},
  {"episode":5,"title":"Thiên Thư Mở Ấn","event":"Thanh Y opens part of the seal to defend the village."},
  {"episode":6,"title":"Sư Phụ Trong Bóng Tối","event":"Master's disappearance explained; he may be holding the ancient barrier."},
  {"episode":7,"title":"Huyền Phù Trấn Quỷ","event":"Final ritual resolves the curse, preserves the master's fate and concludes arc."}
 ],
 "character_registry":{
  "luc_thanh_y":"23-year-old Vietnamese female exorcist, long black hair half up with green wooden pin; ivory and pale-blue Taoist robe, dark blue sash and dark boots; keep same voice and outfit until scripted change",
  "huyen_dao_nhan":"56-year-old male master, short gray beard, top-knot salt and pepper hair, charcoal-gray Taoist robe with olive trim; flashback ep1",
  "tran_vo_canh":"28-year-old male wanderer, black hair tied back, dark-brown coat over black clothes, old leather belt; entrance only ep1 climax",
  "linh_ba":"female red-robed mysterious silhouette in episode1; stable identity to be defined in future episodes"
 },
 "location_registry":{
  "thanh_van_tao_quan":"wood-floor monastery, ancestor altar, wooden lattice door, oil lamp, bookshelves",
  "van_mong_mountain_pass":"stone path, bamboo forest, old wooden railing",
  "hong_dang_village_gate":"weathered stone gate, banyan tree to LEFT, matching red lanterns",
  "hong_dang_main_street":"blue-gray wet stone road, aging wooden houses on both sides, one stable street axis",
  "tran_hon_shrine":"gray-stone shrine, worn statue, stone altar, wooden door on RIGHT"
 },
 "hero_prop_registry":{
  "thien_thu":"indigo-black ancient scripture with round bagua symbol and red seal cord",
  "huyen_phu":"yellow paper charm with vermillion character strokes",
  "chu_sa_brush":"dark wooden brush with crimson-tinted bristles",
  "tran_hon_bell":"small bronze bell with three etched marks",
  "cloth_charm_pouch":"indigo cloth pouch carried by Thanh Y",
  "red_lantern":"distinctive red silk lantern with cloud motif"
 },
 "episode_one_target":{"minutes":11,"scene_duration_seconds":10,"scenes":66,
                       "locations_at_most":5,"named_hero_props_at_most":6,
                       "master_asset_group_limit":20},
 "rules":["create real 4-angle character masters; master sets and physical hero props FIRST",
          "force reference approval in app before rendering scene images",
          "force scene image approval before Muse I2V",
          "stable names, physical prop hand ownership and state, no duplicate entities",
          "all dialogue exclusively Vietnamese; subtitles timed to actual audio",
          "no YouTube publishing without explicit QC and publication approval",
          "do not produce episodes 2 through 7 until later separate request"]
}
bible_path=root/"SERIES_BIBLE_7_TAP.json"
if not bible_path.is_file():
 bible_path.write_text(json.dumps(bible,ensure_ascii=False,indent=2),encoding="utf-8")
elif json.loads(bible_path.read_text(encoding="utf-8")).get("series")!=SERIES:
 raise RuntimeError("SERIES_BIBLE_NAME_CONFLICT")
if (ep/"episode_001_final.mp4").exists() or (ep/"drama_plan.json").exists():
 raise RuntimeError("EPISODE_ALREADY_EXISTS: prevent duplicate and protect active work")
if receipt.exists():
 print("SUBMISSION_RECEIPT_EXISTS_DO_NOT_RESUBMIT",receipt.read_text(encoding="utf-8")[:750],flush=True)
 raise SystemExit(0)
status=json.load(request.urlopen("http://127.0.0.1:8765/api/status",timeout=7))
queue=json.loads((STUDIO/"production_queue.json").read_text(encoding="utf-8"))
if status.get("running") or queue.get("active") or queue.get("items"):
 raise RuntimeError("STORYBOARD_BUSY_NO_CONCURRENT_JOB")
payload={
 "production_mode":"cinematic_drama","series":SERIES,"episode":1,
 "prompt":prompt,"input_mode":"idea","reference_url":"",
 "minutes":11.0,"scene_seconds":10,"language":"Vietnamese","voice_name":"auto",
 "speech_pacing":"normal","genre":"psychological_horror","visual_style":"color_cinematic",
 "user_explicit_genre":True,"user_explicit_style":True,
 "region":"auto","mode":"live","image_provider":"muse_video","model":"gemini-3.5-flash",
 "size":"1280x720","workers":2,"mcp_model_index":1,"mcp_max_images":66,
 "mcp_visual_policy":"unique","auto_minimize_browser":True,
 "clean_watermark":True,"resume":False,"force_new":False,
 "subtitle_style":"karaoke_viral","subtitle_size":58,"camera_motion":"auto",
 "atmospheric_overlay":"auto","motion_mode":"ken_burns",
 "flow_video_model":"Omni 1.1 Flash","flow_video_duration":8,
 "auto_upload":False
}
body=json.dumps(payload,ensure_ascii=False).encode("utf-8")
audit={"series":SERIES,"episode":1,"mode":"live","input_mode":"idea",
       "production_mode":"cinematic_drama","image_provider":"muse_video",
       "minutes":11.0,"planned_scenes":66,"prompt_sha256":hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
       "submitted_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
       "state":"HTTP_SUBMISSION_UNCERTAIN","series_bible":str(bible_path)}
receipt.write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding="utf-8")
try:
 req=request.Request("http://127.0.0.1:8765/api/produce",body,{"Content-Type":"application/json; charset=utf-8"},method="POST")
 with request.urlopen(req,timeout=50) as response:
  raw=response.read()
  parsed=json.loads(raw)
  audit.update(state="ACCEPTED" if 200<=response.status<300 else "NON_2XX",http_status=response.status,response=parsed)
except error.HTTPError as exc:
 body_text=exc.read().decode("utf-8",errors="replace")[:2500]
 audit.update(state="REJECTED",http_status=exc.code,response=body_text)
except Exception as exc:
 audit.update(state="HTTP_UNCERTAIN_DO_NOT_RESUBMIT",error=str(exc))
receipt.write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding="utf-8")
print("STORYBOARD_SUBMISSION_RESULT",json.dumps(audit,ensure_ascii=False),flush=True)
