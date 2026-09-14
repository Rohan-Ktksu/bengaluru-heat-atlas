import ee
import folium

project_id = input("Enter your Google Cloud project ID:").strip()
ee.Initialize(project=project_id)
#bengaluru study area

bengaluru = ee.Geometry.Rectangle([77.45, 12.80, 77.75, 13.15])

#era5-land hourly data
era5 = (ee.ImageCollection("ECMWF/ERA5_LAND/HOURLY").filterBounds(bengaluru).filterDate("2025-04-01", "2025-04-02"))

print("Number of ERA5-land hourly images:")
print(era5.size().getInfo())

#calculate daily mean
daily_mean = era5.mean()

#Air temperature at 2 metres
air_temp = (daily_mean.select("temperature_2m").subtract(273.15).rename("Air_Temperature_C"))

#dew_point temperature

dewpoint = (daily_mean.select("dewpoint_temperature_2m").subtract(273.15).rename("Dewpoint_C"))

#wind components
u_wind = daily_mean.select("u_component_of_wind_10m")
v_wind = daily_mean.select("v_component_of_wind_10m")

#wind speed = sqrt(u^2 + v^2)
wind_speed = (u_wind.pow(2).add(v_wind.pow(2)).sqrt().rename("Wind_speed"))

#calculate Bengaluru averages
temp_stats = air_temp.reduceRegion(reducer= ee.Reducer.mean(), geometry = bengaluru, scale = 10000, maxPixels = 1e9)
wind_stats = wind_speed.reduceRegion(reducer= ee.Reducer.mean(), geometry= bengaluru, scale = 10000, maxPixels = 1e9)
print("Average Bengaluru air temperature:")
print(temp_stats.getInfo())
print("Average Bengaluru Wind Speed:")
print(wind_stats.getInfo())
#visualization
temp_vis = {
    "min":20,
    "max": 45,
    "palette": ["blue", "cyan", "green", "yellow","orange", "red"]
}

wind_vis = {
    "min": 0,
    "max": 10,
    "palette": ["white", "lightblue", "blue", "purple"]
}

def add_ee_layer(self, ee_image, vis_params, name):
    map_id = ee.Image(ee_image).getMapId(vis_params)

    folium.raster_layers.TileLayer(
        tiles = map_id["tile_fetcher"].url_format,
        attr = "Google Earth Engine", 
        name = name,
        overlay = True,
        control = True
    ).add_to(self)

folium.Map.add_ee_layer = add_ee_layer

#create map
m = folium.Map(location = [12.97, 77.59], zoom_start = 9)

m.add_ee_layer(air_temp.clip(bengaluru),temp_vis, "ERA5, Air Temperature")
m.add_ee_layer(wind_speed.clip(bengaluru), wind_vis, "ERA5 Wind Speed")

folium.LayerControl().add_to(m)

m.save("bengaluru_era5_weather.html")

print("ERA5-Land weahter map created successfully")