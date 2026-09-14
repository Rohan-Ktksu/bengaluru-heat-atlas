"""Pure validation and schema helpers shared by the artifact-only processor."""
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from monthly_policy import month_cutoff, require_closed_window

ROOT = Path(__file__).resolve().parents[1]
GRID_PATH = ROOT / 'src/bengaluru_complete_1km_grid.csv'
COLLECTIONS = {'landsat8': 'LANDSAT/LC08/C02/T1_L2',
               'sentinel2': 'COPERNICUS/S2_SR_HARMONIZED'}
FIELDS = {'landsat8': ['LST', 'L_NDVI', 'NDBI', 'NDWI', 'Albedo'],
          'sentinel2': ['S2_NDVI']}
LIMITS = {'LST': (-60, 90), 'L_NDVI': (-1, 1), 'NDBI': (-1, 1),
          'NDWI': (-1, 1), 'S2_NDVI': (-1, 1), 'Albedo': (0, 1)}

def utc(value):
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('Acquisition dates must include a timezone')
    return parsed.astimezone(timezone.utc)

def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False), encoding='utf-8')
    temporary.replace(path)

def load_grid(path=GRID_PATH):
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 1320 or len({r['Grid_ID'] for r in rows}) != 1320:
        raise ValueError('Expected exactly 1,320 unique canonical cells')
    for row in rows:
        w,s,e,n = [float(row[k]) for k in ('West_Longitude','South_Latitude','East_Longitude','North_Latitude')]
        if not (77 < w < e < 79 and 12 < s < n < 14):
            raise ValueError('Invalid Bengaluru grid geometry')
    return rows

def selected_scenes(report, state):
    if report.get('kind') != 'usable_update_detection_v2':
        raise ValueError('An AOI-checked Stage 2 v2 detection report is required')
    selected = {}
    for name, collection in COLLECTIONS.items():
        if name not in state:
            raise ValueError(f'Missing baseline for {name}')
        baseline = utc(state[name])
        entry = report['collections'][name]
        candidate = entry.get('selected_update')
        if not entry.get('update_available'):
            if candidate is not None:
                raise ValueError('Conflicting selected_update and update_available')
            continue
        if entry.get('collection') != collection or not isinstance(candidate, dict):
            raise ValueError('Unexpected collection or missing selected scene')
        if candidate.get('usable') is not True:
            raise ValueError('Selected scene was not marked usable')
        cloud = candidate.get('aoi_cloud_percentage')
        if not isinstance(cloud, (int,float)) or not math.isfinite(cloud) or not 0 <= cloud <= 20:
            raise ValueError('Invalid AOI cloud percentage')
        if utc(candidate['acquisition']) <= baseline:
            raise ValueError('Selected scene is not newer than processed state')
        if utc(candidate['acquisition']) > utc(report['checked_at']):
            raise ValueError('Scene acquisition is after the detection check')
        require_closed_window(candidate['acquisition'],month_cutoff(utc(report['checked_at'])))
        image_id = candidate['image_id']
        if not image_id or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in image_id):
            raise ValueError('Expected a scene index, not an arbitrary asset path')
        selected[name] = {**candidate, 'asset_id': collection+'/'+image_id}
    if bool(selected) != bool(report.get('updates_available')):
        raise ValueError('Inconsistent report update flag')
    return selected

def output_directory(path):
    path = Path(path).resolve()
    allowed = (ROOT / 'latest_data').resolve()
    if path != allowed and allowed not in path.parents:
        raise ValueError('Outputs must stay under latest_data; historical paths are forbidden')
    if path.exists():
        raise ValueError('Use a new output directory to prevent mixing old and new artifacts')
    return path

def protected_hashes():
    paths = [ROOT/'automation/update_state.json', GRID_PATH]
    paths += sorted((ROOT/'website/data').glob('*.json'))
    paths += sorted((ROOT/'website/dist/data').glob('*.json'))
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}

def validate_records(records, expected_ids, selected, minimum):
    if len(records) != len(expected_ids) or {r['Grid_ID'] for r in records} != set(expected_ids):
        raise ValueError('Missing, duplicated, or unknown grid IDs')
    counts = {name:0 for name in selected}
    for row in records:
        if row.get('source_kind') != 'latest_conditions_observed_features':
            raise ValueError('Invalid source kind')
        for name in selected:
            fraction = row[name+'_valid_fraction']
            if not isinstance(fraction,(int,float)) or not math.isfinite(fraction) or not 0 <= fraction <= 1:
                raise ValueError('Invalid valid-pixel fraction')
            values = [row[k] for k in FIELDS[name]]
            if fraction < minimum:
                if any(v is not None for v in values):
                    raise ValueError('Low-coverage cell contains accepted feature values')
            else:
                for field in FIELDS[name]:
                    value = row[field]
                    low,high = LIMITS[field]
                    if not isinstance(value,(int,float)) or not math.isfinite(value) or not low <= value <= high:
                        raise ValueError(f'Invalid {field} for {row["Grid_ID"]}: {value}')
                counts[name] += 1
    if any(count == 0 for count in counts.values()):
        raise ValueError('A selected source has no adequately covered cells')
    return counts
