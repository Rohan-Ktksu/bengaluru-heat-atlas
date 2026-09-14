import pandas as pd
import time
from pathlib import Path

from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter


script_folder = Path(__file__).resolve().parent
project_folder = script_folder.parent

input_file = (
    project_folder
    / "src"
    / "bengaluru_final_cooling_tree_plan.csv"
)

output_file = (
    project_folder
    / "src"
    / "bengaluru_final_cooling_tree_plan_with_localities.csv"
)

cache_file = (
    project_folder
    / "src"
    / "bengaluru_reverse_geocode_cache.csv"
)


df = pd.read_csv(
    input_file
)

print("Final cooling plan loaded.")

print("\nTotal cells:")
print(len(df))


geolocator = Nominatim(
    user_agent="rohan_isro_bengaluru_heat_project"
)

reverse = RateLimiter(
    geolocator.reverse,
    min_delay_seconds=1.1,
    swallow_exceptions=True
)


if cache_file.exists():

    cache_df = pd.read_csv(
        cache_file
    )

    print(
        "\nExisting geocoding cache loaded."
    )

    print(
        "Cached locations:",
        len(cache_df)
    )

else:

    cache_df = pd.DataFrame(
        columns=[
            "Grid_ID",
            "Latitude",
            "Longitude",
            "Area_Name",
            "Neighbourhood",
            "Suburb",
            "Town",
            "City",
            "City_District",
            "County",
            "State_District",
            "Postcode",
            "Display_Name"
        ]
    )


cached_ids = set(
    cache_df["Grid_ID"]
    .astype(str)
)


def extract_address(
    location
):

    if location is None:

        return {
            "Area_Name": None,
            "Neighbourhood": None,
            "Suburb": None,
            "Town": None,
            "City": None,
            "City_District": None,
            "County": None,
            "State_District": None,
            "Postcode": None,
            "Display_Name": None
        }

    raw = location.raw

    address = raw.get(
        "address",
        {}
    )

    neighbourhood = address.get(
        "neighbourhood"
    )

    suburb = address.get(
        "suburb"
    )

    quarter = address.get(
        "quarter"
    )

    residential = address.get(
        "residential"
    )

    village = address.get(
        "village"
    )

    town = address.get(
        "town"
    )

    city = address.get(
        "city"
    )

    city_district = address.get(
        "city_district"
    )

    county = address.get(
        "county"
    )

    state_district = address.get(
        "state_district"
    )

    postcode = address.get(
        "postcode"
    )


    area_name = None

    candidates = [
        neighbourhood,
        suburb,
        quarter,
        residential,
        village,
        town,
        city_district,
        city
    ]

    for candidate in candidates:

        if candidate:

            area_name = candidate

            break


    return {
        "Area_Name": area_name,
        "Neighbourhood": neighbourhood,
        "Suburb": suburb,
        "Town": town,
        "City": city,
        "City_District": city_district,
        "County": county,
        "State_District": state_district,
        "Postcode": postcode,
        "Display_Name": location.address
    }


new_rows = []


for index, row in df.iterrows():

    grid_id = str(
        row["Grid_ID"]
    )

    if grid_id in cached_ids:

        continue


    latitude = float(
        row["Center_Latitude"]
    )

    longitude = float(
        row["Center_Longitude"]
    )


    print(
        "\nGeocoding:",
        index + 1,
        "of",
        len(df),
        grid_id,
        latitude,
        longitude
    )


    try:

        location = reverse(
            (
                latitude,
                longitude
            ),
            language="en",
            zoom=14
        )

        result = extract_address(
            location
        )

    except Exception as error:

        print(
            "Geocoding error:"
        )

        print(
            error
        )

        result = {
            "Area_Name": None,
            "Neighbourhood": None,
            "Suburb": None,
            "Town": None,
            "City": None,
            "City_District": None,
            "County": None,
            "State_District": None,
            "Postcode": None,
            "Display_Name": None
        }


    result_row = {
        "Grid_ID": grid_id,
        "Latitude": latitude,
        "Longitude": longitude,
        **result
    }


    new_rows.append(
        result_row
    )


    print(
        "Area:",
        result[
            "Area_Name"
        ]
    )


    if len(new_rows) >= 20:

        batch_df = pd.DataFrame(
            new_rows
        )

        if cache_file.exists():

            batch_df.to_csv(
                cache_file,
                mode="a",
                header=False,
                index=False
            )

        else:

            batch_df.to_csv(
                cache_file,
                index=False
            )


        print(
            "\nSaved geocoding batch."
        )

        new_rows = []


