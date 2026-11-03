from pathlib import Path
p=Path(r"D:\STORYBOARD_AI\studio\tests\test_muse_gateway_worker.py")
s=p.read_text(encoding="utf-8")
test='''
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

'''
assert "def test_media_prompt_uses_reduced_aspect_ratio" not in s
s=s.replace('if __name__=="__main__":unittest.main()',test+'if __name__=="__main__":unittest.main()')
p.write_text(s,encoding="utf-8")
