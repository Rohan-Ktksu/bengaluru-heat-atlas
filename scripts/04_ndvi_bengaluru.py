import ee
import folium

project_id = input("Enter your google cloud project id:").strip()
ee.Initialize(project=project_id)

#Bengaluru study area
bengaluru = ee.Geometry.Rectangle([77.45, 12.80, 77.75, 13.15])

landsat = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2").filterBounds(bengaluru).filterDate("2025-01-01", "2025-12-31").filter(ee.Filter.lt("CLOUD_COVER",20)))
#select least cloudy image
image = landsat.sort("CLOUD_COVER").first()

3#cloud mask
qa = image.select("QA_PIXEL")

cloud_bit = 1 << 3
cloud_shadow_bit = 1 << 4

mask  = (qa.bitwiseAnd(cloud_bit).eq(0).And(qa.bitwiseAnd(cloud_shadow_bit).eq(0)))

clean_image = image.updateMask(mask)

red = (clean_image.select("SR_B4").multiply(0.0000275).add(-0.2))

nir = (clean_image.select("SR_B5").multiply(0.0000275).add(-0.2))
#calculate ndvi

ndvi = (nir.subtract(red).divide(nir.add(red).rename("NDVI")))

#visualization

ndvi_vis = {
    "min": -1,
    "max": 1,
    "palette": ["blue", "white", "yellow", "lightgreen", "green", "darkgreen"]
}

def add_ee_layer(self, ee_image, vis_params, name):
    map_id = ee.Image(ee_image).getMapId(vis_params)

    folium.raster_layers.TileLayer(
        tiles = map_id["tile_fetcher"].url_format,
        attr = "Google Earth Engine", 
        name = name, 
        overlay= True,
        control = True
    ).add_to(self)

folium.Map.add_ee_layer = add_ee_layer

#create map
m = folium.Map(location = [12.97, 77.59], zoom_start = 10)

m.add_ee_layer(ndvi.clip(bengaluru), ndvi_vis, "Bengaluru NDVI")

folium.LayerControl().add_to(m)
m.save("bengaluru_ndvi.html")
print("NDVI map created successfully.")
