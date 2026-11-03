import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
import sys

from PIL import Image
import seo_quality as q
import seo_packager as seo
import project_organizer as organizer
import test_seo_generation as fixtures


class ReviewRegressionTests(unittest.TestCase):
    def make(self, tmp):
        return fixtures.GenerationTests().fixture(tmp)

    def test_default_auto_genre_produces_the_normal_cache_fingerprint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,_=self.make(tmp)
            self.assertEqual(q.build_episode_context(root, 'auto', 'auto')['fingerprint'],q.build_episode_context(root)['fingerprint'])

    def test_episode_ten_never_modifies_episode_one_hundred(self):
        with tempfile.TemporaryDirectory() as tmp:
            ep=Path(tmp)/'series'/'episode_010';ep.mkdir(parents=True)
            hundred=ep.parent/'00_XUAT_BAN_TOAN_BO_SERIES'/'Tap_100 - Other'
            hundred.mkdir(parents=True)
            target=hundred/'THONG_TIN_DANG_BAI_Tap_10.txt';target.write_text('OTHER EPISODE')
            pack={'engine_version':q.ENGINE_VERSION,'episode':10,'series':'series','titles':[{'title':'Episode ten'}], 'thumbnail_file':None}
            seo.write_seo_package(ep,pack)
            self.assertEqual(target.read_text(encoding="utf-8"),'OTHER EPISODE')
            organizer.organize_episode(ep)
            self.assertTrue(hundred.is_dir())

    def test_same_file_thumbnail_selection_is_a_noop(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'thumbnail_seo.jpg';Image.new('RGB',(1280,720),'red').save(p)
            self.assertEqual(seo.select_thumbnail_file(Path(tmp),'thumbnail_seo.jpg'),p)

    def test_stale_series_thumbnail_is_archived(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,response=self.make(tmp);calls=[]
            provider=fixtures.GenerationTests().provider(response,calls)
            with patch.object(seo,'STUDIO_DIR',Path(tmp)),patch.dict(sys.modules,{'resilient_gemini':provider}):
                pack=seo.generate_seo_package(root,'series',3)
            first=organizer.organize_episode(root)
            series_dir=Path(first['details']['series_publish_dir'])
            self.assertTrue(list(series_dir.glob('THUMBNAIL_CHINH*')))
            pack['thumbnail_file']=None
            seo.write_seo_package(root,pack)
            organizer.organize_episode(root)
            self.assertEqual(list(series_dir.glob('THUMBNAIL_CHINH*')),[])

    def test_malformed_provider_fields_and_duplicate_titles_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,response=self.make(tmp);ctx=q.build_episode_context(root)
            bad=dict(response,tags='not a list')
            with self.assertRaises(ValueError): q.validate_content(bad,ctx)
            bad=dict(response,titles=[response['titles'][0]]*3)
            with self.assertRaises(ValueError): q.validate_content(bad,ctx)

    def test_invented_pinned_comment_is_not_published(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,response=self.make(tmp);calls=[]
            response['pinned_comment']='Did the police arrest Evelyn after she burned the mailbox?'
            provider=fixtures.GenerationTests().provider(response,calls)
            with patch.object(seo,'STUDIO_DIR',Path(tmp)),patch.dict(sys.modules,{'resilient_gemini':provider}):
                pack=seo.generate_seo_package(root,'series',3)
            self.assertNotIn('mailbox',pack['pinned_comment'])

    def test_unsupported_keyword_is_replaced_without_discarding_grounded_titles(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,response=self.make(tmp);ctx=q.build_episode_context(root)
            response['primary_keyword']='HOA alien invasion'
            checked=q.validate_content(response,ctx)
            self.assertNotEqual(checked['primary_keyword'],'HOA alien invasion')
            self.assertEqual(checked['titles'],response['titles'])

    def test_restored_provider_is_retried_after_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,response=self.make(tmp);calls=[]
            with patch.object(seo,'STUDIO_DIR',Path(tmp)),patch.dict(sys.modules,{'resilient_gemini':fixtures.GenerationTests().provider(response,calls,fail=True)}):
                seo.generate_seo_package(root,'series',3)
            with patch.object(seo,'STUDIO_DIR',Path(tmp)),patch.dict(sys.modules,{'resilient_gemini':fixtures.GenerationTests().provider(response,calls)}):
                pack=seo.generate_seo_package(root,'series',3)
            self.assertEqual(pack['generation']['method'],'ai_grounded')

    def test_manual_import_waits_for_episode_generation_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,response=self.make(tmp);source=Path(tmp)/'upload.jpg'
            Image.new('RGB',(1280,720),'blue').save(source)
            entered=threading.Event();errors=[]
            original_open=Image.open
            def observed_open(*args,**kwargs):
                entered.set()
                return original_open(*args,**kwargs)
            def run():
                try: seo.import_and_boost_competitor_thumbnail(source,root,'Title',[])
                except Exception as exc: errors.append(exc)
            lock=seo._episode_lock(root)
            lock.acquire()
            try:
                with patch.object(seo,'STUDIO_DIR',Path(tmp)),patch.object(Image,'open',observed_open):
                    thread=threading.Thread(target=run);thread.start()
                    self.assertFalse(entered.wait(.1),'image import must wait while generation holds the episode lock')
            finally:
                lock.release()
                thread.join(2)
            self.assertEqual(errors,[])


if __name__=='__main__': unittest.main()
