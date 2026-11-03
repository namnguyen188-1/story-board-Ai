import unittest,tempfile,json,sys
from pathlib import Path
from unittest.mock import patch
import seo_quality

class AutoScores(unittest.TestCase):
 def test_enrich_preserves_provider_evidence(self):
  p={'official_vidiq':{'status':'scored','title_scores':[{'title':'A','score':81}]}}
  self.assertEqual(seo_quality.enrich(p)['official_vidiq']['status'],'scored')
 def test_auto_scores_once_and_invalidates_changed_title(self):
  import vidiq_auto as v
  with tempfile.TemporaryDirectory() as t:
   calls=[]
   class Client:
    def score_title(self,title,kind):calls.append(title);return {'score':81,'_credits':{'used':5}}
   p={'titles':[{'title':'A'},{'title':'B'},{'title':'C'}]}
   with patch.object(v,'api_key',return_value='secret'),patch.object(v,'Client',return_value=Client()):
    v.ensure_scores(t,p);v.ensure_scores(t,p)
    self.assertEqual(len(calls),3)
    self.assertEqual(p['official_vidiq']['title_scores'][0]['score'],81)
    self.assertIsNone(p['official_vidiq']['total_score'])
    p['titles'][0]['title']='D';v.ensure_scores(t,p)
    self.assertEqual(len(calls),4)
 def test_missing_key_and_timeout_never_fake_score_or_repeat_charge(self):
  import vidiq_auto as v
  with tempfile.TemporaryDirectory() as t:
   p={'titles':[{'title':'A'}]}
   with patch.object(v,'api_key',return_value=''):v.ensure_scores(t,p)
   self.assertEqual(p['official_vidiq']['status'],'not_connected')
   calls=[]
   class Client:
    def score_title(self,*a):calls.append(1);raise TimeoutError('secret must never appear')
   with patch.object(v,'api_key',return_value='secret'),patch.object(v,'Client',return_value=Client()):
    v.ensure_scores(t,p);v.ensure_scores(t,p)
   self.assertEqual(len(calls),1)
   self.assertIsNone(p['official_vidiq']['title_scores'][0]['score'])
   self.assertNotIn('secret',json.dumps(p))
 def test_every_saved_pack_runs_auto_scoring(self):
  import seo_packager as s
  with tempfile.TemporaryDirectory() as t,patch('vidiq_auto.ensure_scores',side_effect=lambda root,p:p) as scoring:
   s.write_seo_package(t,{'episode':1})
   self.assertTrue(scoring.called)

 def test_connection_failure_can_recover_without_manual_scoring(self):
  import vidiq_auto as v
  with tempfile.TemporaryDirectory() as t:
   p={'titles':[{'title':'A'}]}
   class Good:
    def score_title(self,*args):return {'score':82}
   with patch.object(v,'api_key',return_value='secret'),patch.object(v,'Client',side_effect=[OSError('connection'),Good()]):
    v.ensure_scores(t,p);v.ensure_scores(t,p)
   self.assertEqual(p['official_vidiq']['title_scores'][0]['score'],82)
