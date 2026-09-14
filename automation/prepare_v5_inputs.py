"""Pair satellite acquisitions and prepare all 25 V5 inputs as a review artifact."""
import argparse
from datetime import datetime,timezone,timedelta,date
import math
import os
from pathlib import Path
import statistics

from latest_common import ROOT, load_grid, output_directory, read_json, protected_hashes, write_json
from process_latest import (landsat_features,sentinel_features,feature_collection,reduce_scene,overpass_weather)
from v5_schema import FEATURES,SPATIAL,WEATHER,baseline_cutoff,paired,invalid_features

def catalog_records(ee,collection,fields,limit=10):
    limited=collection.limit(limit)
    array=limited.toList(limit)
    return ee.List.sequence(0,limited.size().subtract(1)).map(
        lambda i:ee.Image(array.get(i)).toDictionary(fields)).getInfo() if limited.size().getInfo() else []

def acquisition(record):
    return datetime.fromtimestamp(record['system:time_start']/1000,timezone.utc).isoformat()

def joint_coverage(ee,landsat,sentinel,region):
    mask=landsat.mask().reduce(ee.Reducer.min()).And(sentinel.mask().reduce(ee.Reducer.min()))
    return mask.unmask(0,sameFootprint=False).rename('valid').reduceRegion(
        reducer=ee.Reducer.mean(),geometry=region,scale=30,crs='EPSG:32643',
        maxPixels=1e8,tileScale=4).get('valid').getInfo()

