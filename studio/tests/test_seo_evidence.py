import json
import tempfile
import unittest
from pathlib import Path

import seo_quality as q


class EvidenceTests(unittest.TestCase):
    def make_episode(self, root, language='English'):
        ep = Path(root) / 'episode_003'
        ep.mkdir()
        plan = {'config': {'language':language,'genre':'family_drama','episode':3},
            'title':'The HOA Tow Warning', 'logline':'Evelyn threatens to tow Marcus\'s pickup truck.',
            'scenes':[{'scene_number':i+1,'summary':s} for i,s in enumerate([
                'Evelyn puts a tow warning on the pickup truck.',
                'Marcus reads the HOA bylaws.',
                'Arthur presents the property deed at the board meeting.'])]}
        (ep/'plan.json').write_text(json.dumps(plan))
        return ep

    def test_all_scenes_and_dialogue_enter_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            ep = self.make_episode(tmp)
            drama = {'cast':[{'name':'Arthur'}], 'scenes':[{'scene_number':3,
                'dialogue_beats':[{'speaker':'Arthur','text':'The easement belongs to the residents.'}]}]}
            (ep/'drama_plan.json').write_text(json.dumps(drama))
            ctx=q.build_episode_context(ep)
            self.assertIn('property deed',ctx['evidence_text'])
            self.assertIn('easement belongs',ctx['evidence_text'])
            self.assertEqual(len(ctx['scenes']),3)
            self.assertIn('Arthur',ctx['characters'])

    def test_reference_is_not_treated_as_produced_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            ep=self.make_episode(tmp)
            (ep/'reference_analysis.json').write_text(json.dumps({'title':'HOA Destroyed My Mailbox on Camera'}))
            ctx=q.build_episode_context(ep)
            self.assertNotIn('mailbox',ctx['evidence_text'].lower())
            self.assertFalse(q.is_grounded('HOA Destroyed My Mailbox',ctx))
            self.assertFalse(q.is_grounded('Caught on Camera: The HOA',ctx))

    def test_tags_are_relevant_without_padding(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx=q.build_episode_context(self.make_episode(tmp))
            tags=q.relevant_tags(['hoa bylaws','mother and son','mailbox vandalism','HOA bylaws'],ctx)
            self.assertIn('hoa bylaws',tags)
            self.assertNotIn('mother and son',tags)
            self.assertNotIn('mailbox vandalism',tags)
            self.assertEqual(tags.count('hoa bylaws'),1)
            self.assertLessEqual(len(', '.join(tags)),500)

    def test_fingerprint_changes_with_final_scene_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            ep=self.make_episode(tmp)
            first=q.build_episode_context(ep)['fingerprint']
            p=json.loads((ep/'plan.json').read_text(encoding="utf-8"))
            p['scenes'][-1]['summary']='Arthur leaves the board meeting.'
            (ep/'plan.json').write_text(json.dumps(p))
            self.assertNotEqual(first,q.build_episode_context(ep)['fingerprint'])

    def test_unknown_durations_do_not_create_fake_chapters(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx=q.build_episode_context(self.make_episode(tmp))
            self.assertEqual(q.episode_chapters(ctx),[])

    def test_chapters_use_measured_durations_and_minimum_ten_seconds(self):
        with tempfile.TemporaryDirectory() as tmp:
            ep=self.make_episode(tmp)
            for i,sec in enumerate([12,15,20],1):
                d=ep/'scenes'/f'scene_{i:04d}'
                d.mkdir(parents=True)
                (d/'result.json').write_text(json.dumps({'qc':{'duration_seconds':sec}}))
            chapters=q.episode_chapters(q.build_episode_context(ep))
            self.assertEqual([c['seconds'] for c in chapters],[0,12,27])
            self.assertTrue(all(c['timing_source']=='rendered' for c in chapters))

    def test_spanish_grounding_keeps_accents(self):
        ctx={'evidence_text':'Relájate y aprende a controlar la ira con estoicismo.', 'language':'Spanish'}
        self.assertTrue(q.is_grounded('Controlar la ira con estoicismo',ctx))
        self.assertFalse(q.is_grounded('La policía arrestó a la vecina',ctx))

    def test_episode_branding_is_not_a_story_claim(self):
        ctx={'evidence_text':'Residents HOA board member against power. Scene 3', 'language':'English'}
        self.assertTrue(q.is_grounded('Residents Fight Back Against Power-Hungry HOA Board Member - DRAMA Ep 3',ctx))

    def test_fallback_is_extractive_and_does_not_invent_plot(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx=q.build_episode_context(self.make_episode(tmp))
            content=q.fallback_content(ctx)
            combined=json.dumps(content).lower()
            self.assertNotIn('mailbox',combined)
            self.assertNotIn('true story',combined)
            self.assertEqual(len(content['titles']),3)
            self.assertEqual(len(content['hashtags']),5)

    def test_corrupt_plan_fails_explicitly(self):
        with tempfile.TemporaryDirectory() as tmp:
            ep=Path(tmp)
            (ep/'plan.json').write_text('{broken')
            with self.assertRaises(ValueError):
                q.build_episode_context(ep)

    def test_native_drama_cast_mapping_is_supported(self):
        with tempfile.TemporaryDirectory() as tmp:
            ep=self.make_episode(tmp)
            (ep/'drama_plan.json').write_text(json.dumps({'cast':{'arthur':{'name':'Arthur'},'evelyn':{'name':'Evelyn'}}}))
            ctx=q.build_episode_context(ep)
            self.assertIn('Arthur',ctx['characters'])
            self.assertIn('Evelyn',ctx['characters'])


if __name__ == '__main__':
    unittest.main()
