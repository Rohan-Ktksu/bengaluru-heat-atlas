import ee
import pandas as pd
from pathlib import Path

project_id = input("Enter your Google Cloud Project ID: ").strip()
ee.Initialize(project=project_id)

script_folder = Path(__file__).resolve().parent
project_folder = script_folder.parent

output_file = (
    project_folder
    / "src"
    / "bengaluru_multidate_ml_dataset.csv"
)

bengaluru = ee.Geometry.Rectangle([
    77.45,
    12.80,
    77.75,
    13.15
])

years = [
    2022,
    2023,
    2024,
    2025,
    2026
]

scenes_per_season = 8

all_landsat_images = []

for year in years:

    print("\nSelecting Landsat scenes for:", year)

    seasons = [
        (
            f"{year}-01-01",
            f"{year}-03-01",
            "Jan-Feb"
        ),
        (
            f"{year}-03-01",
            f"{year}-06-01",
            "Mar-May"
        ),
        (
            f"{year}-06-01",
            f"{year}-10-01",
            "Jun-Sep"
        ),
        (
            f"{year}-10-01",
            f"{year + 1}-01-01",
            "Oct-Dec"
        )
    ]

    if year == 2026:

        seasons = [
            (
                "2026-01-01",
                "2026-03-01",
                "Jan-Feb"
            ),
            (
                "2026-03-01",
                "2026-06-01",
                "Mar-May"
            ),
            (
                "2026-06-01",
                "2026-09-01",
                "Jun-Aug"
            )
        ]

    for start_date, end_date, season_name in seasons:

            seasonal_collection = (
                ee.ImageCollection(
                    "LANDSAT/LC08/C02/T1_L2"
                )
                .filterBounds(bengaluru)
                .filterDate(
                    start_date,
                    end_date
                )
                .filter(
                    ee.Filter.lt(
                        "CLOUD_COVER",
                        20
                    )
                )
                .sort("system:time_start")
            )

            seasonal_count = (
                seasonal_collection
                .size()
                .getInfo()
            )

            print(
                year,
                season_name,
                "usable scenes:",
                seasonal_count
            )

            if seasonal_count == 0:
                continue

            number_to_take = min(
                seasonal_count,
                scenes_per_season
            )

            seasonal_list = seasonal_collection.toList(
                seasonal_count
            )

            if seasonal_count <= scenes_per_season:

                selected_indexes = range(
                    seasonal_count
                )

            else:

                step = (
                    seasonal_count - 1
                ) / (
                    scenes_per_season - 1
                )

                selected_indexes = [
                    round(i * step)
                    for i in range(
                        scenes_per_season
                    )
                ]

            for index in selected_indexes:

                image = ee.Image(
                    seasonal_list.get(index)
                )

                all_landsat_images.append(
                    image
                )

print(
    "\nTotal Landsat scenes selected:",
    len(all_landsat_images)
)

all_rows = []