def find_pair(ee,rows,state,now,minimum=.8,validation_date=None):
    region=feature_collection(ee,rows).geometry()
    landsat_id='LANDSAT/LC08/C02/T1_L2'
    sentinel_id='COPERNICUS/S2_SR_HARMONIZED'
    start=baseline_cutoff(state['landsat8']).isoformat()
    end=now.isoformat()
    if validation_date:
        start=validation_date
        end=(date.fromisoformat(validation_date)+timedelta(days=1)).isoformat()
    collection=(ee.ImageCollection(landsat_id).filterBounds(region).filterDate(start,end)
        .filter(ee.Filter.eq('PROCESSING_LEVEL','L2SP')).filter(ee.Filter.lt('CLOUD_COVER',20))
        .sort('system:time_start',False))
    anchors=catalog_records(ee,collection,['system:index','system:time_start','CLOUD_COVER'])
    audit=[]
    for anchor in anchors:
        stamp=acquisition(anchor)
        land=ee.Image(landsat_id+'/'+anchor['system:index'])
        land_features=landsat_features(land)
        when=ee.Date(stamp)
        candidates=(ee.ImageCollection(sentinel_id).filterBounds(region)
            .filterDate(when.advance(-5,'day'),when.advance(5,'day'))
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE',20)).sort('CLOUDY_PIXEL_PERCENTAGE'))
        records=catalog_records(ee,candidates,['system:index','system:time_start','CLOUDY_PIXEL_PERCENTAGE'])
        item={'landsat_image_id':anchor['system:index'],'landsat_acquisition':stamp,
              'sentinel_candidate_count_checked':len(records),'candidates':[]}
        audit.append(item)
        for candidate in records:
            s2stamp=acquisition(candidate)
            if not paired(stamp,s2stamp): raise ValueError('Pair outside historical temporal window')
            s2=ee.Image(sentinel_id+'/'+candidate['system:index'])
            s2_features=sentinel_features(s2)
            fraction=joint_coverage(ee,land_features,s2_features,region)
            accepted=fraction is not None and fraction>=minimum
            item['candidates'].append({'sentinel_image_id':candidate['system:index'],
                'sentinel_acquisition':s2stamp,'joint_full_aoi_valid_fraction':fraction,'accepted':accepted})
            if accepted:
                return {'landsat_asset':landsat_id+'/'+anchor['system:index'],
                        'landsat_acquisition':stamp,'sentinel_asset':sentinel_id+'/'+candidate['system:index'],
                        'sentinel_acquisition':s2stamp,'joint_full_aoi_valid_fraction':fraction},audit
    return None,audit

def weather_stack(ee,stamp,region):
    """Exact temporal windows/band transforms from script 22; verify complete hours."""
    t=ee.Date(stamp)
    base=ee.ImageCollection('ECMWF/ERA5_LAND/HOURLY').filterBounds(region)
    windows={'forward_1day':base.filterDate(t,t.advance(1,'day')),
             'previous_1day':base.filterDate(t.advance(-1,'day'),t),
             'previous_3day':base.filterDate(t.advance(-3,'day'),t),
             'previous_7day':base.filterDate(t.advance(-7,'day'),t),
             'cloud_previous_1day':ee.ImageCollection('ECMWF/ERA5/HOURLY').filterBounds(region).filterDate(t.advance(-1,'day'),t)}
    expected={'forward_1day':24,'previous_1day':24,'previous_3day':72,'previous_7day':168,'cloud_previous_1day':24}
    provenance={}
    for name,collection in windows.items():
        times=sorted(collection.aggregate_array('system:time_start').getInfo())
        if len(times)!=expected[name] or len(set(times))!=len(times) or any(b-a!=3600000 for a,b in zip(times,times[1:])):
            raise ValueError('Incomplete hourly weather window: '+name)
        provenance[name]={'count':len(times),'first_ms':times[0],'last_ms':times[-1]}
    weather=windows['forward_1day'].mean()
    temp=weather.select('temperature_2m').subtract(273.15)
    dew=weather.select('dewpoint_temperature_2m').subtract(273.15)
    rh=dew.multiply(17.625).divide(dew.add(243.04)).exp().divide(temp.multiply(17.625).divide(temp.add(243.04)).exp()).multiply(100)
    wind=weather.select('u_component_of_wind_10m').pow(2).add(weather.select('v_component_of_wind_10m').pow(2)).sqrt()
    stack=temp.rename('Air_Temp').addBands([wind.rename('Wind_Speed'),rh.rename('Relative_Humidity'),
        weather.select('volumetric_soil_water_layer_1').rename('Soil_Moisture')])
    for days,label in [(1,'Daily_Precipitation'),(3,'Precip_3Day'),(7,'Precip_7Day')]:
        stack=stack.addBands(windows[f'previous_{days}day'].select('total_precipitation_hourly').sum().multiply(1000).rename(label))
    stack=stack.addBands([
        windows['previous_1day'].select('surface_solar_radiation_downwards_hourly').sum().divide(1e6).rename('Solar_Radiation'),
        windows['cloud_previous_1day'].select('total_cloud_cover').mean().multiply(100).rename('Cloud_Cover')])
    for days in [3,7]:
        stack=stack.addBands(windows[f'previous_{days}day'].select('temperature_2m').mean().subtract(273.15).rename(f'Air_Temp_{days}Day'))
    return stack,provenance

def static_dynamic_features(ee,stamp,region):
    when=ee.Date(stamp)
    dw=(ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1').filterBounds(region)
        .filterDate(when.advance(-5,'day'),when.advance(5,'day')))
    dw_count=dw.size().getInfo()
    if not dw_count: raise ValueError('No Dynamic World imagery in the Landsat +/-5-day window')
    ids=dw.aggregate_array('system:index').getInfo()
    elevation=ee.Image('USGS/SRTMGL1_003').select('elevation').rename('Elevation')
    water=ee.Image('JRC/GSW1_4/GlobalSurfaceWater').select('occurrence').unmask(0).gte(50)
    water=water.reproject(ee.Projection('EPSG:32643').atScale(100))
    distance=water.fastDistanceTransform(neighborhood=250,units='pixels',metric='squared_euclidean').sqrt().multiply(100).min(25000).rename('Distance_To_Water')
    return elevation.addBands([distance,dw.select('built').mean().rename('Built_Probability'),
        dw.select('trees').mean().rename('Tree_Probability')]),ids

def prepare(args):
    output=output_directory(args.output)
    before=protected_hashes()
    state=read_json(ROOT/'automation/update_state.json')
    rows=load_grid()
    now=datetime.now(timezone.utc)
    import ee
    import google.auth
    credentials,_=google.auth.default(scopes=['https://www.googleapis.com/auth/earthengine','https://www.googleapis.com/auth/cloud-platform'])
    ee.Initialize(credentials=credentials,project=args.project)
    pair,audit=find_pair(ee,rows,state,now,validation_date=args.validation_date)
    status={'schema_version':1,'generated_at':now.isoformat(),'feature_order':FEATURES,
        'historical_atlas_modified':False,'state_advanced':False,'ml_applied':False,
        'protected_sha256':before,'pair':pair,'candidate_audit':audit,
        'ready_for_publication':False,'minimum_cell_valid_fraction':.7,
        'minimum_joint_aoi_valid_fraction':.8}
    status['run_kind']='historical_validation_replay' if args.validation_date else 'new_acquisition_review'
    status['validation_date']=args.validation_date
    write_json(output/'metadata/pairing.json',status)
    if not pair:
        status.update(status='no_compatible_pair',eligible_cell_count=0)
        write_json(output/'metadata/model_input_status.json',status)
        print('No compatible new pair passed the date/cloud/coverage gates. No inference performed.')
        return
    land=landsat_features(ee.Image(pair['landsat_asset']))
    sentinel=sentinel_features(ee.Image(pair['sentinel_asset']))
    region=feature_collection(ee,rows).geometry()
    extra,dw_ids=static_dynamic_features(ee,pair['landsat_acquisition'],region)
    spatial=land.addBands(sentinel).addBands(extra)
    reduced=reduce_scene(ee,spatial,rows)
    weather,windows=weather_stack(ee,pair['landsat_acquisition'],region)
    # Scripts 22/37 used median of spatially sampled weather values. Use a fixed
    # seed for new dates, retaining date-level summaries rather than 1 km weather.
    sample_region=ee.Geometry.Rectangle([77.45,12.80,77.75,13.15])
    mask=spatial.mask().reduce(ee.Reducer.min())
    samples=weather.updateMask(mask).sample(region=sample_region,scale=30,numPixels=750,seed=42,geometries=False).getInfo()['features']
    if not samples: raise ValueError('No valid meteorological samples')
    daily={field:statistics.median([r['properties'][field] for r in samples]) for field in WEATHER if not field.startswith('Overpass_')}
    overpass=overpass_weather(ee,pair['landsat_acquisition'])
    if overpass['status']!='available': raise ValueError('Overpass weather unavailable')
    date_weather={**daily,**overpass['values']}
    records=[]
    for grid in rows:
        item=reduced[grid['Grid_ID']]
        fraction=item['valid_fraction']
        record={'Grid_ID':grid['Grid_ID'],'source_kind':'paired_v5_model_inputs',
            'valid_fraction':fraction,'landsat_acquisition':pair['landsat_acquisition'],
            'sentinel_acquisition':pair['sentinel_acquisition'],
            'observed_LST':item.get('LST') if fraction>=.7 else None}
        record.update({field:item.get(field) if fraction>=.7 else None for field in SPATIAL})
        record.update(date_weather)
        invalid=invalid_features(record)
        record['eligible_for_inference']=fraction>=.7 and not invalid
        record['invalid_or_missing_features']=invalid
        records.append(record)
    eligible=sum(r['eligible_for_inference'] for r in records)
    if not eligible: raise ValueError('No complete, in-range cells for V5')
    status.update(status='inputs_ready_for_inference_review',total_cells=len(records),eligible_cell_count=eligible,
        weather_windows=windows,weather_sample_count=len(samples),weather_sample_seed=42,
        dynamic_world_image_ids=dw_ids,overpass_weather=overpass,
        imputation='none; only complete adequately covered cells are eligible',
        temporal_lookahead='Air_Temp/Wind/RH/Soil use 24 hours after acquisition, matching script 22; retrospective only')
    if protected_hashes()!=before: raise RuntimeError('Protected data changed')
    write_json(output/'grid/v5_model_inputs.json',records)
    write_json(output/'metadata/model_input_status.json',status)
    print(f'Prepared {eligible}/{len(records)} complete V5 input rows. Publication remains disabled.')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',default=os.environ.get('EE_PROJECT_ID'))
    parser.add_argument('--output',type=Path,default=ROOT/'latest_data/v5-inputs')
    parser.add_argument('--validation-date',choices=['2026-01-27','2026-02-12','2026-02-28',
        '2026-03-16','2026-04-01','2026-04-17','2026-05-03'],default=None,
        help='Explicit historical replay for testing; never a new-data update')
    args=parser.parse_args()
    if not args.project: parser.error('EE_PROJECT_ID is required')
    prepare(args)

if __name__=='__main__': main()
