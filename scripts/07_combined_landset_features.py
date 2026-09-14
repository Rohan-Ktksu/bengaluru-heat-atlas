import ee
import folium
project_id = input("Enter your google cloud project ID: ").strip()

ee.Initialize(project = project_id)

#bengaluru study area

bengaluru = ee.Geometry.Rectangle([77.45, 12.80,77.75, 13.15 ])

#landsat 8 collection

landsat = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2").filterBounds(bengaluru).filterDate("2025-01-01", "2025-12-31").filter(ee.Filter.lt("CLOUD_COVER", 20)))

#select least cloudy image

image = landsat.sort("CLOUD_COVER").first()

#cloud masking

qa = image.select("QA_PIXEL")

cloud_bit = 1 << 3
cloud_shadow_bit = 1 << 4

mask = (qa.bitwiseAnd(cloud_bit).eq(0).And(qa.bitwiseAnd(cloud_shadow_bit).eq(0)))

clean_image = image.updateMask(mask)

#scale reflectance bands

green = (clean_image.select("SR_B3").multiply(0.0000275).add(-0.2))

red = (clean_image.select("SR_B4").multiply(0.0000275).add(-0.2))

nir = (clean_image.select("SR_B5").multiply(0.0000275).add(-0.2))

swir = (clean_image.select("SR_B6").multiply(0.0000275).add(-0.2))

#lst
lst = (clean_image.select("ST_B10").multiply(0.00341802).add(149.0).subtract(273.15).rename("LST"))

#ndvi
ndvi = (nir.subtract(red).divide(nir.add(red)).rename("NDVI"))

#ndbi
ndbi = (swir.subtract(nir).divide(swir.add(nir)).rename("NDBI"))

#ndwi
ndwi = (green.subtract(swir).divide(green.add(swir)).rename("NDWI"))

#visualize settings

lst_vis = {
    "min":20,
    "max": 45,
    "palette": ["blue", "cyan", "green", "yellow", "orange", "red"]

}

ndvi_vis = {
    "min": -1,
    "max": 1,
    "palette": ["brown", "yellow", "lightgreen", "green", "darkgreen"]
}
ndbi_vis = {
    "min": -1,
    "max": 1,
    "palette": ["green", "yellow", "orange", "red"]

}

ndwi_vis = {
    "min": -1,
    "max": 1,
    "palette": ["brown", "yellow", "white", "cyan", "blue"]
}
#earth engine to folium helper
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

m.add_ee_layer(lst.clip(bengaluru), lst_vis, "LST")
m.add_ee_layer(ndvi.clip(bengaluru), ndvi_vis, "NDVI")
m.add_ee_layer(ndbi.clip(bengaluru), ndbi_vis, "NDBI")
m.add_ee_layer(ndwi.clip(bengaluru), ndwi_vis, "NDWI")

folium.LayerControl().add_to(m)

m.save("bengaluru_combined_features.html")

print("Combined Landsat feature map created successfully.")
