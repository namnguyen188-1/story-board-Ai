import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image
from PIL import ImageDraw

import seo_packager as seo


class ExistingRegressionTests(unittest.TestCase):
    def test_missing_thumbnail_cannot_pass(self):
        card = seo.calculate_thumbnail_vidiq_scorecard(Path('missing-thumbnail.jpg'))
        self.assertEqual(card['total_score'], 0)
        self.assertEqual(card['source'], 'internal_technical_checklist')

    def test_actual_thumbnail_dimensions_are_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'tiny.jpg'
            Image.new('RGB', (100, 100), 'white').save(p)
            card = seo.calculate_thumbnail_vidiq_scorecard(p)
            self.assertLess(card['total_score'], 100)
            self.assertFalse(next(b for b in card['breakdown'] if b['id'] == 'resolution_16_9')['passed'])

    def test_spanish_accents_are_not_vietnamese_leak(self):
        self.assertTrue(seo.is_clean_lang_text('Relájate: cómo vivir con propósito y serenidad'))
        self.assertFalse(seo.is_clean_lang_text('Đăng ký kênh và xem tập tiếp theo'))

    def test_scores_have_honest_provenance_and_unknown_performance(self):
        card = seo.calculate_vidiq_score('', '', [], '', [])
        self.assertEqual(card.get('source'), 'internal_checklist')
        self.assertEqual(card.get('total_score'), 0)
        self.assertIsNone(card.get('performance_score'))

    def test_legacy_pack_cannot_regain_invented_metrics(self):
        pack = seo.enrich_seo_package({'best_title': '', 'description': '', 'tags': [],
            'titles': [{'title': 'An ordinary title', 'seo_score':'10/10', 'ctr_potential':'14-18%'}],
            'market_benchmark': {'percentile_rank':'Top 1%', 'market_average_score':62},
            'publishing_schedule': {'best_time_today':'19:45 tonight'}})
        self.assertEqual(pack['vidiq_score']['source'], 'internal_checklist')
        self.assertIsNone(pack['market_benchmark']['market_average_score'])
        self.assertIsNone(pack['titles'][0]['ctr_potential'])
        self.assertIsNone(pack['official_vidiq']['total_score'])
        self.assertIsNone(pack['publishing_schedule']['best_time_today'])

    def test_shorts_do_not_invent_hoa_or_camera(self):
        pack = seo.build_shorts_seo_pack('Calm', 2, 'English', 'stoic', 'Seneca',
            'stoic calm', 'How Seneca Faced Anger')
        text = json.dumps(pack, ensure_ascii=False).lower()
        self.assertNotIn('the hoa', text)
        self.assertNotIn('4k trail cam', text)
        self.assertEqual(pack['vidiq_score']['source'], 'internal_checklist')

    def test_two_people_leave_upper_faces_clear_of_overlay(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'two_people.png'
            im=Image.new('RGB',(1280,720),(30,30,40));draw=ImageDraw.Draw(im)
            draw.ellipse((200,70,480,350),fill=(220,160,140))
            draw.ellipse((820,70,1100,350),fill=(220,160,140));im.save(p)
            self.assertEqual(seo.auto_thumbnail_side(p),'bottom')


if __name__ == '__main__':
    unittest.main()
