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
    / "bengaluru_spatial_greening_plan.csv"
)

df = pd.read_csv(input_file)

print("Cooling priority dataset loaded.")

print("\nTotal rows:")
print(len(df))

required_columns = [
    "date",
    "latitude",
    "longitude",
    "Predicted_LST",
    "L_NDVI",
    "S2_NDVI",
    "Tree_Probability",
    "Built_Probability",
    "Distance_To_Water",
    "Albedo",
    "Cooling_Priority_Score"
]

df = df.dropna(
    subset=required_columns
).copy()

print("\nUsable rows:")
print(len(df))

cell_size_m = 500

lat_m_per_degree = 111320

mean_latitude = df["latitude"].mean()

lon_m_per_degree = (
    111320
    * np.cos(
        np.radians(
            mean_latitude
        )
    )
)

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
    df["Grid_X"].astype(str)
    + "_"
    + df["Grid_Y"].astype(str)
)

print(
    "\nNumber of 500 m grid cells:"
)

print(
    df["Grid_ID"].nunique()
)

grid = (
    df.groupby(
        "Grid_ID"
    )
    .agg(
        Latitude=(
            "latitude",
            "median"
        ),
        Longitude=(
            "longitude",
            "median"
        ),
        Samples=(
            "Predicted_LST",
            "count"
        ),
        Unique_Dates=(
            "date",
            "nunique"
        ),
        Median_Predicted_LST=(
            "Predicted_LST",
            "median"
        ),
        Mean_Predicted_LST=(
            "Predicted_LST",
            "mean"
        ),
        Maximum_Predicted_LST=(
            "Predicted_LST",
            "max"
        ),
        Median_L_NDVI=(
            "L_NDVI",
            "median"
        ),
        Median_S2_NDVI=(
            "S2_NDVI",
            "median"
        ),
        Median_Tree_Probability=(
            "Tree_Probability",
            "median"
        ),
        Median_Built_Probability=(
            "Built_Probability",
            "median"
        ),
        Median_Distance_To_Water=(
            "Distance_To_Water",
            "median"
        ),
        Median_Albedo=(
            "Albedo",
            "median"
        ),
        Median_Cooling_Priority_Score=(
            "Cooling_Priority_Score",
            "median"
        )
    )
    .reset_index()
)

print(
    "\nAggregated cells:"
)

print(
    len(grid)
)


def normalize(series):

    minimum = series.min()
    maximum = series.max()

    if maximum == minimum:

        return pd.Series(
            0.0,
            index=series.index
        )

    return (
        series - minimum
    ) / (
        maximum - minimum
    )


grid["Heat_Score"] = normalize(
    grid["Median_Predicted_LST"]
)

grid["Built_Score"] = normalize(
    grid["Median_Built_Probability"]
)

grid["Low_Tree_Score"] = (
    1
    - normalize(
        grid["Median_Tree_Probability"]
    )
)

grid["Water_Distance_Score"] = normalize(
    grid["Median_Distance_To_Water"]
)

grid["Low_Albedo_Score"] = (
    1
    - normalize(
        grid["Median_Albedo"]
    )
)

grid["Spatial_Cooling_Score"] = (
    0.40
    * grid["Heat_Score"]
    +
    0.25
    * grid["Low_Tree_Score"]
    +
    0.15
    * grid["Built_Score"]
    +
    0.10
    * grid["Water_Distance_Score"]
    +
    0.10
    * grid["Low_Albedo_Score"]
)

grid["Spatial_Cooling_Score"] = (
    grid["Spatial_Cooling_Score"]
    * 100
)

very_high_threshold = (
    grid["Spatial_Cooling_Score"]
    .quantile(0.90)
)

high_threshold = (
    grid["Spatial_Cooling_Score"]
    .quantile(0.75)
)

moderate_threshold = (
    grid["Spatial_Cooling_Score"]
    .quantile(0.50)
)


def priority_class(score):

    if score >= very_high_threshold:

        return "Very High"

    elif score >= high_threshold:

        return "High"

    elif score >= moderate_threshold:

        return "Moderate"

    else:

        return "Low"


