import ee
import pandas as pd
from pathlib import Path

project_id = input(
    "Enter your Google Cloud Project ID: "
).strip()

ee.Initialize(
    project=project_id
)

script_folder = Path(__file__).resolve().parent
project_folder = script_folder.parent

grid_file = (
    project_folder
    / "src"
    / "bengaluru_complete_1km_grid.csv"
)

dates_file = (
    project_folder
    / "src"
    / "v5_2026_hotspot_predictions.csv"
)

output_file = (
    project_folder
    / "src"
    / "bengaluru_complete_grid_spatial_features.csv"
)

grid_df = pd.read_csv(
    grid_file
)

dates_df = pd.read_csv(
    dates_file
)

print("Complete 1 km grid loaded.")
print("Grid cells:", len(grid_df))

dates_df["date"] = pd.to_datetime(
    dates_df["date"]
)

target_dates = (
    dates_df["date"]
    .dt.strftime("%Y-%m-%d")
    .drop_duplicates()
    .sort_values()
    .tolist()
)

print("\n2026 target dates:")

for date in target_dates:
    print(date)

grid_features = []

for _, row in grid_df.iterrows():

    geometry = ee.Geometry.Rectangle(
        [
            float(row["West_Longitude"]),
            float(row["South_Latitude"]),
            float(row["East_Longitude"]),
            float(row["North_Latitude"])
        ],
        geodesic=False
    )

    feature = ee.Feature(
        geometry,
        {
            "Grid_ID": str(
                row["Grid_ID"]
            ),
            "Grid_X": int(
                row["Grid_X"]
            ),
            "Grid_Y": int(
                row["Grid_Y"]
            ),
            "Center_Latitude": float(
                row["Center_Latitude"]
            ),
            "Center_Longitude": float(
                row["Center_Longitude"]
            ),
            "Historical_Samples": int(
                row["Historical_Samples"]
            ),
            "Historical_Unique_Dates": int(
                row["Historical_Unique_Dates"]
            ),
            "Observation_Support": str(
                row["Observation_Support"]
            )
        }
    )

    grid_features.append(
        feature
    )

grid_fc = ee.FeatureCollection(
    grid_features
)

print(
    "\nEarth Engine grid created:",
    len(grid_features),
    "cells"
)

elevation = (
    ee.Image(
        "USGS/SRTMGL1_003"
    )
    .select(
        "elevation"
    )
    .rename(
        "Elevation"
    )
)

gsw = ee.Image(
    "JRC/GSW1_4/GlobalSurfaceWater"
)

water_occurrence = (
    gsw
    .select(
        "occurrence"
    )
    .unmask(0)
)

water_mask = (
    water_occurrence
    .gte(50)
)

water_projection = (
    ee.Projection(
        "EPSG:32643"
    )
    .atScale(100)
)

water_mask_100m = (
    water_mask
    .reproject(
        water_projection
    )
)

distance_to_water = (
    water_mask_100m
    .fastDistanceTransform(
        neighborhood=250,
        units="pixels",
        metric="squared_euclidean"
    )
    .sqrt()
    .multiply(100)
    .min(25000)
    .rename(
        "Distance_To_Water"
    )
)

processed_dates = set()

if output_file.exists():

    existing_df = pd.read_csv(
        output_file
    )

    expected_cells = len(
        grid_df
    )

    complete_dates = (
        existing_df
        .groupby(
            "date"
        )[
            "Grid_ID"
        ]
        .nunique()
    )

    processed_dates = set(
        complete_dates[
            complete_dates >= expected_cells
        ]
        .index
        .astype(str)
    )

    incomplete_dates = set(
        complete_dates[
            complete_dates < expected_cells
        ]
        .index
        .astype(str)
    )

    if len(incomplete_dates) > 0:

        print(
            "\nRemoving incomplete previous dates:"
        )

        print(
            incomplete_dates
        )

        existing_df = existing_df[
            ~existing_df[
                "date"
            ]
            .astype(str)
            .isin(
                incomplete_dates
            )
        ].copy()

        existing_df.to_csv(
            output_file,
            index=False
        )

    print(
        "\nAlready completed dates:",
        len(processed_dates)
    )

