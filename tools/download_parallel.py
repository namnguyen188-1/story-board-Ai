from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.request import Request, urlopen
import sys, time, shutil, os

url = sys.argv[1]
output = Path(sys.argv[2])
total = int(sys.argv[3])
workers = 16
chunk_size = 2 * 1024 * 1024
parts_dir = Path(str(output) + ".parts")
parts_dir.mkdir(parents=True, exist_ok=True)
count = (total + chunk_size - 1) // chunk_size
done_bytes = sum(p.stat().st_size for p in parts_dir.glob("*.part") if p.is_file())
print(f"Parallel resume download: {total} bytes, {workers} workers, {count} chunks; already cached {done_bytes}.", flush=True)

def fetch(i):
    start = i * chunk_size
    end = min(total - 1, start + chunk_size - 1)
    expected = end - start + 1
    part = parts_dir / f"{i:04d}.part"
    if part.exists() and part.stat().st_size > expected:
        part.unlink()
    offset = part.stat().st_size if part.exists() else 0
    if offset == expected:
        return i, expected, "cached"
    for attempt in range(1, 7):
        try:
            req = Request(url, headers={"Range": f"bytes={start + offset}-{end}"})
            with urlopen(req, timeout=120) as response:
                if response.status != 206:
                    raise RuntimeError(f"chunk {i}: expected HTTP 206, got {response.status}")
                content_range = response.headers.get("Content-Range", "")
                if not content_range.startswith(f"bytes {start + offset}-"):
                    raise RuntimeError(f"chunk {i}: unexpected Content-Range {content_range!r}")
                with part.open("ab" if offset else "wb") as f:
                    while True:
                        buf = response.read(1024 * 1024)
                        if not buf:
                            break
                        f.write(buf)
                        f.flush()
                        offset += len(buf)
            if offset != expected:
                raise RuntimeError(f"chunk {i}: received {offset}/{expected} bytes")
            return i, expected, "downloaded"
        except Exception as exc:
            print(f"chunk {i} retry {attempt}/6 at byte {offset}/{expected}: {exc}", flush=True)
            if attempt == 6:
                raise
            time.sleep(min(attempt * 2, 10))
    raise RuntimeError(f"chunk {i} failed")

completed = 0
with ThreadPoolExecutor(max_workers=workers) as pool:
    futures = [pool.submit(fetch, i) for i in range(count)]
    for future in as_completed(futures):
        i, n, state = future.result()
        completed += n
        print(f"chunk {i+1}/{count} {state}; confirmed chunks {completed}/{total} bytes", flush=True)

tmp = Path(str(output) + ".assembling")
with tmp.open("wb") as out:
    for i in range(count):
        part = parts_dir / f"{i:04d}.part"
        if not part.is_file():
            raise RuntimeError(f"missing chunk {i}")
        with part.open("rb") as src:
            shutil.copyfileobj(src, out, 1024 * 1024)
if tmp.stat().st_size != total:
    raise RuntimeError(f"assembled size mismatch: {tmp.stat().st_size}/{total}")
os.replace(tmp, output)
shutil.rmtree(parts_dir, ignore_errors=True)
print(f"DOWNLOAD_PASS path={output} bytes={output.stat().st_size}", flush=True)