import ee
project_id = input("Enter your google cloud project ID:").strip()
ee.Initialize(project=project_id)

#bengaluru study area
bengaluru = ee.Geometry.Rectangle([77.45, 12.80, 77.75, 13.15])

#get landsat image

landsat = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2").filterBounds(bengaluru).filterDate("2025-01-01", "2025-12-31").filter(ee.Filter.lt("CLOUD_COVER", 20)))

landsat_image = landsat.sort("CLOUD_COVER").first()

landsat_date = ee.Date(landsat_image.get("system:time_start"))

print("Landsat date:")
print(landsat_date.format("YYYY-MM-dd").getInfo())

#create sentinel search window

sentinel_start = landsat_date.advance(-5, "day")
sentinel_end = landsat_date.advance(5, "day")

#get sentinel 2

sentinel = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(bengaluru).filterDate(sentinel_start, sentinel_end).filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20)))

print("sentinel-2 images found")
print(sentinel.size().getInfo())

#select least cloudy sentinel image

sentinel_image = (sentinel.sort("CLOUD_PIXEL_PERCENTAGE").first())

sentinel_date = ee.Date(sentinel_image.get("system:time_start"))
print("Selected Sentinel-2 date:")
print(sentinel_date.format("YYYY-MM-dd").getInfo())

#cloud mask sentinel-2
scl = sentinel_image.select("SCL")

sentinel_mask = (scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10)))

sentinel_clean = sentinel_image.updateMask(sentinel_mask)

#sentinel ndvi

red = sentinel_clean.select("B4")
nir = sentinel_clean.select("B8")

s2_ndvi = (nir.subtract(red).divide(nir.add(red)).rename("S2_NDVI"))

print("Sentinel NDVI band created:")
print(s2_ndvi.bandNames().getInfo())

