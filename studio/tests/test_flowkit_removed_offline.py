"""Offline routing regressions: all media/browser boundaries are replaced."""
import ast, importlib, json, os, sys, tempfile, types, unittest
from pathlib import Path
from unittest.mock import patch, Mock
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import mcp_v2_images as images
import mcp_v2_batch as batch
import flowkit_client as client
import flow_account_manager as manager

class RoutingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.source=self.root/"source.png"
        Image.new("RGB",(512,512),"blue").save(self.source)
        self.calls=[]
        owner=self
        class Backend:
            def __init__(self,root,**kw): owner.calls.append(("init",kw))
            def preflight(self): return {}
            def render_one_queue(self,specs):
                owner.calls.append(("render",specs))
                return {s["scene_id"]:{"path":str(owner.source)} for s in specs}
        self.Backend=Backend
        self.fk=types.ModuleType("flowkit_client")
        self.fk.is_flowkit_alive=Mock(return_value=True)
        self.fk.get_webtool_status=Mock(return_value={"connected":True})
        self.fk.ensure_flowkit_running=Mock(return_value=True)
        def bad_image(**kw):
            p=Path(kw["output_path"]);p.parent.mkdir(parents=True,exist_ok=True)
            Image.new("RGB",(512,512),"red").save(p,format="PNG")
        self.fk.generate_image=Mock(side_effect=bad_image)
        self.studio=types.ModuleType("studio");self.studio.flowkit_client=self.fk
        self.modpatch=patch.dict(sys.modules,{"studio":self.studio,"studio.flowkit_client":self.fk,"flowkit_client":self.fk})
        self.modpatch.start();self.addCleanup(self.modpatch.stop)
        self.env=patch.dict(os.environ,{},clear=False);self.env.start();self.addCleanup(self.env.stop)
    def test_cli_defaults_to_mcp_v2(self):
        import series_studio
        args=series_studio.parser().parse_args(["run","--prompt","An original blue sailboat story"])
        self.assertEqual(args.image_provider,"mcp_v2")
    def test_cli_refuses_removed_flowkit_provider(self):
        import series_studio
        with self.assertRaises(SystemExit):
            series_studio.parser().parse_args(["run","--prompt","An original blue sailboat story","--image-provider","flowkit"])
    def test_preflight_returns_native_backend_when_flowkit_is_alive(self):
        with patch.object(images,"account_tool_url",return_value="https://flow.google.com/project/test/tool/test"),patch.object(images,"active_account",return_value={}):
            klass,models=images.preflight()
        self.assertIsNotNone(klass)
        self.assertFalse(self.fk.is_flowkit_alive.called)
    def test_single_image_uses_native_receipt_and_preserves_ratio(self):
        out=self.root/"out.png"
        with patch.object(images,"preflight",return_value=(self.Backend,("pro","lite","2.1"))),patch.object(images,"PRODUCTION_ROOT",self.root):
            images.make_image("A blue sailboat on the calm ocean",out,series="offline",episode=1,scene=1,max_new_images=1,aspect_ratio="9:16")
        with Image.open(out) as im:
            self.assertEqual(im.size,(1080,1920));self.assertEqual(im.getpixel((0,0)),(0,0,255))
        self.assertEqual(len([x for x in self.calls if x[0]=="render"]),1)
        self.assertFalse(self.fk.generate_image.called)
    def test_batch_uses_one_native_queue(self):
        accountmod=types.ModuleType("studio_flow_accounts")
        accountmod.apply_worker_env=lambda:{"id":"offline","name":"offline","cdp_port":9461}
        scenes=[{"description":"A blue ocean sailboat scene "+str(i),"visual_setup":"wide shot"} for i in range(2)]
        with patch.dict(sys.modules,{"studio_flow_accounts":accountmod}),patch.object(batch,"preflight",return_value=(self.Backend,("pro","lite","2.1"))),patch.object(batch,"PRODUCTION_ROOT",self.root),patch.object(batch,"_clear_completed_flow_queue"):
            count=batch.generate_episode_images(scenes,{},series="offline",episode=1,episode_dir=self.root/"ep",max_new_images=2,backend_factory=self.Backend)
        self.assertEqual(count,2)
        self.assertEqual(len([x for x in self.calls if x[0]=="render"]),1)
        with Image.open(self.root/"ep/scenes/scene_0001/image.png") as im:self.assertEqual(im.getpixel((im.width//2,im.height//2)),(0,0,255))
        self.assertFalse(self.fk.generate_image.called)
    def test_disabled_client_does_not_launch_or_clean_job_history(self):
        with patch.object(client,"cleanup_stale_flowkit_jobs") as cleanup,patch.object(client,"is_flowkit_alive",return_value=True),patch.object(client.subprocess,"Popen") as launch:
            self.assertFalse(client.ensure_flowkit_running())
            cleanup.assert_not_called();launch.assert_not_called()
    def test_status_uses_native_auth_and_never_starts_flowkit(self):
        account={"id":"offline","name":"offline"}
        import studio_mcp.accounts as ac
        with patch.object(ac,"active_account",return_value=account),patch.object(ac,"load_accounts",return_value={"active":"offline","accounts":[account]}),patch.object(ac,"account_tool_url",return_value="url"),patch.object(ac,"connection_check",return_value={"connected":False,"logged_in":False}),patch.object(ac,"flow_auth_status",return_value={"authenticated":False}),patch.object(manager,"_sanitize_accounts_db"),patch.object(manager,"_set_chrome_visibility_win32"),patch.object(manager,"is_port_listening",return_value=False),patch.object(manager,"ACCOUNTS_DB_FILE",self.root/"none"):
            status=manager.get_ui_status()
        self.assertFalse(status["ready"]);self.assertEqual(status.get("provider"),"mcp_v2")
        self.assertFalse(self.fk.ensure_flowkit_running.called)
    def test_native_denial_propagates_without_fallback(self):
        class Denied(self.Backend):
            def render_one_queue(self,specs):raise RuntimeError("GOOGLE_UNUSUAL_ACTIVITY")
        with patch.object(images,"preflight",return_value=(Denied,("pro","lite","2.1"))),patch.object(images,"PRODUCTION_ROOT",self.root):
            with self.assertRaisesRegex(RuntimeError,"GOOGLE_UNUSUAL_ACTIVITY"):
                images.make_image("A blue sailboat on the calm ocean",self.root/"denied.png",series="offline",episode=1,scene=1,max_new_images=1)
        self.assertFalse((self.root/"denied.png").exists())
        self.assertFalse(self.fk.generate_image.called)
    def test_thumbnail_denial_does_not_call_alternate_backend(self):
        s=(ROOT/"seo_packager.py").read_text(encoding="utf-8-sig")
        tree=ast.parse(s);node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="generate_thumbnail_with_flow")
        g={"Path":Path,"json":json,"is_vertical_short_episode":lambda p:False}
        exec(compile("from __future__ import annotations\n"+ast.get_source_segment(s,node),str(ROOT/"seo_packager.py"),"exec"),g)
        profiles=types.ModuleType("seo_genre_profiles");profiles.normalize_genre_key=lambda g:"documentary"
        denied=Mock(side_effect=RuntimeError("GOOGLE_UNUSUAL_ACTIVITY"))
        fakeimages=types.ModuleType("mcp_v2_images");fakeimages.make_image=denied
        tuan=types.ModuleType("v2_tuanstor_image");tuan.is_ready=Mock(return_value=False)
        self.studio.v2_tuanstor_image=tuan
        with patch.dict(sys.modules,{"mcp_v2_images":fakeimages,"seo_genre_profiles":profiles,"v2_tuanstor_image":tuan}):
            result=g["generate_thumbnail_with_flow"](self.root,custom_prompt="A detailed blue ocean sailboat thumbnail")
        self.assertFalse(result["ok"]);self.assertIn("GOOGLE_UNUSUAL_ACTIVITY",result.get("error",""))
        self.assertFalse(tuan.is_ready.called);self.assertFalse(self.fk.generate_image.called)

if __name__=="__main__":unittest.main(verbosity=2)
