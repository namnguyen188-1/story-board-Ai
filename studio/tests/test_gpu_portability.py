"""Deterministic multi-GPU regressions (no GPU / paid API calls)."""
import sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import gpu_capabilities as gpu
import comfyui_image_provider as c

class MultiGpuTests(unittest.TestCase):
 def test_3060(self):
  d=gpu.detect_from_outputs("NVIDIA GeForce RTX 3060 Ti, 8192","")
  self.assertEqual(d["primary"]["vram_mb"],8192)
  self.assertEqual(d["primary"]["local_mode"],"cuda")
 def test_3050(self):
  d=gpu.detect_from_outputs("GeForce RTX 3050, 4096","")
  self.assertEqual(d["primary"]["local_mode"],"cuda_lowvram")
 def test_4090(self):
  d=gpu.detect_from_outputs("RTX 4090, 24564","")
  self.assertEqual(d["primary"]["vendor"],"nvidia")
 def test_amd(self):
  d=gpu.detect_from_outputs("",'[{"Name":"AMD Radeon RX 7800 XT","AdapterRAM":0}]')
  self.assertEqual(d["primary"]["local_mode"],"external_comfy_optional")
  self.assertFalse(d["local_gpu_candidate"])
 def test_intel(self):
  d=gpu.detect_from_outputs("",'{"Name":"Intel Arc A770","AdapterRAM":0}')
  self.assertEqual(d["primary"]["vendor"],"intel")
  self.assertFalse(d["local_gpu_candidate"])
 def test_integrated(self):
  d=gpu.detect_from_outputs("",'[{"Name":"Intel UHD Graphics 770","AdapterRAM":0}]')
  self.assertEqual(d["primary"]["recommendation"],"cloud_or_verified_external")
 def test_cpu_only(self):
  d=gpu.detect_from_outputs("","")
  self.assertEqual(d["primary"]["local_mode"],"cloud")
  self.assertTrue(d["cloud_available_by_gpu"])
 def test_false_vram_adapter(self):
  d=gpu.detect_from_outputs("",'{"Name":"AMD Radeon Graphics","AdapterRAM":4294967295}')
  self.assertIsNone(d["primary"]["vram_mb"])
 def test_ready_external_server_amd(self):
  d=gpu.detect_from_outputs("",'{"Name":"AMD Radeon RX 7600","AdapterRAM":0}')
  with patch.object(gpu,"detect_gpu",return_value=d),patch.object(c,"is_ready",return_value=True),patch.object(c,"is_installed",return_value=False):
   self.assertEqual(c.compatibility_status()["state"],"ready_server")
 def test_amd_unverified_local(self):
  d=gpu.detect_from_outputs("",'{"Name":"AMD Radeon RX 7600","AdapterRAM":0}')
  with patch.object(gpu,"detect_gpu",return_value=d),patch.object(c,"is_ready",return_value=False),patch.object(c,"is_installed",return_value=True):
   self.assertFalse(c.compatibility_status()["can_attempt_local"])
 def test_nvidia_installed(self):
  d=gpu.detect_from_outputs("RTX 3060, 12288","")
  with patch.object(gpu,"detect_gpu",return_value=d),patch.object(c,"is_ready",return_value=False),patch.object(c,"is_installed",return_value=True):
   self.assertTrue(c.compatibility_status()["can_attempt_local"])
 def test_gpu_missing_does_not_spawn_comfy(self):
  d=gpu.detect_from_outputs("","")
  with patch.object(gpu,"detect_gpu",return_value=d),patch.object(c,"is_ready",return_value=False),patch.object(c,"is_installed",return_value=False),patch.object(c.subprocess,"Popen") as pop:
   self.assertFalse(c.ensure_server(timeout=0.1))
   pop.assert_not_called()
 def test_comfy_path_env(self):
  # Current production code reads env at import, tested in a separate clean import.
  source=Path(c.__file__).read_text(encoding="utf-8")
  self.assertNotIn('COMFYUI_DIR = Path(r"D:\\ComfyUI")',source)
  self.assertIn("STORYBOARD_COMFYUI_DIR",source)
 def test_no_auto_paid_fallback(self):
  source=Path(c.__file__).read_text(encoding="utf-8")
  self.assertNotIn("mcp_v2_images import",source)
  self.assertNotIn("tuansuapi_provider import",source)

if __name__=="__main__":unittest.main(verbosity=2)
