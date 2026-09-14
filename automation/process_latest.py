"""Extract selected scenes to the canonical grid; artifact only, no ML or publication."""
import argparse
from datetime import datetime, timezone, timedelta
import os
from pathlib import Path

from latest_common import (ROOT, GRID_PATH, FIELDS, load_grid, output_directory,
    protected_hashes, read_json, selected_scenes, utc, validate_records, write_json)
from monthly_policy import month_cutoff, cutoff_metadata, require_closed_window

def ratio(a, b, name):
    denominator = a.add(b)
    return a.subtract(b).divide(denominator).updateMask(denominator.abs().gt(1e-8)).rename(name)

def landsat_features(image):
    # Formulas from scripts 13/19/36. Additional fill exclusion is a validity check.
    qa = image.select('QA_PIXEL')
    valid = qa.bitwiseAnd((1 << 3) | (1 << 4) | 1).eq(0)
    clean = image.updateMask(valid)
    blue,green,red,nir,swir,swir2 = [clean.select('SR_B'+str(b)).multiply(.0000275).add(-.2)
                                  for b in [2,3,4,5,6,7]]
    albedo = (blue.multiply(.356).add(red.multiply(.130)).add(nir.multiply(.373))
              .add(swir.multiply(.085)).add(swir2.multiply(.072)).subtract(.0018).rename('Albedo'))
    lst = clean.select('ST_B10').multiply(.00341802).add(149).subtract(273.15).rename('LST')
    return lst.addBands([ratio(nir,red,'L_NDVI'),ratio(swir,nir,'NDBI'),ratio(green,nir,'NDWI'),albedo])

def sentinel_features(image):
    scl = image.select('SCL')
    valid = scl.neq(0).And(scl.neq(1))
    for code in [3,8,9,10,11]:
        valid = valid.And(scl.neq(code))
    clean = image.updateMask(valid)
    return ratio(clean.select('B8'),clean.select('B4'),'S2_NDVI')

def feature_collection(ee, rows):
    return ee.FeatureCollection([ee.Feature(ee.Geometry.Rectangle([
        float(r[k]) for k in ['West_Longitude','South_Latitude','East_Longitude','North_Latitude']
    ],geodesic=False), {'Grid_ID':r['Grid_ID']}) for r in rows])

def reduce_scene(ee, stack, rows):
    # Full-cell denominator: uncovered pixels count as zero, not silently omitted.
    valid = stack.mask().reduce(ee.Reducer.min()).unmask(0, sameFootprint=False).rename('valid_fraction')
    combined = stack.addBands(valid)
    result = {}
    for offset in range(0,len(rows),110):
        chunk = feature_collection(ee,rows[offset:offset+110])
        reduced = combined.reduceRegions(collection=chunk,reducer=ee.Reducer.mean(),
            scale=30,crs='EPSG:32643',tileScale=4)
        # Strip geometry before transferring a bounded page of numeric properties.
        items = reduced.map(lambda f: ee.Feature(None,f.toDictionary())).getInfo()['features']
        for item in items:
            properties = item['properties']
            if properties['Grid_ID'] in result:
                raise ValueError('Duplicate reduced cell')
            result[properties['Grid_ID']] = properties
        print(f'Aggregated {min(offset+110,len(rows))}/{len(rows)} cells',flush=True)
    return result

def overpass_weather(ee, acquisition):
    # Script 28: mean images in +/-90 min, then AOI mean at 10 km.
    when = ee.Date(acquisition)
    start,end = when.advance(-90,'minute'),when.advance(90,'minute')
    # Preserve script 28's original weather AOI rather than silently changing it.
    region = ee.Geometry.Rectangle([77.45,12.80,77.75,13.15])
    collections = [ee.ImageCollection(name).filterBounds(region).filterDate(start,end)
                   for name in ['ECMWF/ERA5_LAND/HOURLY','ECMWF/ERA5/HOURLY']]
    times = [c.aggregate_array('system:time_start').getInfo() for c in collections]
    if any(not t for t in times):
        return {'status':'unavailable','acquisition':acquisition,'hourly_timestamps_ms':times,'values':None}
    land,cloud = [c.mean() for c in collections]
    temp = land.select('temperature_2m').subtract(273.15)
    dew = land.select('dewpoint_temperature_2m').subtract(273.15)
    rh = dew.multiply(17.625).divide(dew.add(243.04)).exp().divide(
        temp.multiply(17.625).divide(temp.add(243.04)).exp()).multiply(100)
    wind = land.select('u_component_of_wind_10m').pow(2).add(land.select('v_component_of_wind_10m').pow(2)).sqrt()
    solar = land.select('surface_solar_radiation_downwards_hourly').divide(1000000)
    cover = cloud.select('total_cloud_cover').multiply(100)
    stack = temp.rename('Overpass_Air_Temp').addBands([
        rh.rename('Overpass_Relative_Humidity'),wind.rename('Overpass_Wind_Speed'),
        solar.rename('Overpass_Solar_Radiation'),cover.rename('Overpass_Cloud_Cover')])
    values = stack.reduceRegion(reducer=ee.Reducer.mean(),geometry=region,scale=10000,maxPixels=1e9).getInfo()
    import math
    if len(values)!=5 or any(v is None or not math.isfinite(v) for v in values.values()):
        raise ValueError('Incomplete overpass weather values')
    return {'status':'available','acquisition':acquisition,'window_minutes':90,
            'hourly_timestamps_ms':times,'spatial_support':'AOI mean, not 1 km weather',
            'units':{'Overpass_Air_Temp':'C','Overpass_Relative_Humidity':'%',
                     'Overpass_Wind_Speed':'m/s','Overpass_Solar_Radiation':'MJ/m2 per hourly accumulation',
                     'Overpass_Cloud_Cover':'%'},'values':values}

