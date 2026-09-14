import ee

project_id = input("Enter your Google Cloud project ID: ").strip()
ee.Initialize(project = project_id)

#Bengaluru study area

bengaluru = ee.Geometry.Rectangle([77.45, 12.80, 77.75, 13.15])

#landsat
landsat = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2").filterBounds(bengaluru).filterDate("2025-01-01", "2025-12-31").filter(ee.Filter.lt("CLOUD_COVER", 20)))

landsat_image = landsat.sort("CLOUD_COVER").first()

landsat_date = ee.Date(landsat_image.get("system:time_start"))

print("Landsat date:")
print(landsat_date.format("YYYY-MM-dd").getInfo())
# LANDSAT CLOUD MASK

qa = landsat_image.select("QA_PIXEL")

cloud_bit = 1 << 3
cloud_shadow_bit = 1 << 4

landsat_mask = (qa.bitwiseAnd(cloud_bit).eq(0).And(qa.bitwiseAnd(cloud_shadow_bit).eq(0)))

landsat_clean = landsat_image.updateMask(landsat_mask)

#landsat reflectance bands

green = (landsat_clean.select("SR_B3").multiply(0.0000275).add(-0.2))
red = (landsat_clean.select("SR_B4").multiply(0.0000275).add(-0.2))
nir = (landsat_clean.select("SR_B5").multiply(0.0000275).add(-0.2))
swir = (landsat_clean.select("SR_B6").multiply(0.0000275).add(-0.2))
#landsat ndvi

l_ndvi = (nir.subtract(red).divide(nir.add(red)).rename("L_NDVI"))
#ndbi
ndbi = (swir.subtract(nir).divide(swir.add(nir)).rename("NDBI"))
#ndwi
ndwi = (green.subtract(nir).divide(green.add(nir)).rename("NDWI"))

#LST

lst = (landsat_clean.select("ST_B10").multiply(0.00341802).add(149.0).subtract(273.15).rename("LST"))

#Match sentinel-2 to landsat date

sentinel_start = landsat_date.advance(-5, "day")
sentinel_end =  landsat_date.advance(5, "day")

sentinel = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(bengaluru).filterDate(sentinel_start, sentinel_end).filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20)))

print("Sentinel-2 images found:")
print(sentinel.size().getInfo())

sentinel_image = (sentinel.sort("CLOUDY_PIXEL_PERCENTAGE").first())
sentinel_date = ee.Date(sentinel_image.get("system:time_start"))

print("Selected Sentinel-2 date:")

print(sentinel_date.format("YYYY-MM-dd").getInfo())

#sentinel cloud mask

scl = sentinel_image.select("SCL")

sentinel_mask = (scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10)))

sentinel_clean = sentinel_image.updateMask(sentinel_mask)

#sentinel ndvi

s2_red = sentinel_clean.select("B4")
s2_nir = sentinel_clean.select("B8")

s2_ndvi = (s2_nir.subtract(s2_red).divide(s2_nir.add(s2_red)).rename("S2_NDVI"))

#ERA5 for Landsat date

era5_start = landsat_date
era5_end = landsat_date.advance(1, "day")

era5 = (ee.ImageCollection("ECMWF/ERA5_LAND/HOURLY").filterBounds(bengaluru).filterDate(era5_start, era5_end))

weather = era5.mean()

#Air Temperature

air_temp = (weather.select("temperature_2m").subtract(273.15).rename("Air_Temp"))

#wind speed

u = weather.select("u_component_of_wind_10m")
v = weather.select("v_component_of_wind_10m")

wind_speed = (u.pow(2).add(v.pow(2)).sqrt().rename("Wind_Speed"))

#relative humidity

dewpoint = (weather.select("dewpoint_temperature_2m").subtract(273.15))

rh = (ee.Image(100).multiply(dewpoint.multiply(17.625).divide(dewpoint.add(243.04)).exp().divide(air_temp.multiply(17.625).divide(air_temp.add(243.04)).exp())).rename("Relative_Humidity"))

#final feature stack

feature_stack = (l_ndvi.addBands(ndbi).addBands(ndwi).addBands(s2_ndvi).addBands(air_temp).addBands(wind_speed).addBands(rh).addBands(lst))

print("\n Final feature bands:")
print(feature_stack.bandNames().getInfo())