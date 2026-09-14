import ee
import folium

project_id = input("Enter your project ID:").strip()

ee.Initialize(project=project_id)

print("Earth Engine connected successfully.")

#Bengaluru pilot area
bengaluru = ee.Geometry.Rectangle([77.45, 12.80,77.75, 13.15])

#Landsat 8 collection

landsat = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2").filterBounds(bengaluru).filterDate("2025-01-01", "2025-12-31").filter(ee.Filter.lt("CLOUD_COVER", 20)))
#convert ST_B10 to celsius

image = landsat.sort("CLOUD_COVER").first()
lst_celsius = (image.select("ST_B10").multiply(0.00341802).add(149.0).subtract(273.15).rename("LST_Celsius"))

#Visualize settings
vis_params = {"min":20, "max":45, "palette": ["blue", "cyan", "green", "yellow", "orange", "red"]}

#function to add earth engine layers to folium
def add_ee_layer(self, ee_image_object, vis_params, name):
    map_id_dict = ee.Image(ee_image_object).getMapId(vis_params)

    folium.raster_layers.TileLayer(
        tiles = map_id_dict["tile_fetcher"].url_format, 
        attr = "Google Earth Engine",
        name = name, 
        overlay = True,
        control = True
    ).add_to(self)
folium.Map.add_ee_layer = add_ee_layer

#create map
m = folium.Map(location=[12.97, 77.59], zoom_start=10)

#Add lst layer
m.add_ee_layer( lst_celsius.clip(bengaluru), vis_params, "Land Surface Temperature")

folium.LayerControl().add_to(m)

#save output

output_file = "bengaluru_lst_heatmap.html"

m.save(output_file)

print("heatmap created successfully")
print("open this file in your browser:")
print(output_file)
