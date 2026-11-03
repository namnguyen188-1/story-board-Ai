from pathlib import Path
import subprocess,hashlib,json
root=Path(r"D:\STORYBOARD_AI")
rel="studio/runtime/muse/python/python312._pth"
value="Lib\nDLLs\nLib/site-packages\n.\n../../..\nimport site\n"
for base in (root,root/"dist/Storyboard_AI_Studio_Pro_v1.3.6",root/"dist/Muse_Runtime_Repair_v1.3.6"):
 (base/rel).write_text(value,encoding="ascii")
 if base!=root:
  subprocess.run([r"C:\Program Files\7-Zip\7z.exe","a","-tzip",str(base)+".zip",rel],cwd=base,check=True,capture_output=True)
p=root/"tools/build_muse_runtime.py";s=p.read_text(encoding="utf-8");s=s.replace(r"Lib/site-packages\n.\nimport site",r"Lib/site-packages\n.\n../../..\nimport site");p.write_text(s,encoding="utf-8")
subprocess.run([str(root/"studio/runtime/muse/python/python.exe"),"-I","-c","import muse_accounts,muse_gateway_worker,muse_login,muse_cli.cli,muse_cli.gateway,av;print('PORTABLE_APP_BRIDGE_IMPORT_OK')"],check=True)
repair=root/"dist/Muse_Runtime_Repair_v1.3.6.zip"
print(json.dumps({"repair_bytes":repair.stat().st_size,"repair_sha256":hashlib.file_digest(repair.open("rb"),"sha256").hexdigest().upper()}),flush=True)
