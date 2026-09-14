import ast
import unittest
from pathlib import Path
from latest_common import ROOT
from v5_schema import FEATURES,WEATHER,RANGES,baseline_cutoff,paired,invalid_features

class V5InputTests(unittest.TestCase):
    def test_matches_actual_training_feature_order(self):
        tree=ast.parse((ROOT/'scripts/30_final_v5_hotspot_model.py').read_text())
        assignment=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='features' for t in n.targets))
        self.assertEqual(FEATURES,ast.literal_eval(assignment.value))
        self.assertEqual(len(FEATURES),25)
        self.assertEqual(set(FEATURES),set(RANGES))
        self.assertEqual(len(WEATHER),16)
    def test_pairing_boundaries(self):
        anchor='2026-06-04T05:00:00Z'
        self.assertTrue(paired(anchor,'2026-05-30T05:00:00Z'))
        self.assertFalse(paired(anchor,'2026-06-09T05:00:00Z'))
        self.assertFalse(paired(anchor,'2026-05-12T05:00:00Z'))
        self.assertTrue(paired(anchor,'2026-06-04T10:30:00+05:30'))
    def test_midnight_state_represents_processed_day(self):
        self.assertEqual(baseline_cutoff('2026-05-03T00:00:00Z').isoformat(),'2026-05-04T00:00:00+00:00')
        self.assertEqual(baseline_cutoff('2026-05-03T05:00:00Z').isoformat(),'2026-05-03T05:00:00.001000+00:00')
    def test_missing_nonfinite_out_of_range_are_not_eligible(self):
        row={k:(lo+hi)/2 for k,(lo,hi) in RANGES.items()}
        self.assertEqual(invalid_features(row),[])
        for value in [None,float('nan'),float('inf'),True,2]:
            row['S2_NDVI']=value
            self.assertIn('S2_NDVI',invalid_features(row))

if __name__=='__main__': unittest.main()
