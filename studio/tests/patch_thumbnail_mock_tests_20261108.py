from pathlib import Path
root=Path(r'D:\STORYBOARD_AI\studio')
p=root/"tests/test_thumbnail_qa_20261108.py"
backup=root/"runtime/thumbnail_session_qa_20261108_184103/test_thumbnail_qa_20261108.py.original"
backup.write_bytes(p.read_bytes())
s=p.read_text(encoding="utf8")
anchor="  self.patch.start();self.addCleanup(self.patch.stop)\n"
addition='''  import studio_mcp.accounts as accounts
  import studio_mcp.production_tab as tabs
  import studio_mcp.transport as mcp
  import studio_mcp.image_backend as backend
  self.session_events=[]
  class FakeHealth:
   def __call__(self,action,**kwargs):
    assert action=="health"
    return {"native":True,"sdk_image":True,"image_capability":True,
            "capabilities":["addToQueue","startImageProduction"],
            "queue_items":[],"running":False}
  fake_tab="a"*32
  def make_target(*args):
   self.session_events.append("prepare")
   return fake_tab
  def close_target(*args):
   self.session_events.append("close")
   return {"ok":True}
  def abandon_target(*args):
   self.session_events.append("abandon")
   return {"ok":True}
  self.session_patches=[
   patch.object(accounts,"active_account",return_value={"id":"qa_account"}),
   patch.object(accounts,"account_tool_url",return_value="https://flow.google.com/project/example/tool/example"),
   patch.object(tabs,"prepare",side_effect=make_target),
   patch.object(tabs,"close_completed",side_effect=close_target),
   patch.object(tabs,"abandon_fresh",side_effect=abandon_target),
   patch.object(mcp,"LocalFlowMcpTransport",return_value=object()),
   patch.object(backend,"StoryboardImageTransport",return_value=FakeHealth()),
  ]
  for obj in self.session_patches:
   obj.start();self.addCleanup(obj.stop)
'''
assert s.count(anchor)==1
s=s.replace(anchor,anchor+addition,1)
anchor=' def test_denial_no_alternate_or_overwrite(self):'
extra=''' def test_one_session_is_prepared_and_released(self):
  with patch.object(seo,"is_vertical_short_episode",return_value=False):
   self.assertTrue(self.call()["ok"])
  self.assertEqual(self.session_events,["prepare","close"])
 def test_prepare_failure_does_not_generate(self):
  import studio_mcp.production_tab as tabs
  with patch.object(tabs,"prepare",side_effect=RuntimeError("PREFLIGHT_REJECTED")):
   got=self.call()
  self.assertFalse(got["ok"])
  self.assertIn("PREFLIGHT_REJECTED",got["error"])
  self.assertEqual(len(self.calls),0)
'''
assert s.count(anchor)==1
s=s.replace(anchor,extra+anchor,1)
p.write_text(s,encoding="utf8")
print("UPDATED_UNIT_TESTS")
