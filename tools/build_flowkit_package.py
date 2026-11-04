import os
import sys
import zipfile
import time

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def build_flowkit_zip():
    src_dir = "D:/FLOWKIT"
    out_zip = "D:/STORYBOARD_AI/FlowKit_Engine_Standalone.zip"

    exclude_dirs = {"outputs", "__pycache__", ".git"}
    exclude_files = {".DS_Store"}

    start_time = time.time()
    print(f"Bắt đầu đóng gói FlowKit Engine từ {src_dir} vào {out_zip}...", flush=True)

    file_count = 0
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for root, dirs, files in os.walk(src_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for f in files:
                if f in exclude_files or f.endswith(".log") or f.endswith(".tmp"):
                    continue
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, src_dir)
                # archive inside a root FLOWKIT folder so extracting it unpacks directly as FLOWKIT
                arcname = os.path.join("FLOWKIT", rel_path)
                zf.write(full_path, arcname)
                file_count += 1
                if file_count % 1000 == 0:
                    print(f"Đã nén {file_count} files...", flush=True)

    elapsed = time.time() - start_time
    zip_size = os.path.getsize(out_zip) / (1024 * 1024)
    print(f"HOÀN TẤT: Đã đóng gói {file_count} files trong {elapsed:.1f}s. Dung lượng file zip: {zip_size:.2f} MB", flush=True)
    return out_zip

if __name__ == "__main__":
    build_flowkit_zip()
