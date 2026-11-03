import json,pathlib,tempfile,unittest,sys
ROOT=pathlib.Path(__file__).parent
if not (ROOT/'seo_quality.py').exists(): ROOT=ROOT.parent
sys.path.insert(0,str(ROOT));import seo_quality as q
class TopicAlignment(unittest.TestCase):
 def fixture(self,tmp):
  root=pathlib.Path(tmp)
  scenes=[]
  for i in range(1,5):
   scenes.append({'scene_number':i,'summary':'Colossal stone monument in contemplation amid ancient ruins.','description':'Roman stone statue with cinematic light.','narration':'Recuperar el entusiasmo por la vida exige reconocer lo que podemos controlar. La sabiduría estoica nos enseña a cultivar el propósito interior y la fortaleza ante la adversidad.','text_overlay':['Recuperar el entusiasmo por la vida','Gobernar la propia mente','Lecciones estoicas para vivir mejor','El propósito interior'][i-1]})
   d=root/'scenes'/f'scene_{i:04d}';d.mkdir(parents=True);(d/'result.json').write_text(json.dumps({'qc':{'duration_seconds':25}}))
  (root/'plan.json').write_text(json.dumps({'config':{'series':'Stoic','language':'Spanish','genre':'stoic'},'scenes':scenes}),encoding='utf-8')
  (root/'reference_analysis.json').write_text(json.dumps({'title':'Lecciones estoicas para recuperar el entusiasmo por la vida','language':'Spanish'}),encoding='utf-8')
  return root
 def test_context_keeps_reference_topic_and_spoken_content(self):
  with tempfile.TemporaryDirectory() as tmp:
   ctx=q.build_episode_context(self.fixture(tmp))
   self.assertIn('entusiasmo',ctx.get('reference_title','').lower())
   self.assertNotIn('Colossal stone',ctx['evidence_text'])
   self.assertIn('propósito interior',ctx['evidence_text'])
 def test_fallback_never_replaces_topic_with_visual_subject(self):
  with tempfile.TemporaryDirectory() as tmp:
   ctx=q.build_episode_context(self.fixture(tmp));data=q.fallback_content(ctx)
   public=' '.join([data['primary_keyword'],data['description_hook']]+[x['title'] for x in data['titles']]+data['tags']+data['hashtags'])
   self.assertNotIn('stone',public.lower());self.assertNotIn('monument',public.lower())
   self.assertTrue(any('vida' in t['title'].lower() or 'estoic' in t['title'].lower() for t in data['titles']))
   self.assertIn('entusiasmo',data['description_hook'])
 def test_chapters_use_spoken_language_not_english_shot_notes(self):
  with tempfile.TemporaryDirectory() as tmp:
   chapters=q.episode_chapters(q.build_episode_context(self.fixture(tmp)))
   self.assertEqual(chapters[0]['time'],'00:00')
   self.assertIn('entusiasmo',chapters[0]['title'])
   self.assertFalse(any('stone' in c['title'].lower() for c in chapters))
 def test_english_provider_titles_are_rejected_for_spanish_episode(self):
  ctx={'language':'Spanish','evidence_text':'The loss of purpose in daily living. The weight of the past and inner detachment. The wisdom of the ancient world.'}
  data={'titles':[{'title':'The loss of purpose in daily living'},{'title':'The weight of the past and inner detachment'},{'title':'The wisdom of the ancient world'}]}
  with self.assertRaises(ValueError):q.validate_content(data,ctx)
if __name__=='__main__':unittest.main(verbosity=2)
