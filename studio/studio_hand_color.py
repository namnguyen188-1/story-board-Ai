"""Streaming local hand-drawing reveal of the complete original color image."""
from pathlib import Path
import math, os, subprocess, tempfile, wave
import cv2
import numpy as np
from PIL import Image, ImageOps

def _hand(height):
    assets=Path(__file__).resolve().parent/"engine"/"assets"
    image=cv2.imread(str(assets/"drawing-hand.png"))
    mask=cv2.imread(str(assets/"hand-mask.png"),cv2.IMREAD_GRAYSCALE)
    if image is None or mask is None or mask.shape!=image.shape[:2]:
        raise RuntimeError("Drawing hand assets missing or invalid")
    scale=height*.65/image.shape[0]
    size=(max(1,round(image.shape[1]*scale)),max(1,round(image.shape[0]*scale)))
    image=cv2.resize(image,size,interpolation=cv2.INTER_AREA)
    alpha=cv2.resize(mask,size,interpolation=cv2.INTER_AREA).astype(np.float32)/255
    # Marker tip in the original bundled hand; anchor the reveal to this tip.
    return image,alpha,round(35*scale),round(18*scale)

def _overlay(frame,hand,x,y):
    image,alpha,tip_x,tip_y=hand
    left,top=int(x)-tip_x,int(y)-tip_y
    h,w=frame.shape[:2]; hh,hw=image.shape[:2]
    x0,y0=max(0,left),max(0,top)
    x1,y1=min(w,left+hw),min(h,top+hh)
    if x0>=x1 or y0>=y1:return
    sx,sy=x0-left,y0-top
    a=alpha[sy:sy+y1-y0,sx:sx+x1-x0,None]
    frame[y0:y1,x0:x1]=(frame[y0:y1,x0:x1]*(1-a)+
        image[sy:sy+y1-y0,sx:sx+x1-x0]*a).astype(np.uint8)

def iter_color_frames(source,total_frames,hold_frames=25):
    """True hand-drawn outlines, region-by-region coloring, exact final image."""
    from studio_hand_color_strokes import iter_stroke_color_frames
    yield from iter_stroke_color_frames(
        source, total_frames, hold_frames, _hand, _overlay)


def hand_color_video(image,audio,output,width,height,fps=25):
    """Write H.264 with drawing timing derived from the supplied WAV."""
    if width<=0 or height<=0 or width%2 or height%2 or fps<=0:
        raise ValueError("Video dimensions must be positive even integers")
    output=Path(output); output.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(audio),"rb") as w:
        seconds=w.getnframes()/max(1,w.getframerate())
    total=max(3,math.ceil(seconds*fps))
    with Image.open(image) as original:
        source=np.asarray(ImageOps.pad(original.convert("RGB"),(width,height),
            method=Image.Resampling.LANCZOS,color="white"))[:,:,::-1].copy()
    fd,temp=tempfile.mkstemp(suffix=".mp4",prefix="hand_color_",dir=output.parent)
    os.close(fd)
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-y","-f","rawvideo",
         "-pix_fmt","bgr24","-s",str(width)+"x"+str(height),"-r",str(fps),
         "-i","pipe:0","-an","-c:v","libx264","-preset","veryfast","-crf","20",
         "-pix_fmt","yuv420p","-movflags","+faststart",temp]
    process=None
    try:
        with tempfile.TemporaryFile() as errors:
            process=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=errors, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            try:
                for frame in iter_color_frames(source,total,max(1,round(min(1.5,seconds*.18)*fps))):
                    process.stdin.write(frame.tobytes())
                process.stdin.close()
                code=process.wait(timeout=120)
            except BaseException:
                process.kill();process.wait()
                raise
            if code:
                errors.seek(0)
                raise RuntimeError("Hand-color encode failed: "+errors.read().decode(errors="replace")[-500:])
        cap=cv2.VideoCapture(temp)
        try:
            valid=cap.isOpened() and int(cap.get(cv2.CAP_PROP_FRAME_COUNT))==total
        finally:cap.release()
        if not valid:raise RuntimeError("Hand-color MP4 verification failed")
        os.replace(temp,output)
    finally:
        if Path(temp).exists():Path(temp).unlink()
    return str(output)
