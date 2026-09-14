"""Check catalog dates only. Never overwrite the historical atlas or train a model."""
import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path

COLLECTIONS = {
    'landsat8': 'LANDSAT/LC08/C02/T1_L2',
    'sentinel2': 'COPERNICUS/S2_SR_HARMONIZED',
    'era5_land': 'ECMWF/ERA5_LAND/HOURLY',
    'era5': 'ECMWF/ERA5/HOURLY',
}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', default=os.environ.get('EE_PROJECT_ID'))
    parser.add_argument('--output', type=Path, default=Path('catalog-status.json'))
    args = parser.parse_args()
    if not args.project:
        parser.error('Set EE_PROJECT_ID or --project; no interactive login is attempted.')
    import ee
    import google.auth
    credentials, _ = google.auth.default(scopes=[
        'https://www.googleapis.com/auth/earthengine',
        'https://www.googleapis.com/auth/cloud-platform'])
    ee.Initialize(credentials=credentials, project=args.project)
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=120)).strftime('%Y-%m-%d')
    end = (now + timedelta(days=1)).strftime('%Y-%m-%d')
    region = ee.Geometry.Rectangle([77.4459721532,12.7919511319,77.7501879705,13.1512756019], geodesic=False)
    result = {'checked_at':now.isoformat(), 'kind':'catalog_availability_only',
              'research_snapshot_end':'2026-05-03', 'collections':{}}
    for name, collection_id in COLLECTIONS.items():
        collection = ee.ImageCollection(collection_id).filterBounds(region).filterDate(start,end)
        # One bounded metadata query per collection; no raster extraction.
        timestamps = collection.sort('system:time_start',False).limit(1).aggregate_array('system:time_start').getInfo()
        latest = datetime.fromtimestamp(timestamps[0]/1000,timezone.utc).isoformat() if timestamps else None
        result['collections'][name] = {'collection':collection_id, 'latest_acquisition':latest,
            'note':'Catalog presence does not establish cloud-free coverage or model-ready inputs.'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    temporary = args.output.with_suffix('.tmp')
    temporary.write_text(json.dumps(result,indent=2),encoding='utf-8')
    temporary.replace(args.output)
    print('Catalog metadata saved. Research website data was not changed.')

if __name__ == '__main__':
    main()
