import ee
import folium

project_id = input("Enter your Cloud project ID:").strip()
ee.Initialize(project=project_id)

#Bengaluru study area

bengaluru = ee.Geometry.Rectangle([77.45, 12.80, 77.75, 13.15])

#sentinal-2 surface reflectance collection

sentinel = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(bengaluru).filterDate("2025-01-01", "2025-12-31").filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20)))

print("Number of Sentinel-2 images:")
print(sentinel.size().getInfo())

#select least-cloud image
image = sentinel.sort("CLOUDY_PIXEL_PERCENTAGE").first()

#sentinel-2 cloud mask using SCL band

scl = image.select("SCL")

mask = (scl.neq(3) #cloud shadow
        .And(scl.neq(8))#medium probability cloud
        .And(scl.neq(9))#high probability cloud
        .And(scl.neq(10)) #cirrus
        )
clean_image = image.updateMask(mask)

#sentinel-2 bands
red = clean_image.select("B4")
nir = clean_image.select("B8")

#calculate NDVI
ndvi = (nir.subtract(red).divide(nir.add(red)).rename("NDVI"))

#visualization
ndvi_vis = {
    "min": -1,
    "max": 1, 
    "palette": ["brown", "yellow", "lightgreen", "green", "darkgreen"]
}

def add_ee_layer(self, ee_image, vis_params ,name):
    map_id = ee.Image(ee_image).getMapId(vis_params)

    folium.raster_layers.TileLayer(
        tiles= map_id["tile_fetcher"].url_format,
        attr = "Google Earth Engine",
        name = name,
        overlay = True, 
        control = True
    ).add_to(self)
folium.Map.add_ee_layer = add_ee_layer

#create map
m = folium.Map(location = [12.97, 77.59], zoom_start = 10)
m.add_ee_layer(ndvi.clip(bengaluru), ndvi_vis, "Sentinel-2 NDVI")

folium.LayerControl().add_to(m)
m.save("bengaluru_sentinel2_ndvi.html")
print("Sentinel-2 NDVI map created successfully.")

