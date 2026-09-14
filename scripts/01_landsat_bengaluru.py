import ee
project_id = input("Enter your Google Cloud project ID: ").strip()
ee.Initialize(project= project_id)

print("Earth Engine connected successfully")

#Bengaluru pilot area

bengaluru = ee.Geometry.Rectangle([77.45, 12.80, 77.75, 13.15])

#Landsat 8 collection 2 level 2
landsat = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2").filterBounds(bengaluru).filterDate("2025-01-01", "2025-12-31").filter(ee.Filter.lt("CLOUD_COVER",20)))

count = landsat.size().getInfo()

print("Number of suitable Landsat Images:", count)

if count == 0:
    print("No suitable images found")
    exit()
#choose least cloudy image
image = landsat.sort("CLOUD_COVER").first()

print("Selected Landsat Product:")
print(image.get("LANDSAT_PRODUCT_ID").getInfo())

#Surface temperature band
thermal = image.select("ST_B10")

#Apply Landsat temperature scale factor
lst_kelvin = thermal.multiply(0.00341802).add(149.0)

#Convert Kelving to Celsius
lst_celsius = lst_kelvin.subtract(273.15).rename("LST_Celsius")

#calculate average LST over Bengaluru pilot area

stats = lst_celsius.reduceRegion(reducer = ee.Reducer.mean(), geometry=bengaluru, scale = 30, maxPixels = 1e9)
print("Average Land Surface Temperature:")
print(stats.getInfo())