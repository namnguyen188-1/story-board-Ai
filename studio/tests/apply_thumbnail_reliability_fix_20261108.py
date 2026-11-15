from pathlib import Path
import shutil,subprocess,json,hashlib,datetime
root=Path(r"D:\STORYBOARD_AI\studio")
p=root/"seo_packager.py"
stamp=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
backup_dir=root/"runtime"/("thumbnail_reliability_fix_"+stamp)
backup_dir.mkdir(parents=True,exist_ok=False)
backup=backup_dir/"seo_packager.py.original"
original=p.read_bytes()
backup.write_bytes(original)
text=original.decode("utf-8-sig").replace("\r\n", "\n")
def replace_one(src,old,new,tag):
 if src.count(old)!=1:
  raise RuntimeError(f"EXACT_PATCH_MISMATCH_{tag}: {src.count(old)}")
 return src.replace(old,new,1)
try:
 text=replace_one(text,
  '    is_short = (aspect_ratio == "9:16") or is_vertical_short_episode(ep_dir)',
  '    # Explicit target ratio always overrides an episode-wide Shorts hint.\n    is_short = (aspect_ratio == "9:16") if aspect_ratio in {"9:16", "16:9"} else is_vertical_short_episode(ep_dir)',"ratio")
 beg=text.index('    is_valid_cache = not force_regenerate and out_thumb.is_file()')
 end=text.index('    if is_valid_cache:\n',beg)
 old=text[beg:end]
 new='''    is_valid_cache = not force_regenerate and out_thumb.is_file() and out_thumb.stat().st_size > 5000
    if is_valid_cache:
        try:
            from PIL import Image
            with Image.open(out_thumb) as chk:
                chk.verify()
            with Image.open(out_thumb) as chk:
                actual_ratio = chk.width / max(1, chk.height)
                expected_ratio = (9 / 16) if is_short else (16 / 9)
                is_valid_cache = (chk.format == "JPEG" and
                                  chk.width >= 256 and chk.height >= 256 and
                                  abs(actual_ratio - expected_ratio) < 0.035 and
                                  out_thumb.stat().st_size <= 2_000_000)
        except Exception:
            is_valid_cache = False
'''
 text=text[:beg]+new+text[end:]
 text=replace_one(text,'    out_base = ep_dir / "thumbnail_flow_base.jpg"', '    out_base = ep_dir / "thumbnail_flow_base.png"',"base_png")
 beg=text.index('    # Step D: Save Final Thumbnail directly')
 end=text.index('    # Step E: Re-organize Episode for YouTube Publish Folder',beg)
 new='''    # Step D: Write a real, decodable JPEG with a matching extension and ratio.
    # Never copy a PNG byte stream into a .jpg path. Keep existing thumbnail until verified.
    out_thumb = ep_dir / ("thumbnail_shorts.jpg" if is_short else "thumbnail_seo.jpg")
    tmp_thumb = out_thumb.with_name(out_thumb.stem + ".partial.jpg")
    try:
        from PIL import Image, ImageOps
        with Image.open(out_base) as source:
            source.load()
            image = source.convert("RGB")
            target_size = (1080, 1920) if is_short else (1536, 864)
            if abs(image.width / max(1, image.height) - target_size[0] / target_size[1]) > 0.035:
                image = ImageOps.fit(image, target_size, method=Image.Resampling.LANCZOS)
            else:
                image = image.resize(target_size, Image.Resampling.LANCZOS)
            for quality in (92, 88, 84, 78, 72):
                image.save(tmp_thumb, format="JPEG", quality=quality,
                           optimize=True, subsampling=0)
                if tmp_thumb.stat().st_size <= 2_000_000:
                    break
            else:
                raise RuntimeError("THUMBNAIL_JPEG_EXCEEDS_2MB")
        with Image.open(tmp_thumb) as verify_img:
            verify_img.verify()
        with Image.open(tmp_thumb) as verify_img:
            if verify_img.format != "JPEG" or verify_img.size != target_size:
                raise RuntimeError("THUMBNAIL_JPEG_DECODE_OR_DIMENSIONS_FAILED")
        tmp_thumb.replace(out_thumb)
        print(f"[FLOW_THUMBNAIL] Verified JPEG {target_size} ({out_thumb.stat().st_size} bytes): {out_thumb}", flush=True)
    except Exception as exc:
        tmp_thumb.unlink(missing_ok=True)
        return {"ok": False, "error": f"THUMBNAIL_OUTPUT_VERIFICATION_FAILED: {exc}",
                "backend": backend_used or "mcp_v2",
                "aspect_ratio": target_ratio, "is_short": is_short}

'''
 text=text[:beg]+new+text[end:]
 temp=p.with_name(p.name+".thumb-tmp")
 temp.write_bytes(text.replace("\n", "\r\n").encode("utf8"))
 temp.replace(p)
 tests=["test_thumbnail_qa_20261108.py","test_flowkit_removed_offline.py",
        "test_single_lane_no_resubmit_20261108.py"]
 results={}
 for t in tests:
  args=[str(root/"runtime/python/python.exe"),"-B","-X","utf8",str(root/"tests"/t)]
  r=subprocess.run(args,cwd=root,capture_output=True,text=True,encoding="utf8",errors="replace",timeout=90)
  results[t]={"returncode":r.returncode,"log_tail":(r.stdout+r.stderr)[-2500:]}
  print(t,r.returncode,(r.stdout+r.stderr)[-1000:])
  if r.returncode:raise RuntimeError("REGRESSION_FAILED_"+t)
 report={"result":"PATCH_AND_TESTS_PASS","backup":str(backup),"source":str(p),
         "before_sha256":hashlib.sha256(original).hexdigest(),
         "after_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"results":results}
 (backup_dir/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
 print("REPORT",str(backup_dir/"report.json"))
except Exception as exc:
 p.write_bytes(original)
 print("ROLLED_BACK",type(exc).__name__,str(exc))
 raise
