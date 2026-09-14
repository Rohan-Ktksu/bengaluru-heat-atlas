import ee
import folium

project_id = input("Enter your google cloud project id: ").strip()
ee.Initialize(project=project_id)

#Bengaluru study area
bengaluru = ee.Geometry.Rectangle([77.45, 12.80, 7.75, 13.15])

#Get LandSat  8 imgaes
landsat = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2").filterBounds(bengaluru).filterDate("2025-01-01", "2025-12-31").filter(ee.Filter.lt("CLOUD_COVER", 20)))

#select lease cloudy image
image = landsat.sort("CLOUD_COVER").first()

#get quality-assessment band
qa = image.select("QA_PIXEL")

#landsat qa_pixel bit positions

cloud_bit = 1 << 3
cloud_shadow_bit = 1 << 4

#keep pixels that are not cloud and not cloud shadow
mask = (qa.bitwiseAnd(cloud_bit).eq(0).And(qa.bitwiseAnd(cloud_shadow_bit).eq(0)))
#apply the mask
clean_image = image.updateMask(mask)

#calculate lst in celsius 
lst_celsius = (clean_image.select("ST_B10").multiply(0.00341802).add(149.0).subtract(273.15).rename("LST_Celsius"))

#Map colors
vis_params = {"min":20, "max": 45, "palette":["blue", "cyan", "green", "yellow", "orange", "red"]}

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

#create bengaluru map
m = folium.Map(location=[12.97, 77.59], zoom_start =10)

#add cleaned lst
m.add_ee_layer(lst_celsius.clip(bengaluru), vis_params, "CLOUD-Masked LST")

folium.LayerControl().add_to(m)

m.save("bengaluru_lst_cloudmasked.html")
print("Cloud-masked LST map created successfully")