grid["Cooling_Priority"] = (
    grid[
        "Spatial_Cooling_Score"
    ]
    .apply(
        priority_class
    )
)

cell_area_m2 = (
    cell_size_m
    * cell_size_m
)

grid["Cell_Area_m2"] = (
    cell_area_m2
)

grid["Cell_Area_hectares"] = (
    grid["Cell_Area_m2"]
    / 10000
)


def greening_fraction(priority):

    if priority == "Very High":

        return 0.15

    elif priority == "High":

        return 0.10

    elif priority == "Moderate":

        return 0.05

    else:

        return 0.02


grid[
    "Suggested_Greening_Fraction"
] = (
    grid[
        "Cooling_Priority"
    ]
    .apply(
        greening_fraction
    )
)

grid[
    "Suggested_Greening_Percent"
] = (
    grid[
        "Suggested_Greening_Fraction"
    ]
    * 100
)

grid[
    "Suggested_Greening_Area_m2"
] = (
    grid[
        "Cell_Area_m2"
    ]
    * grid[
        "Suggested_Greening_Fraction"
    ]
)

average_mature_tree_canopy_m2 = 30

grid[
    "Assumed_Canopy_Area_Per_Tree_m2"
] = (
    average_mature_tree_canopy_m2
)

grid[
    "Approx_Trees_Needed"
] = (
    grid[
        "Suggested_Greening_Area_m2"
    ]
    / average_mature_tree_canopy_m2
)

grid[
    "Approx_Trees_Needed"
] = (
    np.ceil(
        grid[
            "Approx_Trees_Needed"
        ]
    )
    .astype(int)
)


def intervention(row):

    if row["Cooling_Priority"] == "Very High":

        if row["Median_Built_Probability"] >= 0.50:

            return (
                "Priority urban greening: "
                "street-tree corridors, pocket parks, "
                "institutional planting and suitable green roofs"
            )

        else:

            return (
                "Major canopy expansion and restoration "
                "of available open green areas"
            )

    elif row["Cooling_Priority"] == "High":

        return (
            "Increase tree cover and shaded pedestrian corridors"
        )

    elif row["Cooling_Priority"] == "Moderate":

        return (
            "Targeted tree planting and protection "
            "of existing vegetation"
        )

    else:

        return (
            "Maintain existing vegetation "
            "and monitor heat conditions"
        )


grid["Recommended_Action"] = (
    grid.apply(
        intervention,
        axis=1
    )
)

print(
    "\nSpatial priority thresholds:"
)

print(
    "Moderate:",
    moderate_threshold
)

print(
    "High:",
    high_threshold
)

print(
    "Very High:",
    very_high_threshold
)

print(
    "\nPriority distribution:"
)

print(
    grid[
        "Cooling_Priority"
    ]
    .value_counts()
)

print(
    "\nAverage predicted LST:"
)

print(
    grid.groupby(
        "Cooling_Priority"
    )[
        "Median_Predicted_LST"
    ]
    .mean()
    .sort_values()
)

print(
    "\nEstimated trees by priority:"
)

print(
    grid.groupby(
        "Cooling_Priority"
    )[
        "Approx_Trees_Needed"
    ]
    .sum()
)

top_cells = (
    grid.sort_values(
        "Spatial_Cooling_Score",
        ascending=False
    )
    .head(20)
)

print(
    "\nTop 20 cooling-priority areas:"
)

print(
    top_cells[
        [
            "Grid_ID",
            "Latitude",
            "Longitude",
            "Unique_Dates",
            "Median_Predicted_LST",
            "Median_Tree_Probability",
            "Median_Built_Probability",
            "Spatial_Cooling_Score",
            "Cooling_Priority",
            "Suggested_Greening_Percent",
            "Approx_Trees_Needed"
        ]
    ]
    .to_string(
        index=False
    )
)

grid.to_csv(
    output_file,
    index=False
)

print(
    "\nSpatial greening plan saved successfully."
)

print(
    "Saved at:"
)

print(
    output_file
)