for date_index, date_string in enumerate(
    target_dates
):

    if date_string in processed_dates:

        print(
            "\nSkipping completed date:",
            date_string
        )

        continue

    print(
        "\nProcessing date:",
        date_string,
        "(",
        date_index + 1,
        "of",
        len(target_dates),
        ")"
    )

    try:

        day_start = ee.Date(
            date_string
        )

        day_end = (
            day_start
            .advance(
                1,
                "day"
            )
        )

        landsat = (
            ee.ImageCollection(
                "LANDSAT/LC08/C02/T1_L2"
            )
            .filterBounds(
                grid_fc.geometry()
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
            landsat
            .size()
            .getInfo()
        )

        print(
            "Landsat images found:",
            landsat_count
        )

        if landsat_count == 0:

            print(
                "No Landsat image found."
            )

            continue

        landsat_image = ee.Image(
            landsat.first()
        )

        landsat_date = ee.Date(
            landsat_image.get(
                "system:time_start"
            )
        )

        acquisition_time = (
            landsat_date
            .format(
                "YYYY-MM-dd HH:mm:ss"
            )
            .getInfo()
        )

        print(
            "Landsat acquisition:",
            acquisition_time
        )

        qa = landsat_image.select(
            "QA_PIXEL"
        )

        cloud_bit = 1 << 3
        cloud_shadow_bit = 1 << 4

        landsat_mask = (
            qa
            .bitwiseAnd(
                cloud_bit
            )
            .eq(0)
            .And(
                qa
                .bitwiseAnd(
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

        blue = (
            landsat_clean
            .select(
                "SR_B2"
            )
            .multiply(
                0.0000275
            )
            .add(
                -0.2
            )
        )

        green = (
            landsat_clean
            .select(
                "SR_B3"
            )
            .multiply(
                0.0000275
            )
            .add(
                -0.2
            )
        )

        red = (
            landsat_clean
            .select(
                "SR_B4"
            )
            .multiply(
                0.0000275
            )
            .add(
                -0.2
            )
        )

        nir = (
            landsat_clean
            .select(
                "SR_B5"
            )
            .multiply(
                0.0000275
            )
            .add(
                -0.2
            )
        )

        swir = (
            landsat_clean
            .select(
                "SR_B6"
            )
            .multiply(
                0.0000275
            )
            .add(
                -0.2
            )
        )

        swir2 = (
            landsat_clean
            .select(
                "SR_B7"
            )
            .multiply(
                0.0000275
            )
            .add(
                -0.2
            )
        )

        l_ndvi = (
            nir
            .subtract(
                red
            )
            .divide(
                nir.add(
                    red
                )
            )
            .rename(
                "L_NDVI"
            )
        )

        ndbi = (
            swir
            .subtract(
                nir
            )
            .divide(
                swir.add(
                    nir
                )
            )
            .rename(
                "NDBI"
            )
        )

        ndwi = (
            green
            .subtract(
                nir
            )
            .divide(
                green.add(
                    nir
                )
            )
            .rename(
                "NDWI"
            )
        )

        albedo = (
            blue
            .multiply(
                0.356
            )
            .add(
                red.multiply(
                    0.130
                )
            )
            .add(
                nir.multiply(
                    0.373
                )
            )
            .add(
                swir.multiply(
                    0.085
                )
            )
            .add(
                swir2.multiply(
                    0.072
                )
            )
            .subtract(
                0.0018
            )
            .rename(
                "Albedo"
            )
        )

        sentinel_start = (
            landsat_date
            .advance(
                -5,
                "day"
            )
        )

        sentinel_end = (
            landsat_date
            .advance(
                5,
                "day"
            )
        )

        sentinel = (
            ee.ImageCollection(
                "COPERNICUS/S2_SR_HARMONIZED"
            )
            .filterBounds(
                grid_fc.geometry()
            )
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
            .sort(
                "CLOUDY_PIXEL_PERCENTAGE"
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
                "No Sentinel image found."
            )

            continue

        sentinel_image = ee.Image(
            sentinel.first()
        )

        sentinel_date = ee.Date(
            sentinel_image.get(
                "system:time_start"
            )
        )

        sentinel_date_string = (
            sentinel_date
            .format(
                "YYYY-MM-dd"
            )
            .getInfo()
        )

        print(
            "Selected Sentinel date:",
            sentinel_date_string
        )

        scl = (
            sentinel_image
            .select(
                "SCL"
            )
        )

        sentinel_mask = (
            scl.neq(3)
            .And(
                scl.neq(8)
            )
            .And(
                scl.neq(9)
            )
            .And(
                scl.neq(10)
            )
        )

        sentinel_clean = (
            sentinel_image
            .updateMask(
                sentinel_mask
            )
        )

        s2_red = (
            sentinel_clean
            .select(
                "B4"
            )
        )

        s2_nir = (
            sentinel_clean
            .select(
                "B8"
            )
        )

        s2_ndvi = (
            s2_nir
            .subtract(
                s2_red
            )
            .divide(
                s2_nir.add(
                    s2_red
                )
            )
            .rename(
                "S2_NDVI"
            )
        )

        dynamic_world = (
            ee.ImageCollection(
                "GOOGLE/DYNAMICWORLD/V1"
            )
            .filterBounds(
                grid_fc.geometry()
            )
            .filterDate(
                sentinel_start,
                sentinel_end
            )
        )

        dw_count = (
            dynamic_world
            .size()
            .getInfo()
        )

        print(
            "Dynamic World images found:",
            dw_count
        )

        if dw_count == 0:

            print(
                "No Dynamic World data."
            )

            continue

        built_probability = (
            dynamic_world
            .select(
                "built"
            )
            .mean()
            .rename(
                "Built_Probability"
            )
        )

        tree_probability = (
            dynamic_world
            .select(
                "trees"
            )
            .mean()
            .rename(
                "Tree_Probability"
            )
        )

        spatial_stack = (
            l_ndvi
            .addBands(
                ndbi
            )
            .addBands(
                ndwi
            )
            .addBands(
                s2_ndvi
            )
            .addBands(
                elevation
            )
            .addBands(
                built_probability
            )
            .addBands(
                tree_probability
            )
            .addBands(
                albedo
            )
            .addBands(
                distance_to_water
            )
        )

        reduced = (
            spatial_stack
            .reduceRegions(
                collection=grid_fc,
                reducer=ee.Reducer.mean(),
                scale=30,
                tileScale=4
            )
        )

        result = (
            reduced
            .getInfo()
        )

        rows = []

        for feature in result[
            "features"
        ]:

            properties = (
                feature[
                    "properties"
                ]
                .copy()
            )

            properties[
                "date"
            ] = date_string

            properties[
                "Landsat_Acquisition_Time"
            ] = acquisition_time

            properties[
                "sentinel_date"
            ] = sentinel_date_string

            rows.append(
                properties
            )

        date_df = pd.DataFrame(
            rows
        )

        expected_cells = len(
            grid_df
        )

        print(
            "Grid rows returned:",
            len(date_df),
            "of",
            expected_cells
        )

        if len(date_df) != expected_cells:

            print(
                "Warning: returned cell count does not match grid."
            )

        spatial_columns = [
            "L_NDVI",
            "NDBI",
            "NDWI",
            "S2_NDVI",
            "Elevation",
            "Built_Probability",
            "Tree_Probability",
            "Albedo",
            "Distance_To_Water"
        ]

        print(
            "\nMissing feature values for this date:"
        )

        for column in spatial_columns:

            if column in date_df.columns:

                print(
                    column,
                    ":",
                    date_df[
                        column
                    ]
                    .isna()
                    .sum()
                )

        if output_file.exists():

            date_df.to_csv(
                output_file,
                mode="a",
                header=False,
                index=False
            )

        else:

            date_df.to_csv(
                output_file,
                mode="w",
                header=True,
                index=False
            )

        print(
            "\nSaved spatial features for:",
            date_string
        )

    except Exception as error:

        print(
            "\nDate failed:"
        )

        print(
            date_string
        )

        print(
            error
        )

        print(
            "Continuing to next date."
        )

print(
    "\nStep 36 finished."
)

if output_file.exists():

    final_df = pd.read_csv(
        output_file
    )

    print(
        "\nTotal feature rows:"
    )

    print(
        len(final_df)
    )

    print(
        "\nUnique grid cells:"
    )

    print(
        final_df[
            "Grid_ID"
        ]
        .nunique()
    )

    print(
        "\nUnique dates:"
    )

    print(
        final_df[
            "date"
        ]
        .nunique()
    )

    print(
        "\nRows by date:"
    )

    print(
        final_df[
            "date"
        ]
        .value_counts()
        .sort_index()
    )

    print(
        "\nSaved at:"
    )

    print(
        output_file
    )