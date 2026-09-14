"""Offline tests for data isolation, input provenance and numerical formula reuse."""
import copy
import tempfile
import unittest
from pathlib import Path

from latest_common import ROOT, selected_scenes, utc, output_directory, validate_records
from process_latest import landsat_features, sentinel_features

class Image:
    """Small scalar image algebra to verify formulas without Earth Engine credentials."""
    def __init__(self,value): self.bands=value if isinstance(value,dict) else {'value':value}
    @property
    def value(self): return next(iter(self.bands.values()))
    def op(self,other,fn): return Image(fn(self.value,other.value if isinstance(other,Image) else other))
    def add(self,x): return self.op(x,lambda a,b:a+b)
    def subtract(self,x): return self.op(x,lambda a,b:a-b)
    def multiply(self,x): return self.op(x,lambda a,b:a*b)
    def divide(self,x): return self.op(x,lambda a,b:a/b)
    def abs(self): return Image(abs(self.value))
    def gt(self,x): return self.op(x,lambda a,b:a>b)
    def eq(self,x): return self.op(x,lambda a,b:a==b)
    def neq(self,x): return self.op(x,lambda a,b:a!=b)
    def And(self,x): return self.op(x,lambda a,b:a and b)
    def bitwiseAnd(self,x): return self.op(x,lambda a,b:int(a)&b)
    def select(self,name): return Image({name:self.bands[name]})
    def rename(self,name): return Image({name:self.value})
    def updateMask(self,mask): return self
    def addBands(self,images):
        out=dict(self.bands)
        for image in images: out.update(image.bands)
        return Image(out)

class LatestTests(unittest.TestCase):
    def report(self):
        candidate={'image_id':'LC08_144051_20260604','usable':True,
                   'acquisition':'2026-06-04T05:00:00Z','aoi_cloud_percentage':12.73}
        return {'kind':'usable_update_detection_v2','checked_at':'2026-09-15T00:00:00Z',
                'updates_available':True,'collections':{
            'landsat8':{'collection':'LANDSAT/LC08/C02/T1_L2','update_available':True,'selected_update':candidate},
            'sentinel2':{'update_available':False,'selected_update':None}}}
    def state(self): return {'landsat8':'2026-05-03T00:00:00Z','sentinel2':'2026-05-03T00:00:00Z'}
    def test_timezone_comparison(self):
        self.assertEqual(utc('2026-05-03T05:30:00+05:30'),utc('2026-05-03T00:00:00Z'))
        with self.assertRaises(ValueError): utc('2026-05-03T00:00:00')
    def test_selected_scene_and_missing_state(self):
        self.assertEqual(set(selected_scenes(self.report(),self.state())),{'landsat8'})
        with self.assertRaises(ValueError): selected_scenes(self.report(),{})
    def test_reject_stale_or_bad_scene(self):
        for patch in [{'acquisition':'2026-05-01T00:00:00Z'}, {'usable':False},
                      {'image_id':'../../other'}, {'aoi_cloud_percentage':float('nan')},
                      {'acquisition':'2027-01-01T00:00:00Z'}]:
            report=self.report();report['collections']['landsat8']['selected_update'].update(patch)
            with self.assertRaises(ValueError): selected_scenes(report,self.state())
    def test_historical_output_rejected(self):
        for path in [ROOT/'website/data',ROOT/'src',ROOT/'latest_data/../website']:
            with self.assertRaises(ValueError): output_directory(path)
    def test_coverage_and_missingness(self):
        rows=[{'Grid_ID':'a','source_kind':'latest_conditions_observed_features',
               'sentinel2_valid_fraction':.8,'S2_NDVI':.5},
              {'Grid_ID':'b','source_kind':'latest_conditions_observed_features',
               'sentinel2_valid_fraction':.2,'S2_NDVI':None}]
        self.assertEqual(validate_records(rows,{'a','b'},{'sentinel2':{}},.7),{'sentinel2':1})
        rows[1]['S2_NDVI']=.5
        with self.assertRaises(ValueError): validate_records(rows,{'a','b'},{'sentinel2':{}},.7)
    def test_original_landsat_formulas(self):
        bands={f'SR_B{n}':raw for n,raw in zip([2,3,4,5,6,7],[10000,12000,11000,20000,17000,14000])}
        bands.update(QA_PIXEL=0,ST_B10=45000)
        out=landsat_features(Image(bands)).bands
        blue,green,red,nir,swir,swir2=[bands['SR_B'+str(n)]*.0000275-.2 for n in [2,3,4,5,6,7]]
        self.assertAlmostEqual(out['LST'],45000*.00341802+149-273.15)
        self.assertAlmostEqual(out['L_NDVI'],(nir-red)/(nir+red))
        self.assertAlmostEqual(out['NDBI'],(swir-nir)/(swir+nir))
        self.assertAlmostEqual(out['NDWI'],(green-nir)/(green+nir))
        self.assertAlmostEqual(out['Albedo'],.356*blue+.130*red+.373*nir+.085*swir+.072*swir2-.0018)
    def test_sentinel_bands(self):
        out=sentinel_features(Image({'SCL':4,'B4':1000,'B8':3000})).bands
        self.assertAlmostEqual(out['S2_NDVI'],.5)

if __name__=='__main__': unittest.main()
