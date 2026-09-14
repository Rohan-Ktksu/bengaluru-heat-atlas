"""Frozen V5 input contract, taken from script 30 (no scaler or imputer)."""
import math
from datetime import timedelta
from latest_common import utc

FEATURES = ['L_NDVI','NDBI','NDWI','S2_NDVI','Air_Temp','Wind_Speed',
    'Relative_Humidity','Soil_Moisture','Daily_Precipitation','Precip_3Day',
    'Precip_7Day','Solar_Radiation','Cloud_Cover','Air_Temp_3Day','Air_Temp_7Day',
    'Elevation','Built_Probability','Tree_Probability','Albedo','Distance_To_Water',
    'Overpass_Air_Temp','Overpass_Relative_Humidity','Overpass_Wind_Speed',
    'Overpass_Solar_Radiation','Overpass_Cloud_Cover']
SPATIAL = ['L_NDVI','NDBI','NDWI','S2_NDVI','Elevation','Built_Probability',
           'Tree_Probability','Albedo','Distance_To_Water']
WEATHER = [name for name in FEATURES if name not in SPATIAL]
RANGES = {name:(-60,60) for name in FEATURES if 'Air_Temp' in name}
RANGES.update({name:(-1,1) for name in ['L_NDVI','NDBI','NDWI','S2_NDVI']})
RANGES.update({name:(0,1) for name in ['Soil_Moisture','Built_Probability','Tree_Probability','Albedo']})
RANGES.update({name:(0,100) for name in ['Relative_Humidity','Cloud_Cover','Overpass_Relative_Humidity','Overpass_Cloud_Cover']})
RANGES.update({'Elevation':(-500,9000),'Distance_To_Water':(0,25000),
    'Wind_Speed':(0,100),'Overpass_Wind_Speed':(0,100),
    'Daily_Precipitation':(0,1000),'Precip_3Day':(0,3000),'Precip_7Day':(0,7000),
    'Solar_Radiation':(0,60),'Overpass_Solar_Radiation':(0,6)})

def baseline_cutoff(value):
    date=utc(value)
    # Initial state is a processed study DATE at midnight, not a processed scene time.
    return date+timedelta(days=1) if date.time().isoformat()=='00:00:00' else date+timedelta(milliseconds=1)

def paired(landsat, sentinel):
    gap=(utc(sentinel)-utc(landsat)).total_seconds()/86400
    return -5 <= gap < 5  # Earth Engine filterDate has an exclusive upper bound.

def invalid_features(row):
    bad=[]
    for key in FEATURES:
        value=row.get(key)
        lo,hi=RANGES[key]
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not lo<=value<=hi:
            bad.append(key)
    return bad

def inference_rows(rows):
    accepted=[row for row in rows if row.get('eligible_for_inference') is True]
    if not accepted:
        raise ValueError('No cells meet the paired-input checks')
    for row in accepted:
        if invalid_features(row): raise ValueError('Invalid model input '+row['Grid_ID'])
    return accepted
