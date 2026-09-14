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
    / "bengaluru_persistent_hotspot_tree_plan.csv"
)

df = pd.read_csv(
    input_file
)

print("Cooling recommendation dataset loaded.")

print("\nTotal rows:")
print(len(df))

required_columns = [
    "date",
    "latitude",
    "longitude",
    "Predicted_LST",
    "Heat_Class",
    "L_NDVI",
    "S2_NDVI",
    "Tree_Probability",
    "Built_Probability",
    "Distance_To_Water",
    "Albedo"
]

df = df.dropna(
    subset=required_columns
).copy()

print("\nUsable rows:")
print(len(df))

df["date"] = pd.to_datetime(
    df["date"]
)

cell_size_m = 1000

lat_m_per_degree = 111320

mean_latitude = (
    df["latitude"].mean()
)

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

df["Is_Hot"] = (
    df["Heat_Class"]
    .isin([
        "High",
        "Very High"
    ])
    .astype(int)
)

df["Is_Very_Hot"] = (
    df["Heat_Class"]
    .eq(
        "Very High"
    )
    .astype(int)
)

print(
    "\nNumber of 1 km grid cells:"
)

print(
    df["Grid_ID"]
    .nunique()
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
        Total_Samples=(
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
        Hot_Observations=(
            "Is_Hot",
            "sum"
        ),
        Very_Hot_Observations=(
            "Is_Very_Hot",
            "sum"
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
        )
    )
    .reset_index()
)

grid["Hot_Frequency"] = (
    grid["Hot_Observations"]
    / grid["Total_Samples"]
)

grid["Very_Hot_Frequency"] = (
    grid["Very_Hot_Observations"]
    / grid["Total_Samples"]
)

minimum_unique_dates = 3

grid["Reliable_Cell"] = (
    grid["Unique_Dates"]
    >= minimum_unique_dates
)

print(
    "\nCells with at least",
    minimum_unique_dates,
    "unique dates:"
)

print(
    grid[
        "Reliable_Cell"
    ].sum()
)

reliable = grid[
    grid["Reliable_Cell"]
].copy()

print(
    "\nReliable rows:"
)

