import ee
import folium

project_id = input("Enter your Google cloud project ID: ").strip()
ee.Initialize(project=project_id)

#bengaluru study area

bengaluru = ee.Geometry.Rectangle([77.45, 12.80, 77.75, 13.15])

landsat = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2").filterBounds(bengaluru).filterDate("2025-01-01", "2025-12-31").filter(ee.Filter.lt("CLOUD_COVER", 20)))

#select least_cloudy image

image = landsat.sort("CLOUD_COVER").first()

#cloud masking

qa = image.select("QA_PIXEL")
cloud_bit = 1 << 3
cloud_shadow_bit = 1 << 4

mask = (qa.bitwiseAnd(cloud_bit).eq(0).And(qa.bitwiseAnd(cloud_shadow_bit).eq(0)))

clean_image = image.updateMask(mask)

#scale reflectance bands

green = (clean_image.select("SR_B3").multiply(0.0000275).add(-0.2))
nir = (clean_image.select("SR_B5").multiply(0.0000275).add(-0.2))

#calculate NDWI

ndwi = (green.subtract(nir).divide(green.add(nir)).rename("NDWI"))

#visualization
ndwi_vis = {
    "min": -1,
    "max": 1,
    "palette": ["brown", "yellow", "white", "cyan", "blue"]
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
m = folium.Map(location = [12.97, 77.59], zoom_start = 10)

m.add_ee_layer(ndwi.clip(bengaluru), ndwi_vis, "Bengaluru NDWI")

folium.LayerControl().add_to(m)

m.save("bengaluru_ndwi.html")
print("NDWI map created successfully.")

