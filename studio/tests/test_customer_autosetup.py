"""Release-candidate bootstrap safety/portability tests; no real GPU downloads."""
import unittest,tempfile,sys,os,hashlib,json
from pathlib import Path
ROOT=Path(r"D:\STORYBOARD_AI\dist\Storyboard_AI_Studio_Pro_Transfer_Test_20261015\studio")
sys.path.insert(0,str(ROOT))
import customer_bootstrap as b

class CustomerBootstrapTests(unittest.TestCase):
    def test_core(self):
        info=b.report_core()
        self.assertTrue(info["ready"],info)
    def test_detect_local(self):
        self.assertEqual(b.local_report()["vendor"],"nvidia")
    def test_official_manifest(self):
        raw={"tag_name":"v1.0","assets":[{"name":"ComfyUI_windows_portable_nvidia.7z",
            "size":800_000_000,"browser_download_url":
            "https://github.com/Comfy-Org/ComfyUI/releases/download/v1.0/ComfyUI_windows_portable_nvidia.7z",
            "digest":"sha256:"+"1"*64}]}
        row=b.release_asset(raw,"nvidia")
        self.assertEqual(row["digest"],"1"*64)
        for vendor in ("amd","intel"):
            self.assertRaises(ValueError,b.release_asset,raw,vendor)
    def test_sha_required(self):
        raw={"tag_name":"v1.0","assets":[{"name":"ComfyUI_windows_portable_nvidia.7z",
            "size":800_000_000,"browser_download_url":
            "https://github.com/Comfy-Org/ComfyUI/releases/download/v1.0/ComfyUI_windows_portable_nvidia.7z",
            "digest":""}]}
        self.assertRaisesRegex(ValueError,"SHA256",b.release_asset,raw,"nvidia")
    def test_untrusted_host_rejected(self):
        raw={"assets":[{"name":"ComfyUI_windows_portable_nvidia.7z",
            "size":800_000_000,"browser_download_url":
            "https://evil.example/Comfy-Org/ComfyUI/releases/download/v1/ComfyUI_windows_portable_nvidia.7z",
            "digest":"sha256:"+"2"*64}]}
        self.assertRaises(ValueError,b.release_asset,raw,"nvidia")
    def test_checksum_file_and_resume(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/"src.bin";src.write_bytes(b"portable" * 1200)
            dest=Path(d)/"dst.bin"
            h=hashlib.sha256(src.read_bytes()).hexdigest()
            b.download_checked(src.as_uri(),dest,src.stat().st_size,h)
            self.assertEqual(dest.read_bytes(),src.read_bytes())
            b.download_checked(src.as_uri(),dest,src.stat().st_size,h)
            self.assertRaises(RuntimeError,b.download_checked,src.as_uri(),Path(d)/"bad.bin",src.stat().st_size,"0"*64)
    def test_no_auto_api(self):
        code=(ROOT/"customer_bootstrap.py").read_text(encoding="utf-8")
        self.assertNotIn("TUANSU_API_KEY",code)
        self.assertNotIn("GEMINI_API_KEY",code)
    def test_portable_ready_modules(self):
        from comfyui_image_provider import build_workflow
        job=build_workflow("forest","none","sd_xl_base_1.0.safetensors",640,360)
        self.assertGreaterEqual(job["3"]["inputs"]["steps"],20)
        self.assertGreater(job["3"]["inputs"]["cfg"],5)
    def test_no_system_python_install(self):
        code=(ROOT.parent/"customer_setup_wizard.cs").read_text(encoding="utf-8")
        self.assertIn("check-core",code)
        self.assertIn("install-local",code)
        self.assertIn("install-local",code)
        self.assertNotIn("python.org/ftp",code)

if __name__=="__main__":
    unittest.main(verbosity=2)