print(
    len(reliable)
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


reliable["Heat_Intensity_Score"] = normalize(
    reliable["Median_Predicted_LST"]
)

reliable["Hot_Frequency_Score"] = (
    reliable["Hot_Frequency"]
)

reliable["Very_Hot_Frequency_Score"] = (
    reliable["Very_Hot_Frequency"]
)

reliable["Low_Tree_Score"] = (
    1
    - normalize(
        reliable[
            "Median_Tree_Probability"
        ]
    )
)

reliable["Built_Score"] = normalize(
    reliable[
        "Median_Built_Probability"
    ]
)

reliable["Water_Distance_Score"] = normalize(
    reliable[
        "Median_Distance_To_Water"
    ]
)

reliable["Low_Albedo_Score"] = (
    1
    - normalize(
        reliable[
            "Median_Albedo"
        ]
    )
)

reliable["Persistent_Heat_Score"] = (
    0.30
    * reliable["Heat_Intensity_Score"]
    +
    0.25
    * reliable["Hot_Frequency_Score"]
    +
    0.10
    * reliable["Very_Hot_Frequency_Score"]
    +
    0.15
    * reliable["Low_Tree_Score"]
    +
    0.10
    * reliable["Built_Score"]
    +
    0.05
    * reliable["Water_Distance_Score"]
    +
    0.05
    * reliable["Low_Albedo_Score"]
)

reliable["Persistent_Heat_Score"] = (
    reliable["Persistent_Heat_Score"]
    * 100
)

very_high_threshold = (
    reliable[
        "Persistent_Heat_Score"
    ]
    .quantile(
        0.90
    )
)

high_threshold = (
    reliable[
        "Persistent_Heat_Score"
    ]
    .quantile(
        0.75
    )
)

moderate_threshold = (
    reliable[
        "Persistent_Heat_Score"
    ]
    .quantile(
        0.50
    )
)


def classify_priority(score):

    if score >= very_high_threshold:

        return "Very High"

    elif score >= high_threshold:

        return "High"

    elif score >= moderate_threshold:

        return "Moderate"

    else:

        return "Low"


reliable["Persistent_Cooling_Priority"] = (
    reliable[
        "Persistent_Heat_Score"
    ]
    .apply(
        classify_priority
    )
)

cell_area_m2 = (
    cell_size_m
    * cell_size_m
)

reliable["Cell_Area_m2"] = (
    cell_area_m2
)

reliable["Cell_Area_hectares"] = (
    reliable["Cell_Area_m2"]
    / 10000
)


def minimum_greening(priority):

    if priority == "Very High":
        return 0.12

    elif priority == "High":
        return 0.08

    elif priority == "Moderate":
        return 0.04

    else:
        return 0.01


def maximum_greening(priority):

    if priority == "Very High":
        return 0.18

    elif priority == "High":
        return 0.12

    elif priority == "Moderate":
        return 0.07

    else:
        return 0.03


reliable["Min_Greening_Fraction"] = (
    reliable[
        "Persistent_Cooling_Priority"
    ]
    .apply(
        minimum_greening
    )
)

reliable["Max_Greening_Fraction"] = (
    reliable[
        "Persistent_Cooling_Priority"
    ]
    .apply(
        maximum_greening
    )
)

reliable["Need_Factor"] = (
    0.50
    * reliable["Low_Tree_Score"]
    +
    0.30
    * reliable["Hot_Frequency"]
    +
    0.20
    * reliable["Built_Score"]
)

reliable["Suggested_Greening_Fraction"] = (
    reliable["Min_Greening_Fraction"]
    +
    (
        reliable["Max_Greening_Fraction"]
        - reliable["Min_Greening_Fraction"]
    )
    * reliable["Need_Factor"]
)

reliable["Suggested_Greening_Percent"] = (
    reliable[
        "Suggested_Greening_Fraction"
    ]
    * 100
)

reliable["Suggested_Greening_Area_m2"] = (
    reliable[
        "Cell_Area_m2"
    ]
    * reliable[
        "Suggested_Greening_Fraction"
    ]
)

average_canopy_per_tree_m2 = 30

reliable[
    "Assumed_Mature_Canopy_Per_Tree_m2"
] = (
    average_canopy_per_tree_m2
)

reliable["Approx_Trees_To_Plant"] = (
    reliable[
        "Suggested_Greening_Area_m2"
    ]
    / average_canopy_per_tree_m2
)

reliable["Approx_Trees_To_Plant"] = (
    np.ceil(
        reliable[
            "Approx_Trees_To_Plant"
        ]
    )
    .astype(int)
)

reliable["Trees_Per_Hectare"] = (
    reliable[
        "Approx_Trees_To_Plant"
    ]
    / reliable[
        "Cell_Area_hectares"
    ]
)


def recommendation(row):

    if (
        row["Persistent_Cooling_Priority"]
        == "Very High"
    ):

        if (
            row["Median_Built_Probability"]
            >= 0.50
        ):

            return (
                "Urgent urban greening: "
                "street trees, shaded corridors, "
                "pocket parks, institutional planting "
                "and suitable green roofs"
            )

        else:

            return (
                "Major tree-canopy expansion "
                "and restoration of open green areas"
            )

    elif (
        row["Persistent_Cooling_Priority"]
        == "High"
    ):

        return (
            "Increase tree canopy, shaded streets "
            "and connected green corridors"
        )

    elif (
        row["Persistent_Cooling_Priority"]
        == "Moderate"
    ):

        return (
            "Targeted tree planting and protection "
            "of existing vegetation"
        )

    else:

        return (
            "Maintain existing vegetation "
            "and monitor future heat"
        )


reliable["Recommended_Action"] = (
    reliable.apply(
        recommendation,
        axis=1
    )
)

print(
    "\nPersistent heat thresholds:"
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
    "\nPersistent priority distribution:"
)

print(
    reliable[
        "Persistent_Cooling_Priority"
    ]
    .value_counts()
)

print(
    "\nAverage number of observation dates:"
)

print(
    reliable[
        "Unique_Dates"
    ].mean()
)

print(
    "\nMean hot frequency by priority:"
)

print(
    reliable.groupby(
        "Persistent_Cooling_Priority"
    )[
        "Hot_Frequency"
    ]
    .mean()
    .sort_values()
)

print(
    "\nMean median LST by priority:"
)

print(
    reliable.groupby(
        "Persistent_Cooling_Priority"
    )[
        "Median_Predicted_LST"
    ]
    .mean()
    .sort_values()
)

print(
    "\nEstimated trees to plant by priority:"
)

print(
    reliable.groupby(
        "Persistent_Cooling_Priority"
    )[
        "Approx_Trees_To_Plant"
    ]
    .sum()
)

print(
    "\nAverage trees per hectare:"
)

print(
    reliable.groupby(
        "Persistent_Cooling_Priority"
    )[
        "Trees_Per_Hectare"
    ]
    .mean()
)

top_cells = (
    reliable
    .sort_values(
        "Persistent_Heat_Score",
        ascending=False
    )
    .head(20)
)

print(
    "\nTop 20 persistent hotspot areas:"
)

print(
    top_cells[
        [
            "Grid_ID",
            "Latitude",
            "Longitude",
            "Unique_Dates",
            "Median_Predicted_LST",
            "Hot_Frequency",
            "Very_Hot_Frequency",
            "Median_Tree_Probability",
            "Median_Built_Probability",
            "Persistent_Heat_Score",
            "Persistent_Cooling_Priority",
            "Suggested_Greening_Percent",
            "Approx_Trees_To_Plant",
            "Trees_Per_Hectare"
        ]
    ]
    .to_string(
        index=False
    )
)

reliable.to_csv(
    output_file,
    index=False
)

print(
    "\nPersistent hotspot tree plan saved successfully."
)

print(
    "Saved at:"
)

print(
    output_file
)