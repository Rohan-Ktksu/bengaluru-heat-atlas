import pandas as pd
import numpy as np
from pathlib import Path

script_folder = Path(__file__).resolve().parent
project_folder = script_folder.parent

input_file = (
    project_folder
    / "src"
    / "v5_cooling_priority_recommendations.csv"
)

output_file = (
    project_folder
    / "src"
    / "bengaluru_complete_1km_grid.csv"
)

df = pd.read_csv(
    input_file
)

print("2026 cooling-priority dataset loaded.")

print("\nRows:")
print(len(df))

required_columns = [
    "date",
    "latitude",
    "longitude"
]

df = df.dropna(
    subset=required_columns
).copy()

df["date"] = pd.to_datetime(
    df["date"]
)

cell_size_m = 1000

lat_m_per_degree = 111320

mean_latitude = (
    df["latitude"]
    .mean()
)

lon_m_per_degree = (
    111320
    * np.cos(
        np.radians(
            mean_latitude
        )
    )
)

print("\nMean latitude:")
print(mean_latitude)

print("\nLongitude metres per degree:")
print(lon_m_per_degree)

df["X_Meters"] = (
    df["longitude"]
    * lon_m_per_degree
)

df["Y_Meters"] = (
    df["latitude"]
    * lat_m_per_degree
)

df["Grid_X"] = (
    np.floor(
        df["X_Meters"]
        / cell_size_m
    )
    .astype(int)
)

df["Grid_Y"] = (
    np.floor(
        df["Y_Meters"]
        / cell_size_m
    )
    .astype(int)
)

df["Grid_ID"] = (
    df["Grid_X"]
    .astype(str)
    + "_"
    + df["Grid_Y"]
    .astype(str)
)

min_grid_x = (
    df["Grid_X"]
    .min()
)

max_grid_x = (
    df["Grid_X"]
    .max()
)

min_grid_y = (
    df["Grid_Y"]
    .min()
)

max_grid_y = (
    df["Grid_Y"]
    .max()
)

print("\nGrid extent:")

print(
    "X:",
    min_grid_x,
    "to",
    max_grid_x
)

print(
    "Y:",
    min_grid_y,
    "to",
    max_grid_y
)

grid_rows = []

for grid_x in range(
    min_grid_x,
    max_grid_x + 1
):

    for grid_y in range(
        min_grid_y,
        max_grid_y + 1
    ):

        west_m = (
            grid_x
            * cell_size_m
        )

        east_m = (
            west_m
            + cell_size_m
        )

        south_m = (
            grid_y
            * cell_size_m
        )

        north_m = (
            south_m
            + cell_size_m
        )

        center_x_m = (
            west_m
            + cell_size_m / 2
        )

        center_y_m = (
            south_m
            + cell_size_m / 2
        )

        west_lon = (
            west_m
            / lon_m_per_degree
        )

        east_lon = (
            east_m
            / lon_m_per_degree
        )

        south_lat = (
            south_m
            / lat_m_per_degree
        )

        north_lat = (
            north_m
            / lat_m_per_degree
        )

        center_lon = (
            center_x_m
            / lon_m_per_degree
        )

        center_lat = (
            center_y_m
            / lat_m_per_degree
        )

        grid_id = (
            f"{grid_x}_{grid_y}"
        )

        grid_rows.append(
            {
                "Grid_ID": grid_id,
                "Grid_X": grid_x,
                "Grid_Y": grid_y,
                "Center_Latitude": center_lat,
                "Center_Longitude": center_lon,
                "South_Latitude": south_lat,
                "North_Latitude": north_lat,
                "West_Longitude": west_lon,
                "East_Longitude": east_lon,
                "Cell_Size_m": cell_size_m,
                "Cell_Area_m2": 1000000,
                "Cell_Area_hectares": 100
            }
        )

grid = pd.DataFrame(
    grid_rows
)

print(
    "\nComplete rectangular grid cells:"
)

print(
    len(grid)
)

observation_summary = (
    df.groupby(
        "Grid_ID"
    )
    .agg(
        Historical_Samples=(
            "latitude",
            "count"
        ),
        Historical_Unique_Dates=(
            "date",
            "nunique"
        )
    )
    .reset_index()
)

grid = grid.merge(
    observation_summary,
    on="Grid_ID",
    how="left"
)

grid[
    "Historical_Samples"
] = (
    grid[
        "Historical_Samples"
    ]
    .fillna(0)
    .astype(int)
)

grid[
    "Historical_Unique_Dates"
] = (
    grid[
        "Historical_Unique_Dates"
    ]
    .fillna(0)
    .astype(int)
)

grid[
    "Persistent_Reliable_Cell"
] = (
    grid[
        "Historical_Unique_Dates"
    ]
    >= 3
)


def support_class(
    unique_dates
):

    if unique_dates >= 6:

        return "Very High"

    elif unique_dates >= 5:

        return "High"

    elif unique_dates >= 3:

        return "Moderate"

    elif unique_dates >= 1:

        return "Limited"

    else:

        return "Prediction Only"


grid[
    "Observation_Support"
] = (
    grid[
        "Historical_Unique_Dates"
    ]
    .apply(
        support_class
    )
)

observed_xy = set(
    zip(
        df["Grid_X"],
        df["Grid_Y"]
    )
)


def inside_study_footprint(
    row
):

    gx = row[
        "Grid_X"
    ]

    gy = row[
        "Grid_Y"
    ]

    if (
        gx,
        gy
    ) in observed_xy:

        return True

    for dx in [
        -1,
        0,
        1
    ]:

        for dy in [
            -1,
            0,
            1
        ]:

            if (
                gx + dx,
                gy + dy
            ) in observed_xy:

                return True

    return False


grid[
    "Inside_Study_Footprint"
] = (
    grid.apply(
        inside_study_footprint,
        axis=1
    )
)

grid = (
    grid[
        grid[
            "Inside_Study_Footprint"
        ]
    ]
    .copy()
)

grid = (
    grid
    .sort_values(
        [
            "Grid_Y",
            "Grid_X"
        ]
    )
    .reset_index(
        drop=True
    )
)

print(
    "\nCells inside study footprint:"
)

print(
    len(grid)
)

print(
    "\nObservation support:"
)

print(
    grid[
        "Observation_Support"
    ]
    .value_counts()
)

print(
    "\nReliable cells with >= 3 unique dates:"
)

print(
    grid[
        "Persistent_Reliable_Cell"
    ]
    .sum()
)

limited_cells = (
    grid[
        "Historical_Unique_Dates"
    ]
    .between(
        1,
        2
    )
    .sum()
)

prediction_only_cells = (
    grid[
        "Historical_Unique_Dates"
    ]
    .eq(0)
    .sum()
)

print(
    "\nLimited cells with 1-2 dates:"
)

print(
    limited_cells
)

print(
    "\nPrediction-only cells with 0 dates:"
)

print(
    prediction_only_cells
)

print(
    "\nCells requiring prediction / additional support:"
)

print(
    (
        ~grid[
            "Persistent_Reliable_Cell"
        ]
    )
    .sum()
)

grid.to_csv(
    output_file,
    index=False
)

print(
    "\nComplete Bengaluru grid saved."
)

print(
    "\nSaved at:"
)

print(
    output_file
)

print(
    "\nFirst 10 grid cells:"
)

print(
    grid.head(
        10
    )
    .to_string(
        index=False
    )
)