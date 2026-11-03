from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
orch_py = ROOT / "studio" / "cinematic_engine" / "drama_orchestrator.py"
lines = orch_py.read_text(encoding="utf-8").splitlines(keepends=True)

target_idx = -1
for i, l in enumerate(lines):
    if "muse_clip.mp4" in l and "Bắt buộc dựng lại 100%" in l:
        target_idx = i
        break

if target_idx != -1:
    # Find the preceding 'else:' line
    else_idx = target_idx - 1
    while else_idx >= 0 and "else:" not in lines[else_idx]:
        else_idx -= 1
    
    replacement = [
        "                elif (sc_dir / \"fallback_used.json\").is_file():\n",
        "                    from .drama_video_engine import get_media_duration\n",
        "                    final_dur = get_media_duration(final_scene_mp4)\n",
        "                    print(f\"[CẢNH {sc_num:02d}] Đã hoàn thiện ở chế độ Fallback điện ảnh ({final_scene_mp4.name}, {final_dur:.1f}s), tái sử dụng.\", flush=True)\n",
        "                    print(f\"SCENE_PASS {sc_num}\", flush=True)\n",
        "                    return sc_num, final_scene_mp4\n",
        "                else:\n",
        "                    print(f\"[CẢNH {sc_num:02d}] Cảnh cũ thiếu muse_clip.mp4 -> Thử dựng lại bằng Muse AI Video...\", flush=True)\n"
    ]
    lines[else_idx:target_idx+1] = replacement
    orch_py.write_text("".join(lines), encoding="utf-8")
    print(f"SUCCESS: Patched fallback resume check at lines {else_idx}-{target_idx}")
else:
    print("Already patched or pattern not found.")
