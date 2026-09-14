"""Run the checksum-verified original V5 model on validated rows, for review only."""
import argparse
import hashlib
import importlib.metadata
from pathlib import Path
from latest_common import ROOT,protected_hashes,read_json,write_json
from v5_schema import FEATURES,inference_rows
from validate_v5_inputs import validate

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    parser.add_argument('--model',type=Path,required=True)
    args=parser.parse_args()
    directory=args.directory.resolve()
    if (ROOT/'latest_data').resolve() not in directory.parents:
        raise ValueError('Inference output must stay within latest_data')
    report=validate(args.directory,verify_protected=False)
    if report['eligible_cell_count']==0: raise ValueError('No matched inputs to predict')
    manifest=read_json(ROOT/'MODEL_MANIFEST.json')
    expected=next(x for x in manifest if x['filename']=='urban_heat_model_v5.pkl')
    digest=hashlib.sha256()
    with args.model.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''): digest.update(block)
    if digest.hexdigest()!=expected['sha256']: raise ValueError('Model checksum mismatch')
    versions=dict(line.split('==') for line in (ROOT/'research-environment.txt').read_text().splitlines() if '==' in line)
    for name in ['scikit-learn','numpy','joblib']:
        if importlib.metadata.version(name)!=versions[name]: raise ValueError('Restore the recorded model runtime version for '+name)
    before=protected_hashes()
    import joblib
    import numpy as np
    import pandas as pd
    bundle=joblib.load(args.model)  # Only after manifest verification, never an arbitrary URL.
    if list(bundle['features'])!=FEATURES: raise ValueError('Serialized model feature order mismatch')
    model=bundle['model']
    if list(model.feature_names_in_)!=FEATURES: raise ValueError('Estimator feature order mismatch')
    rows=inference_rows(read_json(args.directory/'grid/v5_model_inputs.json'))
    frame=pd.DataFrame(rows)[FEATURES]
    predictions=model.predict(frame)
    if not np.isfinite(predictions).all(): raise ValueError('Non-finite predictions')
    output=[{'Grid_ID':r['Grid_ID'],'Predicted_LST':float(v),'observed_LST':r['observed_LST'],
             'landsat_acquisition':r['landsat_acquisition'],'sentinel_acquisition':r['sentinel_acquisition'],
             'source_kind':'experimental_v5_prediction'} for r,v in zip(rows,predictions)]
    comparisons=[(r['Predicted_LST'],r['observed_LST']) for r in output if r['observed_LST'] is not None]
    summary={'status':'predicted_for_review','predicted_cells':len(output),'model_sha256':digest.hexdigest(),
             'ready_for_publication':False,'historical_atlas_modified':False,'state_advanced':False,
             'note':'Grid-mean input inference differs from pixel training support. Diagnostics are not independent accuracy certification.'}
    input_status=read_json(args.directory/'metadata/model_input_status.json')
    for key in ['run_kind','data_cutoff_exclusive','data_through','data_date_policy']:
        summary[key]=input_status[key]
    if comparisons:
        errors=np.array([p-o for p,o in comparisons])
        summary['observed_comparison']={'cells':len(comparisons),'MAE_C':float(abs(errors).mean()),
            'RMSE_C':float(np.sqrt((errors**2).mean())),'bias_C':float(errors.mean())}
    if protected_hashes()!=before: raise RuntimeError('Protected data changed')
    destination=args.directory/'predictions'
    if destination.exists(): raise ValueError('Predictions already exist; preserve the first review artifact')
    write_json(destination/'v5_predictions.json',output)
    write_json(destination/'summary.json',summary)
    print(summary)

if __name__=='__main__': main()
