"""Test script to verify all camera motions and overlay blending in FFmpeg."""
import subprocess, math, os
from pathlib import Path

FFMPEG = "d:\\STORYBOARD_AI\\studio\\engine\\bin\\ffmpeg.exe"
SRC_IMG = "d:\\STORYBOARD_AI\\studio\\diagnostics\\mcp_integration_mock_scene.png"
OVERLAYS_DIR = Path("d:\\STORYBOARD_AI\\studio\\engine\\assets\\overlays")
OUTPUT_DIR = Path("d:\\STORYBOARD_AI\\studio\\diagnostics\\test_motions")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

width, height = 1280, 720
fps = 25
duration_sec = 4
frames = fps * duration_sec

motions = {
    "zoom_in": (
        f"zoompan=z='min(1.0+0.18*(on/{frames}),1.25)':"
        f"x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':"
        f"d={frames}:s={width}x{height}:fps={fps}"
    ),
    "zoom_out": (
        f"zoompan=z='max(1.18-0.18*(on/{frames}),1.0)':"
        f"x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':"
        f"d={frames}:s={width}x{height}:fps={fps}"
    ),
    "pan_right": (
        f"zoompan=z='1.15':"
        f"x='(iw-iw/zoom)*0.10+(iw-iw/zoom)*0.80*(on/{frames})':"
        f"y='(ih-ih/zoom)/2':"
        f"d={frames}:s={width}x{height}:fps={fps}"
    ),
    "pan_left": (
        f"zoompan=z='1.15':"
        f"x='(iw-iw/zoom)*0.90-(iw-iw/zoom)*0.80*(on/{frames})':"
        f"y='(ih-ih/zoom)/2':"
        f"d={frames}:s={width}x{height}:fps={fps}"
    ),
    "tilt_up": (
        f"zoompan=z='1.15':"
        f"x='(iw-iw/zoom)/2':"
        f"y='(ih-ih/zoom)*0.85-(ih-ih/zoom)*0.70*(on/{frames})':"
        f"d={frames}:s={width}x{height}:fps={fps}"
    ),
    "orbit_drift": (
        f"zoompan=z='1.12+0.08*(on/{frames})':"
        f"x='(iw-iw/zoom)/2+(iw-iw/zoom)*0.35*sin(2*PI*(on/{frames})*0.8)':"
        f"y='(ih-ih/zoom)/2+(ih-ih/zoom)*0.35*cos(2*PI*(on/{frames})*0.8)':"
        f"d={frames}:s={width}x{height}:fps={fps},"
        f"rotate='0.007*sin(2*PI*t/{duration_sec})':ow='{width}':oh='{height}':c=black"
    )
}

print("Testing camera motions...")
for name, vf in motions.items():
    out_mp4 = OUTPUT_DIR / f"test_{name}.mp4"
    cmd = [
        FFMPEG, "-hide_banner", "-loglevel", "error", "-y",
        "-loop", "1", "-framerate", str(fps), "-i", SRC_IMG,
        "-vf", vf + ",format=yuv420p",
        "-frames:v", str(frames),
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "22",
        str(out_mp4)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"FAILED motion {name}: {res.stderr}")
    else:
        print(f"PASS motion {name} -> {out_mp4.name} ({out_mp4.stat().st_size} bytes)")

print("\nTesting overlay blend on orbit_drift...")
overlay_file = OVERLAYS_DIR / "dust_particles.mp4"
out_blend = OUTPUT_DIR / "test_orbit_with_dust.mp4"
filter_complex = (
    f"[0:v]{motions['orbit_drift']},format=rgba[base];"
    f"[1:v]scale={width}:{height},format=rgba[ovl];"
    f"[base][ovl]blend=all_mode='screen':all_opacity=0.45,format=yuv420p[vout]"
)
cmd_blend = [
    FFMPEG, "-hide_banner", "-loglevel", "error", "-y",
    "-loop", "1", "-framerate", str(fps), "-i", SRC_IMG,
    "-stream_loop", "-1", "-i", str(overlay_file),
    "-filter_complex", filter_complex,
    "-map", "[vout]",
    "-frames:v", str(frames),
    "-c:v", "libx264", "-preset", "ultrafast", "-crf", "22",
    str(out_blend)
]
res_b = subprocess.run(cmd_blend, capture_output=True, text=True)
if res_b.returncode != 0:
    print(f"FAILED blend: {res_b.stderr}")
else:
    print(f"PASS blend -> {out_blend.name} ({out_blend.stat().st_size} bytes)")
