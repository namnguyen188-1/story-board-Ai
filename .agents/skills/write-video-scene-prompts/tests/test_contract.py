import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from validate_prompts import validate

EXAMPLE = (ROOT/'tests/fixtures/camera_tang_13_64s.txt').read_text(encoding='utf-8')

class ContractRegression(unittest.TestCase):
    def test_valid_8x8_64s_9x16(self):
        r = validate(EXAMPLE, 64, '9:16')
        self.assertTrue(r['pass'], r['errors'])
        self.assertEqual((r['scene_count'],r['total_seconds']), (8,64))
        self.assertEqual(r['warnings'], [])
    def test_reject_changed_label(self):
        changed=EXAMPLE.replace('FORMAT & STYLE:', '1. FORMAT & STYLE:', 1)
        r=validate(changed,64,'9:16')
        self.assertFalse(r['pass'])
    def test_reject_missing_field(self):
        changed=EXAMPLE.replace('END STATE:', 'END STATE REMOVED:',1)
        r=validate(changed,64,'9:16')
        self.assertFalse(r['pass'])
    def test_reject_wrong_runtime(self):
        self.assertFalse(validate(EXAMPLE,60,'9:16')['pass'])
    def test_reject_wrong_ratio(self):
        self.assertFalse(validate(EXAMPLE,64,'16:9')['pass'])
    def test_reject_prefix_introduction(self):
        self.assertFalse(validate('Intro\n'+EXAMPLE,64,'9:16')['pass'])
    def test_reject_gap(self):
        changed=EXAMPLE.replace('SCENE_002 | TIMELINE 00:08–00:16','SCENE_002 | TIMELINE 00:09–00:16',1)
        self.assertFalse(validate(changed,64,'9:16')['pass'])

if __name__ == '__main__':
    unittest.main()