for i, landsat_image in enumerate(
    all_landsat_images
):

    print(
        "\nProcessing scene:",
        i + 1,
        "of",
        len(all_landsat_images)
    )

    landsat_date = ee.Date(
        landsat_image.get(
            "system:time_start"
        )
    )

    date_string = (
        landsat_date
        .format("YYYY-MM-dd")
        .getInfo()
    )

    print(
        "Landsat date:",
        date_string
    )

    qa = landsat_image.select(
        "QA_PIXEL"
    )

    cloud_bit = 1 << 3
    cloud_shadow_bit = 1 << 4

    landsat_mask = (
        qa.bitwiseAnd(cloud_bit)
        .eq(0)
        .And(
            qa.bitwiseAnd(
                cloud_shadow_bit
            )
            .eq(0)
        )
    )

    landsat_clean = (
        landsat_image
        .updateMask(
            landsat_mask
        )
    )

    green = (
        landsat_clean
        .select("SR_B3")
        .multiply(0.0000275)
        .add(-0.2)
    )

    red = (
        landsat_clean
        .select("SR_B4")
        .multiply(0.0000275)
        .add(-0.2)
    )

    nir = (
        landsat_clean
        .select("SR_B5")
        .multiply(0.0000275)
        .add(-0.2)
    )

    swir = (
        landsat_clean
        .select("SR_B6")
        .multiply(0.0000275)
        .add(-0.2)
    )

    l_ndvi = (
        nir.subtract(red)
        .divide(
            nir.add(red)
        )
        .rename("L_NDVI")
    )

    ndbi = (
        swir.subtract(nir)
        .divide(
            swir.add(nir)
        )
        .rename("NDBI")
    )

    ndwi = (
        green.subtract(nir)
        .divide(
            green.add(nir)
        )
        .rename("NDWI")
    )

    lst = (
        landsat_clean
        .select("ST_B10")
        .multiply(0.00341802)
        .add(149.0)
        .subtract(273.15)
        .rename("LST")
    )

    sentinel_start = (
        landsat_date
        .advance(
            -7,
            "day"
        )
    )

    sentinel_end = (
        landsat_date
        .advance(
            8,
            "day"
        )
    )

    sentinel = (
        ee.ImageCollection(
            "COPERNICUS/S2_SR_HARMONIZED"
        )
        .filterBounds(bengaluru)
        .filterDate(
            sentinel_start,
            sentinel_end
        )
        .filter(
            ee.Filter.lt(
                "CLOUDY_PIXEL_PERCENTAGE",
                20
            )
        )
    )

    sentinel_count = (
        sentinel
        .size()
        .getInfo()
    )

    print(
        "Sentinel-2 images found:",
        sentinel_count
    )

    if sentinel_count == 0:

        print(
            "Skipping scene: no Sentinel-2 match."
        )

        continue

    sentinel_image = (
        sentinel
        .sort(
            "CLOUDY_PIXEL_PERCENTAGE"
        )
        .first()
    )

    sentinel_date = ee.Date(
        sentinel_image.get(
            "system:time_start"
        )
    )

    sentinel_date_string = (
        sentinel_date
        .format("YYYY-MM-dd")
        .getInfo()
    )

    print(
        "Selected Sentinel date:",
        sentinel_date_string
    )

    scl = sentinel_image.select(
        "SCL"
    )

    sentinel_mask = (
        scl.neq(3)
        .And(scl.neq(8))
        .And(scl.neq(9))
        .And(scl.neq(10))
    )

    sentinel_clean = (
        sentinel_image
        .updateMask(
            sentinel_mask
        )
    )

    s2_red = (
        sentinel_clean
        .select("B4")
    )

    s2_nir = (
        sentinel_clean
        .select("B8")
    )

    s2_ndvi = (
        s2_nir
        .subtract(s2_red)
        .divide(
            s2_nir.add(s2_red)
        )
        .rename("S2_NDVI")
    )

    era5_start = landsat_date

    era5_end = (
        landsat_date
        .advance(
            1,
            "day"
        )
    )

    era5 = (
        ee.ImageCollection(
            "ECMWF/ERA5_LAND/HOURLY"
        )
        .filterBounds(bengaluru)
        .filterDate(
            era5_start,
            era5_end
        )
    )

    era5_count = (
        era5
        .size()
        .getInfo()
    )

    print(
        "ERA5 hourly observations:",
        era5_count
    )

    if era5_count == 0:

        print(
            "Skipping scene: no ERA5 data."
        )

        continue

    weather = era5.mean()

    air_temp = (
        weather
        .select("temperature_2m")
        .subtract(273.15)
        .rename("Air_Temp")
    )

    u = weather.select(
        "u_component_of_wind_10m"
    )

    v = weather.select(
        "v_component_of_wind_10m"
    )

    wind_speed = (
        u.pow(2)
        .add(
            v.pow(2)
        )
        .sqrt()
        .rename("Wind_Speed")
    )

    dewpoint = (
        weather
        .select(
            "dewpoint_temperature_2m"
        )
        .subtract(273.15)
    )

    rh = (
        ee.Image(100)
        .multiply(
            dewpoint
            .multiply(17.625)
            .divide(
                dewpoint.add(243.04)
            )
            .exp()
            .divide(
                air_temp
                .multiply(17.625)
                .divide(
                    air_temp.add(243.04)
                )
                .exp()
            )
        )
        .rename(
            "Relative_Humidity"
        )
    )

    feature_stack = (
        l_ndvi
        .addBands(ndbi)
        .addBands(ndwi)
        .addBands(s2_ndvi)
        .addBands(air_temp)
        .addBands(wind_speed)
        .addBands(rh)
        .addBands(lst)
    )

    samples = (
        feature_stack
        .sample(
            region=bengaluru,
            scale=30,
            numPixels=750,
            seed=42 + i,
            geometries=True
        )
    )

    sample_data = samples.getInfo()

    number_of_samples = len(
        sample_data[
            "features"
        ]
    )

    print(
        "Samples returned:",
        number_of_samples
    )

    for feature in sample_data[
        "features"
    ]:

        row = (
            feature[
                "properties"
            ]
            .copy()
        )

        row[
            "date"
        ] = date_string

        row[
            "sentinel_date"
        ] = sentinel_date_string

        row[
            "year"
        ] = int(
            date_string[
                0:4
            ]
        )

        geometry = feature.get(
            "geometry"
        )

        if geometry is not None:

            coordinates = (
                geometry[
                    "coordinates"
                ]
            )

            row[
                "longitude"
            ] = coordinates[0]

            row[
                "latitude"
            ] = coordinates[1]

        all_rows.append(
            row
        )

df = pd.DataFrame(
    all_rows
)

print(
    "\nTotal rows:",
    len(df)
)

print(
    "\nColumns:"
)

print(
    df.columns.tolist()
)

if len(df) > 0:

    print(
        "\nUnique Landsat dates:"
    )

    print(
        df[
            "date"
        ]
        .nunique()
    )

    print(
        "\nSamples by year:"
    )

    print(
        df[
            "year"
        ]
        .value_counts()
        .sort_index()
    )

    print(
        "\nSamples per Landsat date:"
    )

    print(
        df[
            "date"
        ]
        .value_counts()
        .sort_index()
    )

    print(
        "\nFirst 5 rows:"
    )

    print(
        df.head()
    )

df.to_csv(
    output_file,
    index=False
)

print(
    "\nDataset saved successfully."
)

print(
    "Saved at:"
)

print(
    output_file
)