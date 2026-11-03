# -*- coding: utf-8 -*-
"""Launch actual Storyboard AI pipeline E2E (new isolated 7-scene production)."""
from pathlib import Path
import json, subprocess, sys, time, os, hashlib
ROOT=Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0,str(ROOT))
from series_studio import slug
from muse_accounts import get_ready_accounts
series="QA Robot Ti Muse 6 Luong Oct26"
series_slug=slug(series)
ep=ROOT/"productions"/series_slug/"episode_001"
ready=get_ready_accounts()
print("QA_SERIES",series,"slug",series_slug)
print("READY_ACCOUNTS",len(ready))
if len(ready)<6: raise RuntimeError("E2E_NEEDS_SIX_READY_MUSE_ACCOUNTS")
if ep.exists() and any(ep.iterdir()):
 raise RuntimeError("QA_DESTINATION_NOT_EMPTY: no overwrite allowed")
ep.mkdir(parents=True,exist_ok=True)
qa_dir=ROOT/"diagnostics"/"qa_muse_parallel_20261026"
qa_dir.mkdir(parents=True,exist_ok=True)
prompt="""Viết tập thử nghiệm hoạt hình 3D điện ảnh liên tục: ROBOT TÍ VÀ NGỌN ĐÈN SAO.
Trong một xưởng sửa đồ chơi ven biển đầy ánh nắng, Robot Tí là robot tròn màu xanh lam,
mắt LED tròn màu hổ phách, vết xước hình X nhỏ trên má trái, đeo khăn quàng vàng,
không đổi kiểu dáng hoặc trang phục trong toàn tập. Đạo cụ quan trọng là đèn lồng bằng
đồng đỏ có cửa kính hình ngôi sao và bánh răng vàng. Robot Tí phát hiện đèn không sáng,
kiểm tra, tìm bánh răng, lắp, vặn tay quay, ánh sáng trở lại và cuối cùng nhìn ra biển.
Tất cả các cảnh xảy ra trong xưởng gỗ cạnh một cửa sổ tròn duy nhất.
Khóa ngoại hình nhân vật, đạo cụ, màu ánh sáng, bố trí nội thất qua mọi cảnh.
Chuyển động và hành động có nguyên nhân-hệ quả, mắt nhìn theo vật, trọng lực tự nhiên.
Không teleport, không thay mặt, không thay khăn vàng, không tự xuất hiện đồ vật.
Cốt truyện vui, an toàn, lời thoại tiếng Việt hoàn toàn. Phong cách hoạt hình 3D CGI,
chất liệu đẹp như phim điện ảnh, tuyệt đối không trở thành phim người đóng.
Chỉ tập trung một nhân vật chính Robot Tí và đèn lồng đồng xuyên suốt toàn tập.
Đây là một tập phim duy nhất liên tiếp, dài 70 giây, 7 cảnh x 10 giây."""
args=[
 str(ROOT/"runtime"/"python"/"python.exe"),"-u",str(ROOT/"pipeline_router.py"),"run",
 "--production-mode","cinematic_drama",
 "--series",series,
 "--episode","1",
 "--prompt",prompt,
 "--minutes","1.1666667",
 "--scene-seconds","10",
 "--language","Vietnamese",
 "--genre","animation",
 "--visual-style","animation_3d",
 "--size","1280x720",
 "--workers","6",
 "--image-provider","muse_video",
 "--input-mode","idea",
 "--model","gemini-3.8-flash",
 "--no-shorts",
 "--no-subtitles"
]
log_out=qa_dir/"stdout.log"
log_err=qa_dir/"stderr.log"
manifest=qa_dir/"run_manifest.json"
manifest.write_text(json.dumps({
 "series":series,"slug":series_slug,"episode_folder":str(ep),"ready_count":len(ready),
 "cmd_args_redacted":" ".join(args[:6])+" [series, prompts and options omitted]",
 "expected_scene_count":7,"expected_workers":6,
 "status":"LAUNCHING","created":time.strftime("%Y-%m-%d %H:%M:%S")
},ensure_ascii=False,indent=2),encoding="utf-8")
# Validate imports and code compile before real provider calls.
import py_compile
for name in ["pipeline_router.py","cinematic_engine/drama_orchestrator.py",
             "cinematic_engine/drama_planner.py","cinematic_engine/drama_video_engine.py",
             "muse_video_provider.py"]:
 py_compile.compile(str(ROOT/name),doraise=True)
fl=getattr(subprocess,"CREATE_NO_WINDOW",0)
with open(log_out,"wb") as o,open(log_err,"wb") as e:
 proc=subprocess.Popen(args,cwd=str(ROOT),stdout=o,stderr=e,creationflags=fl,
                       stdin=subprocess.DEVNULL,env={**os.environ,"PYTHONUTF8":"1","PYTHONIOENCODING":"utf-8"})
manifest_data=json.loads(manifest.read_text(encoding="utf-8"))
manifest_data["status"]="PROCESS_STARTED"
manifest_data["pid"]=proc.pid
manifest.write_text(json.dumps(manifest_data,ensure_ascii=False,indent=2),encoding="utf-8")
print("ACTUAL_PIPELINE_PID",proc.pid)
print("LOG_PATH",log_out)
print("QA_EPISODE_PATH",ep)
