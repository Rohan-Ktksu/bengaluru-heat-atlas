import ee
project_id = input("Enter your Google Cloud project ID: ").strip()

ee.Initialize(project=project_id)

#Bengaluru study area

bengaluru = ee.Geometry.Rectangle([77.45, 12.80, 77.75, 13.15])
#era5 land hourly data for one day

era5 = (ee.ImageCollection("ECMWF/ERA5_LAND/HOURLY").filterBounds(bengaluru).filterDate("2025-04-01", "2025-04-02"))

#daily mean
daily_mean = era5.mean()

#Temperature and dew point in celsius

temp_c = (daily_mean.select("temperature_2m").subtract(273.15).rename("Temp_C"))

dew_c = (daily_mean.select("dewpoint_temperature_2m").subtract(273.15).rename("Dew_C"))

#Relative Humidity calculation

rh = (ee.Image(100).multiply ((dew_c.multiply(17.625).divide(dew_c.add(243.04)).exp()).divide(temp_c.multiply(17.625).divide(temp_c.add(243.04)).exp())).rename("Relative_Humidity"))

#Bengaluru average humidity

rh_stats = rh.reduceRegion(reducer = ee.Reducer.mean(), geometry=bengaluru, scale = 10000, maxPixels= 1e9)

print("Average Bengaluru  Relative Humidity")
print(rh_stats.getInfo())