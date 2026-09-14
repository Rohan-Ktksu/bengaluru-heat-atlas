"""Validate a Stage 3 artifact against the protected historical grid and state."""
import argparse
from datetime import timedelta
from pathlib import Path
from monthly_policy import cutoff_metadata, month_cutoff, require_closed_window
from latest_common import (FIELDS, load_grid, protected_hashes, read_json,
                           validate_records, write_json, utc)

def validate(directory):
    metadata = read_json(directory/'metadata/processing_status.json')
    policy = cutoff_metadata(utc(metadata['generated_at']))
    if any(metadata.get(key)!=value for key,value in policy.items()):
        raise ValueError('Missing or inconsistent previous-month cutoff')
    if metadata['protected_sha256'] != protected_hashes():
        raise ValueError('Historical data/state does not match the processing snapshot')
    for flag in ['historical_atlas_modified','state_advanced','ml_applied']:
        if metadata[flag] is not False:
            raise ValueError('Artifact-only invariant failed: '+flag)
    if metadata['status']=='no_new_scenes':
        return {'status':'passed_no_new_scenes'}
    if metadata['status']!='processed_for_review':
        raise ValueError('Processing did not succeed')
    selected = metadata['selected_scenes']
    cutoff = month_cutoff(utc(metadata['generated_at']))
    for name,scene in selected.items():
        require_closed_window(scene['acquisition'],cutoff,
            timedelta(minutes=90) if name=='landsat8' else timedelta())
    rows = read_json(directory/'grid/latest_grid_features.json')
    counts = validate_records(rows,{r['Grid_ID'] for r in load_grid()},selected,
                              metadata['minimum_cell_valid_fraction'])
    if counts!=metadata['valid_cell_counts']:
        raise ValueError('Summary counts do not match grid')
    for row in rows:
        for name,scene in selected.items():
            if row[name+'_image_id']!=scene['image_id'] or utc(row[name+'_acquisition'])!=utc(scene['acquisition']):
                raise ValueError('Cell provenance mismatch')
    if read_json(directory/'metadata/selected_scenes.json')!=selected:
        raise ValueError('Selected scene files disagree')
    return {'status':'passed_for_manual_review','total_cells':len(rows),
            'valid_cell_counts':counts,'ready_for_ml':False,'ready_for_publication':False}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    args=parser.parse_args()
    result=validate(args.directory)
    write_json(args.directory/'metadata/validation.json',result)
    print(result)

if __name__=='__main__':
    main()