if len(new_rows) > 0:

    batch_df = pd.DataFrame(
        new_rows
    )

    if cache_file.exists():

        batch_df.to_csv(
            cache_file,
            mode="a",
            header=False,
            index=False
        )

    else:

        batch_df.to_csv(
            cache_file,
            index=False
        )


cache_df = pd.read_csv(
    cache_file
)

cache_df = (
    cache_df
    .drop_duplicates(
        subset="Grid_ID",
        keep="last"
    )
)


df["Grid_ID"] = (
    df["Grid_ID"]
    .astype(str)
)

cache_df["Grid_ID"] = (
    cache_df["Grid_ID"]
    .astype(str)
)


merge_columns = [
    "Grid_ID",
    "Area_Name",
    "Neighbourhood",
    "Suburb",
    "Town",
    "City",
    "City_District",
    "County",
    "State_District",
    "Postcode",
    "Display_Name"
]


final_df = df.merge(
    cache_df[
        merge_columns
    ],
    on="Grid_ID",
    how="left"
)


print(
    "\nCells with area names:"
)

print(
    final_df[
        "Area_Name"
    ]
    .notna()
    .sum()
)


print(
    "\nCells without area names:"
)

print(
    final_df[
        "Area_Name"
    ]
    .isna()
    .sum()
)


print(
    "\nTop hotspot areas:"
)


top = (
    final_df
    .sort_values(
        "Hybrid_Heat_Score",
        ascending=False
    )
    .head(
        30
    )
)


print(
    top[
        [
            "Grid_ID",
            "Area_Name",
            "Suburb",
            "Postcode",
            "Final_Median_LST",
            "Hybrid_Heat_Score",
            "Final_Cooling_Priority",
            "Approx_Trees_To_Plant",
            "Planning_Reliability"
        ]
    ]
    .to_string(
        index=False
    )
)


area_summary = (
    final_df
    .groupby(
        "Area_Name",
        dropna=True
    )
    .agg(

        Grid_Cells=(
            "Grid_ID",
            "count"
        ),

        Mean_LST=(
            "Final_Median_LST",
            "mean"
        ),

        Maximum_LST=(
            "Final_Max_LST",
            "max"
        ),

        Mean_Heat_Score=(
            "Hybrid_Heat_Score",
            "mean"
        ),

        Total_Trees=(
            "Approx_Trees_To_Plant",
            "sum"
        ),

        High_Priority_Cells=(
            "Final_Cooling_Priority",
            lambda x: (
                x.isin(
                    [
                        "High",
                        "Very High"
                    ]
                )
            ).sum()
        )

    )
    .reset_index()
)


area_summary = (
    area_summary
    .sort_values(
        [
            "High_Priority_Cells",
            "Mean_Heat_Score"
        ],
        ascending=False
    )
)


summary_file = (
    project_folder
    / "src"
    / "bengaluru_locality_heat_summary.csv"
)


area_summary.to_csv(
    summary_file,
    index=False
)


final_df.to_csv(
    output_file,
    index=False
)


print(
    "\nSTEP 43 COMPLETE"
)


print(
    "\nFinal locality dataset saved at:"
)

print(
    output_file
)


print(
    "\nLocality summary saved at:"
)

print(
    summary_file
)