"""Validate pairing, canonical IDs, input order, coverage and feature eligibility."""
import argparse
import math
from pathlib import Path
from latest_common import load_grid, protected_hashes, read_json, write_json
from v5_schema import FEATURES,paired,invalid_features

def validate(directory,verify_protected=True):
    status=read_json(directory/'metadata/model_input_status.json')
    if status['feature_order']!=FEATURES: raise ValueError('Feature order mismatch')
    if any(status.get(k) is not False for k in ['historical_atlas_modified','state_advanced','ml_applied','ready_for_publication']):
        raise ValueError('Review-only invariant failed')
    if verify_protected and status['protected_sha256']!=protected_hashes():
        raise ValueError('Protected inputs changed')
    if status['status']=='no_compatible_pair':
        if status.get('pair') is not None or status['eligible_cell_count']!=0:
            raise ValueError('No-pair status contains eligible data')
        return {'status':'passed_no_compatible_pair','eligible_cell_count':0,'ready_for_publication':False}
    if status['status']!='inputs_ready_for_inference_review': raise ValueError('Inputs incomplete')
    pair=status['pair']
    if not paired(pair['landsat_acquisition'],pair['sentinel_acquisition']): raise ValueError('Dates cannot be paired')
    if pair['joint_full_aoi_valid_fraction']<.8: raise ValueError('Insufficient scene-pair coverage')
    rows=read_json(directory/'grid/v5_model_inputs.json')
    ids={r['Grid_ID'] for r in load_grid()}
    if len(rows)!=len(ids) or {r['Grid_ID'] for r in rows}!=ids: raise ValueError('Grid mismatch')
    eligible=0
    for row in rows:
        fraction=row['valid_fraction']
        if not isinstance(fraction,(int,float)) or not math.isfinite(fraction) or not 0<=fraction<=1:
            raise ValueError('Invalid coverage')
        for key in ['landsat_acquisition','sentinel_acquisition']:
            if row[key]!=pair[key]: raise ValueError('Scene timestamp mismatch')
        bad=invalid_features(row)
        expected=fraction>=.7 and not bad
        if row['eligible_for_inference'] is not expected or row['invalid_or_missing_features']!=bad:
            raise ValueError('Eligibility inconsistent with values')
        eligible+=expected
    if not eligible or eligible!=status['eligible_cell_count']: raise ValueError('Eligibility count mismatch')
    return {'status':'passed_for_inference_review','eligible_cell_count':eligible,
            'total_cells':len(rows),'ready_for_publication':False}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    args=parser.parse_args()
    result=validate(args.directory)
    write_json(args.directory/'metadata/input_validation.json',result)
    print(result)

if __name__=='__main__': main()
