"""Procedural generator for high-quality seamless atmospheric overlay loops.
Generates:
1. dust_particles.mp4 (Cinematic golden floating bokeh dust motes)
2. cinematic_smoke.mp4 (Soft volumetric drifting mist/fog wisps)
3. falling_snow.mp4 (Gentle fluttering falling snowflakes)
All assets are 1280x720, 25fps, 10s (250 frames), perfectly seamless loops.
"""
from __future__ import annotations
import math, os, subprocess, tempfile
from pathlib import Path
import cv2
import numpy as np

ENGINE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = ENGINE_DIR / "assets" / "overlays"
WIDTH = 1280
HEIGHT = 720
FPS = 25
DURATION_SEC = 10
TOTAL_FRAMES = FPS * DURATION_SEC

# Locate FFmpeg binary
FFMPEG_BIN = str(ENGINE_DIR / "bin" / "ffmpeg.exe")
if not os.path.exists(FFMPEG_BIN):
    FFMPEG_BIN = "ffmpeg"


def encode_frames_to_mp4(frame_generator, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.parent / f"temp_{output_path.name}"
    
    cmd = [
        FFMPEG_BIN, "-hide_banner", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "bgr24",
        "-s", f"{WIDTH}x{HEIGHT}", "-r", str(FPS),
        "-i", "pipe:0",
        "-c:v", "libx264", "-preset", "slow", "-crf", "18",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(tmp_path)
    ]
    
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    for frame in frame_generator():
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    stderr = proc.stderr.read()
    proc.wait()
    
    if proc.returncode != 0:
        if tmp_path.exists(): tmp_path.unlink()
        raise RuntimeError(f"FFmpeg encode failed for {output_path.name}: {stderr.decode('utf-8', 'replace')}")
    
    if output_path.exists():
        output_path.unlink()
    os.replace(tmp_path, output_path)
    print(f"Generated {output_path.name} successfully ({output_path.stat().st_size / 1024:.1f} KB)")


def generate_dust_particles():
    """Generates 150 particles with depth, bokeh, Brownian drift, and golden amber glow."""
    np.random.seed(42)
    n_particles = 160
    
    # Particle properties
    x0 = np.random.uniform(0, WIDTH, n_particles)
    y0 = np.random.uniform(0, HEIGHT, n_particles)
    depth = np.random.uniform(0.15, 1.0, n_particles)  # 0.15=far away, 1.0=close
    
    # Motion frequencies (must be integers for seamless 10s loop)
    k_y = np.random.choice([1, 2, 3], n_particles)  # integer vertical loops
    m_x = np.random.choice([1, 2, 3], n_particles)  # integer horizontal cycles
    phi_x = np.random.uniform(0, 2 * math.pi, n_particles)
    amp_x = np.random.uniform(15, 55, n_particles) * depth
    
    # Twinkle frequency (integer)
    twinkle_k = np.random.choice([1, 2, 4], n_particles)
    twinkle_phi = np.random.uniform(0, 2 * math.pi, n_particles)
    
    # Colors: mix of warm golden amber and soft warm white
    color_types = np.random.choice([0, 1], n_particles, p=[0.7, 0.3])
    
    for f in range(TOTAL_FRAMES):
        t = f / TOTAL_FRAMES
        theta = 2 * math.pi * t
        
        # Black canvas
        canvas = np.zeros((HEIGHT, WIDTH, 3), dtype=np.float32)
        
        for i in range(n_particles):
            # Compute position with seamless wrap
            curr_y = (y0[i] - k_y[i] * HEIGHT * t) % HEIGHT
            curr_x = (x0[i] + amp_x[i] * math.sin(m_x[i] * theta + phi_x[i])) % WIDTH
            
            # Brightness modulation
            twinkle = 0.75 + 0.25 * math.cos(twinkle_k[i] * theta + twinkle_phi[i])
            alpha = depth[i] * twinkle
            
            # Radius and color based on depth
            radius = 1.0 + depth[i] * 4.5
            if color_types[i] == 0:
                # Golden amber (B, G, R)
                color = np.array([120, 205, 255], dtype=np.float32) * (alpha * 0.95)
            else:
                # Soft cinematic warm white
                color = np.array([210, 235, 255], dtype=np.float32) * (alpha * 0.9)
            
            ix, iy = int(round(curr_x)), int(round(curr_y))
            r_int = max(1, int(math.ceil(radius)))
            
            # Draw core circle
            cv2.circle(canvas, (ix, iy), r_int, color.tolist(), -1, lineType=cv2.LINE_AA)
            
            # Foreground particles get soft bokeh halo
            if depth[i] > 0.65:
                halo_color = color * 0.35
                cv2.circle(canvas, (ix, iy), r_int * 2 + 1, halo_color.tolist(), -1, lineType=cv2.LINE_AA)
        
        # Subtle Gaussian blur to give optical camera diffusion
        blurred = cv2.GaussianBlur(canvas, (5, 5), 1.2)
        # Blend crisp and blurred
        final = np.clip(canvas * 0.7 + blurred * 0.5, 0, 255).astype(np.uint8)
        yield final


def generate_cinematic_smoke():
    """Generates soft, undulating volumetric smoke and fog wisps."""
    np.random.seed(101)
    n_wisps = 16
    
    # Centers of fog clouds
    x0 = np.random.uniform(0, WIDTH, n_wisps)
    y0 = np.random.uniform(HEIGHT * 0.2, HEIGHT * 0.9, n_wisps)
    radii_x = np.random.uniform(160, 320, n_wisps)
    radii_y = np.random.uniform(90, 200, n_wisps)
    
    k_x = np.random.choice([1, 2], n_wisps)
    phi_x = np.random.uniform(0, 2 * math.pi, n_wisps)
    drift_x = np.random.uniform(80, 220, n_wisps)
    
    k_y = np.random.choice([1, 2], n_wisps)
    phi_y = np.random.uniform(0, 2 * math.pi, n_wisps)
    drift_y = np.random.uniform(20, 60, n_wisps)
    
    intensities = np.random.uniform(28, 65, n_wisps)
    
    for f in range(TOTAL_FRAMES):
        t = f / TOTAL_FRAMES
        theta = 2 * math.pi * t
        
        canvas = np.zeros((HEIGHT, WIDTH), dtype=np.float32)
        
        for i in range(n_wisps):
            # Smooth periodic displacement
            cx = (x0[i] + drift_x[i] * math.sin(k_x[i] * theta + phi_x[i])) % WIDTH
            cy = (y0[i] + drift_y[i] * math.cos(k_y[i] * theta + phi_y[i]))
            
            # Breathing expansion
            rx = int(radii_x[i] * (1.0 + 0.15 * math.sin(theta + phi_x[i])))
            ry = int(radii_y[i] * (1.0 + 0.15 * math.cos(theta + phi_y[i])))
            
            # Draw ellipse
            cv2.ellipse(canvas, (int(cx), int(cy)), (max(10, rx), max(10, ry)), 
                        math.degrees(phi_x[i]), 0, 360, float(intensities[i]), -1)
            
            # If close to border, draw wrap-around counterpart for seamless edge
            if cx < rx:
                cv2.ellipse(canvas, (int(cx + WIDTH), int(cy)), (max(10, rx), max(10, ry)),
                            math.degrees(phi_x[i]), 0, 360, float(intensities[i]), -1)
            elif cx > WIDTH - rx:
                cv2.ellipse(canvas, (int(cx - WIDTH), int(cy)), (max(10, rx), max(10, ry)),
                            math.degrees(phi_x[i]), 0, 360, float(intensities[i]), -1)
        
        # Heavy volumetric diffusion blur
        fog = cv2.GaussianBlur(canvas, (101, 101), 45.0)
        fog = np.clip(fog * 1.35, 0, 255)
        
        # Tint slightly cool bluish-white (cinematic smoke)
        b = (fog * 0.88).astype(np.uint8)
        g = (fog * 0.82).astype(np.uint8)
        r = (fog * 0.78).astype(np.uint8)
        
        frame = cv2.merge([b, g, r])
        yield frame


def generate_falling_snow():
    """Generates 280 gentle falling snowflakes with natural flutter and depth."""
    np.random.seed(88)
    n_flakes = 280
    
    x0 = np.random.uniform(0, WIDTH, n_flakes)
    y0 = np.random.uniform(0, HEIGHT, n_flakes)
    depth = np.random.uniform(0.2, 1.0, n_flakes)
    
    # Downward loops across 10s: flakes complete 2 to 6 full cycles
    k_y = np.random.choice([2, 3, 4, 5, 6], n_flakes)
    m_x = np.random.choice([1, 2, 3], n_flakes)
    phi_x = np.random.uniform(0, 2 * math.pi, n_flakes)
    flutter_amp = np.random.uniform(8, 28, n_flakes) * depth
    
    for f in range(TOTAL_FRAMES):
        t = f / TOTAL_FRAMES
        theta = 2 * math.pi * t
        
        canvas = np.zeros((HEIGHT, WIDTH, 3), dtype=np.float32)
        
        for i in range(n_flakes):
            curr_y = (y0[i] + k_y[i] * HEIGHT * t) % HEIGHT
            curr_x = (x0[i] + flutter_amp[i] * math.sin(m_x[i] * theta + phi_x[i])) % WIDTH
            
            radius = 1.0 + depth[i] * 3.8
            brightness = 140 + depth[i] * 115
            color = [brightness, brightness, brightness]
            
            ix, iy = int(round(curr_x)), int(round(curr_y))
            r_int = max(1, int(math.ceil(radius)))
            
            cv2.circle(canvas, (ix, iy), r_int, color, -1, lineType=cv2.LINE_AA)
            if depth[i] > 0.8:
                # Foreground soft flake halo
                cv2.circle(canvas, (ix, iy), r_int + 2, [brightness * 0.35] * 3, -1, lineType=cv2.LINE_AA)
        
        # Soft diffusion
        blurred = cv2.GaussianBlur(canvas, (3, 3), 0.8)
        final = np.clip(canvas * 0.75 + blurred * 0.45, 0, 255).astype(np.uint8)
        yield final


def generate_cinematic_rain():
    """Generates 450 cinematic rain streaks with dynamic wind slant, droplet splash ripples and subtle lightning illumination pulses."""
    np.random.seed(77)
    n_streaks = 450
    
    x0 = np.random.uniform(0, WIDTH, n_streaks)
    y0 = np.random.uniform(0, HEIGHT, n_streaks)
    depth = np.random.uniform(0.2, 1.0, n_streaks)
    slant_dx = np.random.uniform(12, 28, n_streaks)
    length = np.random.uniform(25, 65, n_streaks) * depth
    k_y = np.random.choice([14, 16, 18, 20, 22, 24], n_streaks)
    
    for f in range(TOTAL_FRAMES):
        t = f / TOTAL_FRAMES
        theta = 2 * math.pi * t
        
        lightning = 0.0
        if 42 <= f <= 44:
            lightning = 35.0 * (1.0 - abs(f - 43) * 0.5)
        elif 165 <= f <= 167:
            lightning = 45.0 * (1.0 - abs(f - 166) * 0.5)
            
        canvas = np.zeros((HEIGHT, WIDTH, 3), dtype=np.float32)
        if lightning > 0:
            canvas[:] = [lightning * 0.9, lightning * 0.95, lightning]
            
        for i in range(n_streaks):
            curr_y = (y0[i] + k_y[i] * HEIGHT * t) % HEIGHT
            curr_x = (x0[i] + slant_dx[i] * math.sin(theta) + (curr_y / HEIGHT) * slant_dx[i]) % WIDTH
            
            x1 = int(round(curr_x))
            y1 = int(round(curr_y))
            x2 = int(round(curr_x + slant_dx[i] * 0.35))
            y2 = int(round(curr_y + length[i]))
            
            alpha = depth[i] * 0.85
            color = [alpha * 240, alpha * 225, alpha * 210]
            thick = 1 if depth[i] < 0.75 else 2
            
            cv2.line(canvas, (x1, y1), (x2, y2), color, thick, lineType=cv2.LINE_AA)
            
            if curr_y > HEIGHT * 0.82 and depth[i] > 0.6:
                splash_r = int(depth[i] * 4.0)
                splash_alpha = alpha * 0.5
                cv2.ellipse(canvas, (x2, min(HEIGHT - 2, y2)), (splash_r, max(1, splash_r // 2)), 0, 0, 360,
                            [splash_alpha * 240, splash_alpha * 225, splash_alpha * 210], 1, lineType=cv2.LINE_AA)
                            
        blurred = cv2.GaussianBlur(canvas, (3, 3), 0.7)
        final = np.clip(canvas * 0.85 + blurred * 0.35, 0, 255).astype(np.uint8)
        yield final


def generate_fire_embers():
    """Generates 160 rising turbulent fire embers and glowing sparks with heat shimmer."""
    np.random.seed(105)
    n_embers = 160
    
    x0 = np.random.uniform(0, WIDTH, n_embers)
    y0 = np.random.uniform(0, HEIGHT, n_embers)
    depth = np.random.uniform(0.2, 1.0, n_embers)
    k_y = np.random.choice([2, 3, 4, 5], n_embers)
    m_x = np.random.choice([2, 3, 4, 5], n_embers)
    phi_x = np.random.uniform(0, 2 * math.pi, n_embers)
    drift_amp = np.random.uniform(25, 75, n_embers) * depth
    
    flicker_k = np.random.choice([4, 6, 8, 10], n_embers)
    flicker_phi = np.random.uniform(0, 2 * math.pi, n_embers)
    color_cat = np.random.choice([0, 1, 2], n_embers, p=[0.35, 0.50, 0.15])
    
    for f in range(TOTAL_FRAMES):
        t = f / TOTAL_FRAMES
        theta = 2 * math.pi * t
        
        canvas = np.zeros((HEIGHT, WIDTH, 3), dtype=np.float32)
        
        for i in range(n_embers):
            curr_y = (y0[i] - k_y[i] * HEIGHT * t) % HEIGHT
            curr_x = (x0[i] + drift_amp[i] * math.sin(m_x[i] * theta + phi_x[i])) % WIDTH
            
            flicker = 0.7 + 0.3 * math.cos(flicker_k[i] * theta + flicker_phi[i])
            height_fade = 0.4 + 0.6 * (curr_y / HEIGHT)
            alpha = depth[i] * flicker * height_fade
            
            radius = 1.0 + depth[i] * 3.8
            r_int = max(1, int(math.ceil(radius)))
            
            if color_cat[i] == 0:
                color = np.array([50, 210, 255], dtype=np.float32) * alpha
            elif color_cat[i] == 1:
                color = np.array([20, 130, 255], dtype=np.float32) * alpha
            else:
                color = np.array([20, 50, 240], dtype=np.float32) * alpha
                
            ix, iy = int(round(curr_x)), int(round(curr_y))
            cv2.circle(canvas, (ix, iy), r_int, color.tolist(), -1, lineType=cv2.LINE_AA)
            
            if depth[i] > 0.55:
                halo_color = color * 0.45
                cv2.circle(canvas, (ix, iy), r_int * 2 + 2, halo_color.tolist(), -1, lineType=cv2.LINE_AA)
                
        blurred = cv2.GaussianBlur(canvas, (7, 7), 1.8)
        final = np.clip(canvas * 0.75 + blurred * 0.65, 0, 255).astype(np.uint8)
        yield final


def generate_vintage_film():
    """Generates classic 8mm/16mm film scratches, hair/dust particles, jitter and warm vignette."""
    np.random.seed(99)
    scratch_x = np.random.uniform(WIDTH * 0.15, WIDTH * 0.85, 4)
    scratch_active = np.random.choice([0, 1], (4, TOTAL_FRAMES), p=[0.4, 0.6])
    
    y_coords, x_coords = np.ogrid[:HEIGHT, :WIDTH]
    cx, cy = WIDTH / 2, HEIGHT / 2
    dist_from_center = np.sqrt((x_coords - cx)**2 + (y_coords - cy)**2)
    max_dist = math.sqrt(cx**2 + cy**2)
    vignette = (dist_from_center / max_dist) ** 2.2
    
    for f in range(TOTAL_FRAMES):
        np.random.seed((f * 37) % 5000)
        noise = np.random.normal(0, 14, (HEIGHT, WIDTH)).astype(np.float32)
        
        canvas = np.zeros((HEIGHT, WIDTH, 3), dtype=np.float32)
        canvas[:, :, 0] = np.clip(noise * 0.6, 0, 255)
        canvas[:, :, 1] = np.clip(noise * 0.85 + 4, 0, 255)
        canvas[:, :, 2] = np.clip(noise * 1.1 + 8, 0, 255)
        
        v_pulse = 0.35 + 0.08 * math.sin(f * 0.2)
        canvas[:, :, 0] += vignette * v_pulse * 15
        canvas[:, :, 1] += vignette * v_pulse * 25
        canvas[:, :, 2] += vignette * v_pulse * 35
        
        for s in range(4):
            if scratch_active[s, f]:
                sx = int(scratch_x[s] + np.random.uniform(-1.5, 1.5))
                sx = max(0, min(WIDTH - 1, sx))
                scratch_bright = np.random.uniform(90, 190)
                cv2.line(canvas, (sx, 0), (sx, HEIGHT), [scratch_bright * 0.8, scratch_bright * 0.9, scratch_bright], 1)
                
        n_specks = np.random.randint(2, 6)
        for _ in range(n_specks):
            sp_x = np.random.randint(0, WIDTH)
            sp_y = np.random.randint(0, HEIGHT)
            sp_r = np.random.choice([1, 2])
            sp_col = np.random.uniform(120, 230)
            cv2.circle(canvas, (sp_x, sp_y), sp_r, [sp_col * 0.8, sp_col * 0.9, sp_col], -1)
            
        final = np.clip(canvas, 0, 255).astype(np.uint8)
        yield final


def generate_sun_rays():
    """Generates soft diagonal volumetric sunbeams and golden light leaks."""
    np.random.seed(63)
    n_rays = 6
    ray_angles = np.linspace(-math.pi * 0.28, -math.pi * 0.15, n_rays)
    widths = [80, 120, 160, 110, 140, 90]
    
    for f in range(TOTAL_FRAMES):
        t = f / TOTAL_FRAMES
        theta = 2 * math.pi * t
        
        canvas = np.zeros((HEIGHT, WIDTH), dtype=np.float32)
        origin_x = -50 + 40 * math.sin(theta)
        origin_y = -30 + 30 * math.cos(theta)
        
        for i in range(n_rays):
            angle = ray_angles[i] + 0.03 * math.sin(theta + i)
            ray_len = 1600
            w = widths[i] * (1.0 + 0.2 * math.sin(theta * 2 + i * 1.5))
            
            dx = math.cos(angle)
            dy = -math.sin(angle)
            nx = -dy
            ny = dx
            
            p1 = (int(origin_x - nx * (w * 0.2)), int(origin_y - ny * (w * 0.2)))
            p2 = (int(origin_x + nx * (w * 0.2)), int(origin_y + ny * (w * 0.2)))
            p3 = (int(origin_x + dx * ray_len + nx * w), int(origin_y + dy * ray_len + ny * w))
            p4 = (int(origin_x + dx * ray_len - nx * w), int(origin_y + dy * ray_len - ny * w))
            
            pts = np.array([p1, p2, p3, p4], dtype=np.int32)
            ray_intensity = 55.0 + 25.0 * math.cos(theta + i * 0.8)
            cv2.fillPoly(canvas, [pts], float(ray_intensity))
            
        blurred = cv2.GaussianBlur(canvas, (121, 121), 60.0)
        b = (blurred * 0.55).astype(np.uint8)
        g = (blurred * 0.85).astype(np.uint8)
        r = (blurred * 1.05).clip(0, 255).astype(np.uint8)
        
        frame = cv2.merge([b, g, r])
        yield frame


def main():
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    print("--- GENERATING SEAMLESS ATMOSPHERIC OVERLAYS ---")
    
    dust_path = ASSETS_DIR / "dust_particles.mp4"
    if not dust_path.exists():
        print("1/7 Rendering Cinematic Dust Particles...")
        encode_frames_to_mp4(generate_dust_particles, dust_path)
    
    smoke_path = ASSETS_DIR / "cinematic_smoke.mp4"
    if not smoke_path.exists():
        print("2/7 Rendering Cinematic Smoke & Fog...")
        encode_frames_to_mp4(generate_cinematic_smoke, smoke_path)
    
    snow_path = ASSETS_DIR / "falling_snow.mp4"
    if not snow_path.exists():
        print("3/7 Rendering Falling Snow...")
        encode_frames_to_mp4(generate_falling_snow, snow_path)
        
    rain_path = ASSETS_DIR / "cinematic_rain.mp4"
    print("4/7 Rendering Cinematic Rain & Storm...")
    encode_frames_to_mp4(generate_cinematic_rain, rain_path)
    
    embers_path = ASSETS_DIR / "fire_embers.mp4"
    print("5/7 Rendering Fire Embers & Sparks...")
    encode_frames_to_mp4(generate_fire_embers, embers_path)
    
    vintage_path = ASSETS_DIR / "vintage_film.mp4"
    print("6/7 Rendering Vintage Film Grain & Scratches...")
    encode_frames_to_mp4(generate_vintage_film, vintage_path)
    
    sun_path = ASSETS_DIR / "sun_rays.mp4"
    print("7/7 Rendering Sun Rays & Light Leaks...")
    encode_frames_to_mp4(generate_sun_rays, sun_path)
    
    print("--- ALL OVERLAYS GENERATED SUCCESSFULLY! ---")


if __name__ == "__main__":
    main()
