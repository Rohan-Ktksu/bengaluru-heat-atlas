import ee
project_id = input("Enter your google cloud project ID: ").strip()
ee.Initialize(project = project_id)

#Bengaluru study area
bengaluru = ee.Geometry.Rectangle([77.45, 12.80, 77.75, 13.15])

#get landsat image

landsat = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2").filterBounds(bengaluru).filterDate("2025-01-01", "2025-12-31").filter(ee.Filter.lt("CLOUD_COVER", 20)))

#select least cloudy image
image = landsat.sort("CLOUD_COVER").first()
#get landsat acquisition date

landsat_date = ee.Date(image.get("system:time_start"))

print("Landsat acquisition date:")
print(landsat_date.format("YYYY-MM-dd").getInfo())

#create start and end date

start_date = landsat_date

end_date = landsat_date.advance(1, "day")

#get era5 on same date

era5  = (ee.ImageCollection("ECMWF/ERA5_LAND/HOURLY").filterBounds(bengaluru).filterDate(start_date, end_date))

print("ERA5 hourly observation found:")
print(era5.size().getInfo())

#average hourly weather for that day

weather = era5.mean()

#air temperature

air_temp = (weather.select("temperature_2m").subtract(273.15).rename("Air_Temp_C"))

# dew point

dewpoint = (weather.select("dewpoint_temperature_2m").subtract(273.15).rename("Dewpoint_C"))

#windspeed

u = weather.select("u_component_of_wind_10m")
v = weather.select("v_component_of_wind_10m")

wind_speed = (u.pow(2).add(v.pow(2)).sqrt().rename("Wind_Speed"))

#relative humidity

rh = (ee.Image(100).multiply(dewpoint.multiply(17.625).divide(dewpoint.add(243.05)).exp().divide(air_temp.multiply(17.625).divide(air_temp.add(243.04)).exp())).rename("Relative_Humidity"))

#calculate bengaluru averages

weather_features = (air_temp.addBands(wind_speed).addBands(rh))

stats = weather_features.reduceRegion(reducer=ee.Reducer.mean(), geometry=bengaluru, scale = 10000,maxPixels = 1e9 )

print("\nWeather on Landsat acquisition date:")
print(stats.getInfo())