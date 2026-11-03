import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from PIL import Image
import seo_packager as seo
import project_organizer


class GenerationTests(unittest.TestCase):
    def fixture(self, tmp, language='English', genre='family_drama'):
        root=Path(tmp)/'series'/'episode_003'
        root.mkdir(parents=True)
        cases={
            'English': ('HOA Tow Warning','Evelyn threatens to tow the pickup truck.',
                ['Evelyn puts a tow warning on the pickup truck.','Marcus reads the HOA bylaws.','Arthur presents the property deed.'],
                'pickup truck', ['HOA Tow Warning','Evelyn Threatens the Pickup Truck','Marcus Reads the HOA Bylaws']),
            'Spanish': ('Controlar la ira con estoicismo','Séneca explica cómo controlar la ira con estoicismo.',
                ['Séneca explica la ira y la serenidad.','La pausa ayuda a controlar la ira.','La serenidad permite actuar con propósito.'],
                'controlar la ira',['Controlar la ira con estoicismo','Séneca explica la ira y la serenidad','La serenidad permite actuar con propósito']),
            'Vietnamese': ('Tiếng gõ cửa lúc nửa đêm','Lan nghe tiếng gõ cửa trong căn nhà vắng.',
                ['Lan nghe tiếng gõ cửa lúc nửa đêm.','Lan nhìn qua khe cửa trong căn nhà vắng.','Bóng người đứng trước cửa rồi biến mất.'],
                'tiếng gõ cửa',['Tiếng gõ cửa lúc nửa đêm','Lan nhìn qua khe cửa','Bóng người đứng trước cửa'])}
        title,summary,summaries,kw,titles=cases[language]
        plan={'config':{'language':language,'genre':genre,'episode':3,'series':'series'},'title':title,'logline':summary,
            'scenes':[{'scene_number':i,'summary':s,'narration':s} for i,s in enumerate(summaries,1)]}
        (root/'plan.json').write_text(json.dumps(plan,ensure_ascii=False),encoding='utf-8')
        for i in range(1,4):
            d=root/'scenes'/f'scene_{i:04d}'; d.mkdir(parents=True)
            (d/'result.json').write_text(json.dumps({'qc':{'duration_seconds':15+i}}))
            arr=np.random.default_rng(i).integers(30,220,(720,1280,3),dtype=np.uint8)
            Image.fromarray(arr).save(d/'image.png')
        response={'primary_keyword':kw,'titles':[{'title':t,'type':'Episode detail'} for t in titles],
            'description_hook':summary,'story_synopsis':summaries[-1],'tags':[kw,'mother and son','mailbox vandalism'],
            'hashtags':[],'thumbnail_hook_text':kw.upper(),'thumbnail_scene_num':2,'pinned_comment':''}
        return root,response

    def provider(self, response, calls, fail=False):
        def generate_content(**kwargs):
            calls.append(kwargs)
            if fail:
                raise RuntimeError('Provider unavailable')
            return types.SimpleNamespace(text=json.dumps(response,ensure_ascii=False))
        return types.SimpleNamespace(ResilientClient=lambda:types.SimpleNamespace(models=types.SimpleNamespace(generate_content=generate_content)))

    def test_three_languages_generate_one_image_and_consistent_exports(self):
        for lang,genre in [('English','family_drama'),('Spanish','stoic'),('Vietnamese','psychological_horror')]:
            with self.subTest(language=lang),tempfile.TemporaryDirectory() as tmp:
                root,response=self.fixture(tmp,lang,genre); calls=[]
                with patch.object(seo,'STUDIO_DIR',Path(tmp)),patch.dict(sys.modules,{'resilient_gemini':self.provider(response,calls)}):
                    pack=seo.generate_seo_package(root,'series',3)
                self.assertEqual(pack['generation']['method'],'ai_grounded')
                self.assertEqual(len(pack['titles']),3)
                self.assertEqual(len(pack['hashtags']),5)
                self.assertEqual(len(pack['thumbnail_options']),1)
                self.assertEqual(pack['thumbnail_scene_num'],2)
                self.assertEqual(pack['thumbnail_checks']['width'],1280)
                self.assertEqual(pack['thumbnail_checks']['height'],720)
                self.assertEqual(pack['source_summary']['scene_count'],3)
                self.assertIn(response['story_synopsis'],calls[0]['contents'])
                self.assertNotIn('mother and son',pack['tags'])
                self.assertNotIn('mailbox vandalism',pack['tags'])
                self.assertLessEqual(len(', '.join(pack['tags'])),500)
                self.assertTrue(all(len(t['title'])<=100 for t in pack['titles']))
                self.assertIn(response['primary_keyword'],pack['description'].lower())
                self.assertEqual(json.loads((root/'youtube_publish_pack.json').read_text(encoding="utf-8"))['best_title'],pack['best_title'])
                txt=(root/'youtube_publish_pack.txt').read_text(encoding="utf-8")
                self.assertIn(pack['best_title'],txt)
                self.assertNotIn('14-18%',txt)
                self.assertIsNone(pack['official_vidiq']['total_score'])

    def test_cache_survives_grouped_chapters_and_thumbnail_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,response=self.fixture(tmp); calls=[]
            with patch.object(seo,'STUDIO_DIR',Path(tmp)),patch.dict(sys.modules,{'resilient_gemini':self.provider(response,calls)}):
                first=seo.generate_seo_package(root,'series',3)
                seo.generate_seo_package(root,'series',3,custom_hook_text='READ THE BYLAWS')
                self.assertEqual(len(calls),1)
                plan=json.loads((root/'plan.json').read_text(encoding="utf-8")); plan['scenes'][-1]['summary']='Arthur leaves the meeting.'
                (root/'plan.json').write_text(json.dumps(plan))
                seo.generate_seo_package(root,'series',3)
                self.assertEqual(len(calls),2)

    def test_provider_failure_and_bad_content_are_explicit_fallbacks(self):
        for mode in ('unavailable','invented_plot'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                root,response=self.fixture(tmp); calls=[]
                if mode=='invented_plot':
                    response['titles'][0]['title']='The HOA Destroyed My Mailbox on Camera'
                with patch.object(seo,'STUDIO_DIR',Path(tmp)),patch.dict(sys.modules,{'resilient_gemini':self.provider(response,calls,fail=mode=='unavailable')}):
                    pack=seo.generate_seo_package(root,'series',3)
                self.assertEqual(pack['generation']['method'],'extractive_fallback')
                self.assertNotIn('mailbox',json.dumps(pack['titles']).lower())
                self.assertTrue(pack['generation']['review_required'])

    def test_mirrors_are_updated_with_txt_and_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,response=self.fixture(tmp); calls=[]
            pub=root/'00_DANG_BAI_YOUTUBE';pub.mkdir()
            mirror=pub/'03_THONG_TIN_DANG_BAI - previous.txt';mirror.write_text('STALE')
            with patch.object(seo,'STUDIO_DIR',Path(tmp)),patch.dict(sys.modules,{'resilient_gemini':self.provider(response,calls)}):
                seo.generate_seo_package(root,'series',3)
            self.assertEqual(mirror.read_text(encoding="utf-8"),(root/'youtube_publish_pack.txt').read_text(encoding="utf-8"))

    def test_single_thumbnail_export_does_not_include_legacy_variants(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,response=self.fixture(tmp); calls=[]
            Image.new('RGB',(1280,720),'red').save(root/'thumbnail_opt_1.jpg')
            with patch.object(seo,'STUDIO_DIR',Path(tmp)),patch.dict(sys.modules,{'resilient_gemini':self.provider(response,calls)}):
                seo.generate_seo_package(root,'series',3)
            result=project_organizer.organize_episode(root)
            self.assertEqual(result['details']['alt_thumbnails'],[])

    def test_missing_current_image_does_not_export_stale_thumbnail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'series'/'episode_003';root.mkdir(parents=True)
            (root/'youtube_publish_pack.json').write_text(json.dumps({'engine_version':'grounded-seo-2026.10.22.1',
                'episode':3,'thumbnail_file':None,'titles':[{'title':'Current episode'}]}))
            Image.new('RGB',(1280,720),'red').save(root/'thumbnail_seo.jpg')
            result=project_organizer.organize_episode(root)
            self.assertIsNone(result['details']['thumbnail'])


if __name__=='__main__':
    unittest.main()