def run(args):
    output = output_directory(args.output)
    state = read_json(args.state)
    report = read_json(args.detection)
    selected = selected_scenes(report,state)
    now = datetime.now(timezone.utc)
    cutoff = month_cutoff(now)
    for name,scene in selected.items():
        require_closed_window(scene['acquisition'],cutoff,
            timedelta(minutes=90) if name=='landsat8' else timedelta())
    before = protected_hashes()
    metadata = {'schema_version':1,'generated_at':now.isoformat(),
        'source_kind':'latest_conditions_observed_features','selected_scenes':selected,
        'historical_atlas_modified':False,'state_advanced':False,'ml_applied':False,
        'grid_source':str(GRID_PATH.relative_to(ROOT)), 'protected_sha256':before,
        'minimum_cell_valid_fraction':args.min_valid_fraction,
        'aggregation':'mean at 30 m in EPSG:32643; no imputation',
        'scene_pairing':'Independent sensor dates; not a model-ready paired feature matrix'}
    metadata.update(cutoff_metadata(now))
    if not selected:
        metadata['status']='no_new_scenes'
        write_json(output/'metadata/processing_status.json',metadata)
        return
    import ee
    import google.auth
    credentials,_ = google.auth.default(scopes=['https://www.googleapis.com/auth/earthengine',
                                               'https://www.googleapis.com/auth/cloud-platform'])
    ee.Initialize(credentials=credentials,project=args.project)
    rows = load_grid()
    records = {r['Grid_ID']:{'Grid_ID':r['Grid_ID'],'source_kind':metadata['source_kind']} for r in rows}
    for name,scene in selected.items():
        image = ee.Image(scene['asset_id'])
        info = image.toDictionary(['system:time_start','PROCESSING_LEVEL']).getInfo()
        actual = datetime.fromtimestamp(info['system:time_start']/1000,timezone.utc)
        if abs((actual-utc(scene['acquisition'])).total_seconds())>1:
            raise ValueError('Scene acquisition does not match detection report')
        required = ['QA_PIXEL','SR_B2','SR_B3','SR_B4','SR_B5','SR_B6','SR_B7','ST_B10'] if name=='landsat8' else ['B4','B8','SCL']
        if not set(required).issubset(image.bandNames().getInfo()):
            raise ValueError('Scene is missing expected bands')
        if name=='landsat8' and info.get('PROCESSING_LEVEL')!='L2SP':
            raise ValueError('Landsat scene lacks a surface-temperature product')
        stack = landsat_features(image) if name=='landsat8' else sentinel_features(image)
        print('Processing '+scene['asset_id'],flush=True)
        reduced = reduce_scene(ee,stack,rows)
        if set(reduced)!=set(records):
            raise ValueError('Reduction did not return the canonical grid')
        for grid_id,row in records.items():
            values = reduced[grid_id]
            fraction = values.get('valid_fraction')
            if fraction is None:
                raise ValueError('Full-cell coverage denominator is missing')
            row[name+'_valid_fraction'] = fraction
            row[name+'_acquisition'] = scene['acquisition']
            row[name+'_image_id'] = scene['image_id']
            row[name+'_quality'] = 'sufficient_coverage' if fraction>=args.min_valid_fraction else 'insufficient_coverage'
            for field in FIELDS[name]:
                row[field] = values.get(field) if fraction>=args.min_valid_fraction else None
    values = list(records.values())
    counts = validate_records(values,set(records),selected,args.min_valid_fraction)
    metadata['weather'] = overpass_weather(ee,selected['landsat8']['acquisition']) if 'landsat8' in selected else {'status':'not_requested_no_landsat_update'}
    metadata['status'] = 'processed_for_review'
    metadata['valid_cell_counts'] = counts
    metadata['mean_full_cell_valid_fraction'] = {name:sum(r[name+'_valid_fraction'] for r in values)/len(values) for name in selected}
    if len(selected)==2:
        metadata['sensor_date_gap_days'] = abs((utc(selected['landsat8']['acquisition'])-utc(selected['sentinel2']['acquisition'])).total_seconds())/86400
    if protected_hashes()!=before:
        raise RuntimeError('Protected historical data or state changed during processing')
    write_json(output/'grid/latest_grid_features.json',values)
    write_json(output/'metadata/selected_scenes.json',selected)
    write_json(output/'summaries/latest_summary.json',{'total_cells':len(values),'valid_cell_counts':counts,
        'not_model_ready':True,'review_required':True,'historical_atlas_modified':False})
    write_json(output/'metadata/processing_status.json',metadata)
    print('Saved feature artifact for review. Historical atlas and state unchanged.',flush=True)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',default=os.environ.get('EE_PROJECT_ID'))
    parser.add_argument('--state',type=Path,default=ROOT/'automation/update_state.json')
    parser.add_argument('--detection',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=ROOT/'latest_data')
    parser.add_argument('--min-valid-fraction',type=float,default=.7)
    args = parser.parse_args()
    if not args.project:
        parser.error('Set EE_PROJECT_ID or --project')
    if not 0 < args.min_valid_fraction <= 1:
        parser.error('Minimum valid fraction must be in (0,1]')
    run(args)

if __name__=='__main__':
    main()
