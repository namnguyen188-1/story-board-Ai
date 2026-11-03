"""Gateway worker contracts against a local fake service; never contacts Muse."""
import base64, importlib.util, io, json, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

class GatewayWorkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.worker_path=Path(__file__).resolve().parents[1]/"muse_gateway_worker.py"

    def worker(self):
        self.assertTrue(self.worker_path.is_file(),"Saved-session gateway worker is not implemented")
        import muse_gateway_worker
        return muse_gateway_worker

    def media(self):
        import av
        from PIL import Image
        img=io.BytesIO();Image.new("RGB",(160,90),"navy").save(img,format="PNG")
        video=io.BytesIO()
        with av.open(video,mode="w",format="mp4") as c:
            st=c.add_stream("libx264",rate=24);st.width=160;st.height=90;st.pix_fmt="yuv420p"
            for _ in range(24):
                frame=av.VideoFrame.from_image(Image.new("RGB",(160,90),"navy"))
                for packet in st.encode(frame):c.mux(packet)
            for packet in st.encode():c.mux(packet)
        return img.getvalue(),video.getvalue()

    def fake(self, w, image, video):
        class Service:
            def __init__(self):
                self.submissions=0;self.accepted=False;self.completed=True;self.reads=[];self.pathmap={}
            def submit(self,sid,prompt,tag):
                self.submissions+=1;self.accepted=True;self.tag=tag
                self.ip="workspace/test/"+tag+"_image.png";self.vp="workspace/test/"+tag+"_video.mp4"
                self.pathmap={self.ip:image,self.vp:video}
                return True
            def call(self,method,body=None):
                body=body or {}
                if method=="session.start":return {"session_id":"test-session"}
                if method=="sessions.list":return {"sessions":[{"session_id":"test-session","status":"completed" if self.completed else "running"}]}
                if method=="chat.history":
                    events=[]
                    if self.accepted:events.append({"seq":1,"event_name":"message.user","payload":{"display_text":self.tag}})
                    if self.accepted and self.completed:events.append({"seq":2,"event_name":"message.assistant","payload":{"display_text":json.dumps({"image_path":"/"+self.ip,"video_path":"/"+self.vp})}})
                    return {"chat_events":events}
                if method=="fs.stat":return {"kind":"file","size":len(self.pathmap[body["path"]]),"modified_ms":123}
                if method=="fs.read":
                    self.reads.append((body["path"],body["offset"]))
                    raw=self.pathmap[body["path"]];off=body["offset"];part=raw[off:off+body["len"]]
                    return {"path":body["path"],"offset":off,"len":len(part),"eof":off+len(part)==len(raw),"data_base64":base64.b64encode(part).decode()}
                raise AssertionError(method)
            def close(self):pass
        return Service()

    def test_render_creates_real_image_and_video_without_user_reference(self):
        w=self.worker();image,video=self.media();api=self.fake(w,image,video)
        with tempfile.TemporaryDirectory() as td:
            request={"output_image_path":str(Path(td)/"image.png"),"prompt":"a blue cup","width":160,"height":90,"duration":1}
            result=w.run_render(request,api=api,submit=api.submit,poll_interval=.001,timeout=1)
            self.assertTrue((Path(td)/"muse_clip.mp4").is_file())
            self.assertEqual(result["video"]["video_frames_decoded"],24)
            self.assertEqual(result["image"]["width"],160)
            self.assertEqual(api.submissions,1)

    def test_render_creates_direct_text_to_video_and_extracts_poster_frame(self):
        w=self.worker();_,video=self.media()
        class PureVideoService:
            def __init__(self):
                self.submissions=0;self.accepted=False;self.completed=True;self.reads=[]
            def submit(self,sid,prompt,tag):
                self.submissions+=1;self.accepted=True;self.tag=tag
                self.vp='workspace/test/'+tag+'_video.mp4'
                self.pathmap={self.vp:video}
                return True
            def call(self,method,body=None):
                body=body or {}
                if method=='session.start':return {'session_id':'test-session'}
                if method=='sessions.list':return {'sessions':[{'session_id':'test-session','status':'completed'}]}
                if method=='chat.history':
                    events=[]
                    if self.accepted:events.append({'seq':1,'event_name':'message.user','payload':{'display_text':self.tag}})
                    if self.accepted and self.completed:events.append({'seq':2,'event_name':'message.assistant','payload':{'display_text':json.dumps({'video_path':'/'+self.vp})}})
                    return {'chat_events':events}
                if method=='fs.stat':return {'kind':'file','size':len(self.pathmap[body['path']]),'modified_ms':123}
                if method=='fs.read':
                    self.reads.append((body['path'],body['offset']))
                    raw=self.pathmap[body['path']];off=body['offset'];part=raw[off:off+body['len']]
                    return {'path':body['path'],'offset':off,'len':len(part),'eof':off+len(part)==len(raw),'data_base64':base64.b64encode(part).decode()}
                raise AssertionError(method)
            def close(self):pass
        api=PureVideoService()
        with tempfile.TemporaryDirectory() as td:
            request={'output_image_path':str(Path(td)/'image.png'),'prompt':'a blue cup','width':160,'height':90,'duration':1}
            result=w.run_render(request,api=api,submit=api.submit,poll_interval=.001,timeout=1)
            self.assertTrue((Path(td)/'muse_clip.mp4').is_file())
            self.assertTrue((Path(td)/'image.png').is_file())
            self.assertEqual(result['video']['video_frames_decoded'],24)
            self.assertEqual(result['image']['width'],160)
            self.assertEqual(result['image']['height'],90)
            self.assertEqual(api.submissions,1)

    def test_pending_job_resumes_without_second_submission(self):
        w=self.worker();image,video=self.media();api=self.fake(w,image,video);api.completed=False
        with tempfile.TemporaryDirectory() as td:
            req={"output_image_path":str(Path(td)/"image.png"),"prompt":"cup","width":160,"height":90,"duration":1}
            with self.assertRaisesRegex(RuntimeError,"MUSE_JOB_PENDING"):
                w.run_render(req,api=api,submit=api.submit,poll_interval=.001,timeout=.01)
            api.completed=True
            result=w.run_render(req,api=api,submit=api.submit,poll_interval=.001,timeout=1)
            self.assertTrue(result["ok"]);self.assertEqual(api.submissions,1)

    def test_completed_job_reuses_verified_files(self):
        w=self.worker();image,video=self.media();api=self.fake(w,image,video)
        with tempfile.TemporaryDirectory() as td:
            req={"output_image_path":str(Path(td)/"image.png"),"prompt":"cup","width":160,"height":90,"duration":1}
            a=w.run_render(req,api=api,submit=api.submit,poll_interval=.001,timeout=1)
            b=w.run_render(req,api=api,submit=api.submit,poll_interval=.001,timeout=1)
            self.assertEqual(a["video"]["sha256"],b["video"]["sha256"]);self.assertEqual(api.submissions,1)

    def test_changed_prompt_cannot_replace_pending_job(self):
        w=self.worker();image,video=self.media();api=self.fake(w,image,video);api.completed=False
        with tempfile.TemporaryDirectory() as td:
            req={"output_image_path":str(Path(td)/"image.png"),"prompt":"cup","width":160,"height":90,"duration":1}
            with self.assertRaisesRegex(RuntimeError,"MUSE_JOB_PENDING"):
                w.run_render(req,api=api,submit=api.submit,poll_interval=.001,timeout=.01)
            with self.assertRaisesRegex(RuntimeError,"MUSE_SCENE_INPUT_CHANGED"):
                w.run_render({**req,"prompt":"boat"},api=api,submit=api.submit,poll_interval=.001,timeout=1)
            self.assertEqual(api.submissions,1)

    def test_failed_remote_job_never_resubmits(self):
        w=self.worker();image,video=self.media();api=self.fake(w,image,video);api.completed=False
        original=api.call
        def fail(method,body=None):
            if method=="sessions.list":return {"sessions":[{"session_id":"test-session","status":"failed"}]}
            return original(method,body)
        api.call=fail
        with tempfile.TemporaryDirectory() as td:
            req={"output_image_path":str(Path(td)/"image.png"),"prompt":"cup","width":160,"height":90,"duration":1}
            for _ in range(2):
                with self.assertRaisesRegex(RuntimeError,"MUSE_REMOTE_FAILED"):
                    w.run_render(req,api=api,submit=api.submit,poll_interval=.001,timeout=1)
            self.assertEqual(api.submissions,1)

    def test_partial_download_continues_at_saved_offset(self):
        w=self.worker();image,video=self.media();api=self.fake(w,image,video);api.submit("s","","tag")
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/"clip.mp4";partial=target.with_suffix(".mp4.part")
            partial.write_bytes(video[:12])
            partial.with_suffix(".part.json").write_text(json.dumps({"path":api.vp,"size":len(video),"modified_ms":123}))
            meta=w.download(api,api.vp,target)
            self.assertEqual(api.reads[0][1],12);self.assertEqual(target.read_bytes(),video)
            self.assertEqual(meta["bytes"],len(video))

    def test_remote_path_cannot_escape_workspace(self):
        w=self.worker()
        for path in ("/etc/passwd","workspace/../secrets.mp4","https://other.test/a.mp4"):
            with self.assertRaises(ValueError):w.workspace_path(path)

    def test_persistent_lock_releases_after_exception(self):
        w=self.worker()
        with tempfile.TemporaryDirectory() as td:
            lock=Path(td)/"lock"
            with self.assertRaises(ValueError):
                with w.render_lock(lock,timeout=.01):raise ValueError("test")
            with w.render_lock(lock,timeout=.01):pass


    def test_media_prompt_uses_reduced_aspect_ratio(self):
        w=self.worker();image,video=self.media();api=self.fake(w,image,video)
        prompts=[]
        def submit(sid,prompt,tag):
            prompts.append(prompt)
            return api.submit(sid,prompt,tag)
        with tempfile.TemporaryDirectory() as td:
            req={"output_image_path":str(Path(td)/"image.png"),"prompt":"cup","width":160,"height":90,"duration":1}
            w.run_render(req,api=api,submit=submit,poll_interval=.001,timeout=1)
        self.assertIn("composition ratio 16:9",prompts[0])
        self.assertNotIn("composition ratio 160:90",prompts[0])

if __name__=="__main__":unittest.main()
