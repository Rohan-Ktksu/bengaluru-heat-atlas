import ee
import pandas as pd
from pathlib import Path

project_id = input("Enter your Google Cloud Project ID: ").strip()
ee.Initialize(project=project_id)

script_folder = Path(__file__).resolve().parent
project_folder = script_folder.parent

input_file = (
    project_folder
    / "src"
    / "bengaluru_multidate_v4_spatial_ml_dataset.csv"
)

output_file = (
    project_folder
    / "src"
    / "bengaluru_multidate_v5_overpass_ml_dataset.csv"
)

df = pd.read_csv(input_file)

print("V4 dataset loaded.")

print("Total rows:")
print(len(df))

print("Unique dates:")
print(df["date"].nunique())

df["date"] = pd.to_datetime(df["date"])

unique_dates = (
    df["date"]
    .drop_duplicates()
    .sort_values()
)

overpass_rows = []

bengaluru = ee.Geometry.Rectangle([
    77.45,
    12.80,
    77.75,
    13.15
])

for index, date_value in enumerate(unique_dates):

    date_string = date_value.strftime(
        "%Y-%m-%d"
    )

    print(
        "\nProcessing date:",
        date_string,
        "(",
        index + 1,
        "of",
        len(unique_dates),
        ")"
    )

    day_start = ee.Date(
        date_string
    )

    day_end = day_start.advance(
        1,
        "day"
    )

    landsat_collection = (
        ee.ImageCollection(
            "LANDSAT/LC08/C02/T1_L2"
        )
        .filterBounds(
            bengaluru
        )
        .filterDate(
            day_start,
            day_end
        )
        .sort(
            "CLOUD_COVER"
        )
    )

    landsat_count = (
        landsat_collection
        .size()
        .getInfo()
    )

    if landsat_count == 0:

        print(
            "No Landsat image found for date."
        )

        continue

    landsat_image = ee.Image(
        landsat_collection.first()
    )

    landsat_time = ee.Date(
        landsat_image.get(
            "system:time_start"
        )
    )

    acquisition_time = (
        landsat_time
        .format(
            "YYYY-MM-dd HH:mm:ss"
        )
        .getInfo()
    )

    print(
        "Landsat acquisition time:",
        acquisition_time
    )

    window_start = (
        landsat_time
        .advance(
            -90,
            "minute"
        )
    )

    window_end = (
        landsat_time
        .advance(
            90,
            "minute"
        )
    )

    era5_land = (
        ee.ImageCollection(
            "ECMWF/ERA5_LAND/HOURLY"
        )
        .filterBounds(
            bengaluru
        )
        .filterDate(
            window_start,
            window_end
        )
    )

    era5_land_count = (
        era5_land
        .size()
        .getInfo()
    )

    print(
        "ERA5-Land hourly images:",
        era5_land_count
    )

    if era5_land_count == 0:

        print(
            "No ERA5-Land overpass data found."
        )

        continue

    era5_cloud = (
        ee.ImageCollection(
            "ECMWF/ERA5/HOURLY"
        )
        .filterBounds(
            bengaluru
        )
        .filterDate(
            window_start,
            window_end
        )
    )

    era5_cloud_count = (
        era5_cloud
        .size()
        .getInfo()
    )

    print(
        "ERA5 cloud images:",
        era5_cloud_count
    )

    if era5_cloud_count == 0:

        print(
            "No ERA5 cloud data found."
        )

        continue

    overpass_weather = (
        era5_land
        .mean()
    )

    overpass_cloud_weather = (
        era5_cloud
        .mean()
    )

    overpass_air_temp = (
        overpass_weather
        .select(
            "temperature_2m"
        )
        .subtract(
            273.15
        )
        .rename(
            "Overpass_Air_Temp"
        )
    )

    overpass_dewpoint = (
        overpass_weather
        .select(
            "dewpoint_temperature_2m"
        )
        .subtract(
            273.15
        )
    )

    overpass_rh = (
        ee.Image(100)
        .multiply(
            overpass_dewpoint
            .multiply(
                17.625
            )
            .divide(
                overpass_dewpoint.add(
                    243.04
                )
            )
            .exp()
            .divide(
                overpass_air_temp
                .multiply(
                    17.625
                )
                .divide(
                    overpass_air_temp.add(
                        243.04
                    )
                )
                .exp()
            )
        )
        .rename(
            "Overpass_Relative_Humidity"
        )
    )

    overpass_u = (
        overpass_weather
        .select(
            "u_component_of_wind_10m"
        )
    )

    overpass_v = (
        overpass_weather
        .select(
            "v_component_of_wind_10m"
        )
    )

    overpass_wind_speed = (
        overpass_u
        .pow(2)
        .add(
            overpass_v.pow(2)
        )
        .sqrt()
        .rename(
            "Overpass_Wind_Speed"
        )
    )

    overpass_solar = (
        overpass_weather
        .select(
            "surface_solar_radiation_downwards_hourly"
        )
        .divide(
            1000000
        )
        .rename(
            "Overpass_Solar_Radiation"
        )
    )

    overpass_cloud_cover = (
        overpass_cloud_weather
        .select(
            "total_cloud_cover"
        )
        .multiply(
            100
        )
        .rename(
            "Overpass_Cloud_Cover"
        )
    )

    overpass_stack = (
        overpass_air_temp
        .addBands(
            overpass_rh
        )
        .addBands(
            overpass_wind_speed
        )
        .addBands(
            overpass_solar
        )
        .addBands(
            overpass_cloud_cover
        )
    )

    stats = (
        overpass_stack
        .reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=bengaluru,
            scale=10000,
            maxPixels=1e9
        )
        .getInfo()
    )

    print(
        "Overpass conditions:"
    )

    print(stats)

    overpass_rows.append({
        "date": date_string,
        "Landsat_Acquisition_Time": acquisition_time,
        "Overpass_Air_Temp": stats.get(
            "Overpass_Air_Temp"
        ),
        "Overpass_Relative_Humidity": stats.get(
            "Overpass_Relative_Humidity"
        ),
        "Overpass_Wind_Speed": stats.get(
            "Overpass_Wind_Speed"
        ),
        "Overpass_Solar_Radiation": stats.get(
            "Overpass_Solar_Radiation"
        ),
        "Overpass_Cloud_Cover": stats.get(
            "Overpass_Cloud_Cover"
        )
    })

overpass_df = pd.DataFrame(
    overpass_rows
)

print(
    "\nOverpass table:"
)

print(
    overpass_df.head()
)

df["date"] = (
    df["date"]
    .dt.strftime(
        "%Y-%m-%d"
    )
)

v5_df = df.merge(
    overpass_df,
    on="date",
    how="left"
)

print(
    "\nV5 rows:"
)

print(
    len(v5_df)
)

new_features = [
    "Overpass_Air_Temp",
    "Overpass_Relative_Humidity",
    "Overpass_Wind_Speed",
    "Overpass_Solar_Radiation",
    "Overpass_Cloud_Cover"
]

print(
    "\nMissing overpass values:"
)

print(
    v5_df[
        new_features
    ]
    .isnull()
    .sum()
)

print(
    "\nV5 columns:"
)

print(
    v5_df.columns.tolist()
)

v5_df.to_csv(
    output_file,
    index=False
)

print(
    "\nV5 dataset saved successfully."
)

print(
    "Saved at:"
)

print(
    output_file
)