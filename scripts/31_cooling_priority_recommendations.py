import pandas as pd
import numpy as np
from pathlib import Path

script_folder = Path(__file__).resolve().parent
project_folder = script_folder.parent

input_file = (
    project_folder
    / "src"
    / "v5_2026_hotspot_predictions.csv"
)

output_file = (
    project_folder
    / "src"
    / "v5_cooling_priority_recommendations.csv"
)

df = pd.read_csv(input_file)

print("Hotspot dataset loaded.")

print("\nTotal rows:")
print(len(df))

print("\nColumns:")
print(df.columns.tolist())

required_columns = [
    "Predicted_LST",
    "Tree_Probability",
    "Built_Probability",
    "L_NDVI",
    "S2_NDVI",
    "Distance_To_Water",
    "Albedo",
    "latitude",
    "longitude",
    "date"
]

df = df.dropna(
    subset=required_columns
).copy()

print("\nUsable rows:")
print(len(df))


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


df["Heat_Score"] = normalize(
    df["Predicted_LST"]
)

df["Built_Score"] = normalize(
    df["Built_Probability"]
)

df["Tree_Deficit"] = (
    1
    - df["Tree_Probability"]
    .clip(
        0,
        1
    )
)

df["Landsat_Vegetation_Deficit"] = (
    1
    - normalize(
        df["L_NDVI"]
    )
)

df["Sentinel_Vegetation_Deficit"] = (
    1
    - normalize(
        df["S2_NDVI"]
    )
)

df["Vegetation_Deficit"] = (
    0.50
    * df["Tree_Deficit"]
    +
    0.25
    * df["Landsat_Vegetation_Deficit"]
    +
    0.25
    * df["Sentinel_Vegetation_Deficit"]
)

df["Water_Distance_Score"] = normalize(
    df["Distance_To_Water"]
)

df["Albedo_Heat_Score"] = (
    1
    - normalize(
        df["Albedo"]
    )
)

df["Cooling_Priority_Score"] = (
    0.40
    * df["Heat_Score"]
    +
    0.25
    * df["Vegetation_Deficit"]
    +
    0.15
    * df["Built_Score"]
    +
    0.10
    * df["Water_Distance_Score"]
    +
    0.10
    * df["Albedo_Heat_Score"]
)

df["Cooling_Priority_Score"] = (
    df["Cooling_Priority_Score"]
    * 100
)

very_high_threshold = (
    df["Cooling_Priority_Score"]
    .quantile(
        0.90
    )
)

high_threshold = (
    df["Cooling_Priority_Score"]
    .quantile(
        0.75
    )
)

moderate_threshold = (
    df["Cooling_Priority_Score"]
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


df["Cooling_Priority"] = (
    df["Cooling_Priority_Score"]
    .apply(
        classify_priority
    )
)

target_tree_probability = 0.40

df["Canopy_Deficit"] = (
    target_tree_probability
    - df["Tree_Probability"]
)

df["Canopy_Deficit"] = (
    df["Canopy_Deficit"]
    .clip(
        lower=0
    )
)

df["Recommended_Canopy_Increase_Percent"] = (
    df["Canopy_Deficit"]
    * 100
)


def recommendation(row):

    if row["Cooling_Priority"] == "Very High":

        if row["Built_Probability"] >= 0.50:

            return (
                "High-priority urban greening: "
                "street trees, shaded corridors, "
                "pocket parks and suitable green roofs"
            )

        else:

            return (
                "High-priority canopy expansion "
                "and restoration of available green space"
            )

    elif row["Cooling_Priority"] == "High":

        if row["Tree_Probability"] < 0.20:

            return (
                "Increase tree canopy and create "
                "connected shaded green corridors"
            )

        else:

            return (
                "Protect existing canopy and add "
                "targeted shade vegetation"
            )

    elif row["Cooling_Priority"] == "Moderate":

        return (
            "Maintain vegetation and consider "
            "targeted local canopy improvement"
        )

    else:

        return (
            "Maintain existing vegetation "
            "and monitor future heat conditions"
        )


df["Recommendation"] = df.apply(
    recommendation,
    axis=1
)

print(
    "\nCooling priority thresholds:"
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
    "\nCooling priority distribution:"
)

print(
    df["Cooling_Priority"]
    .value_counts()
)

print(
    "\nMean predicted LST by cooling priority:"
)

print(
    df.groupby(
        "Cooling_Priority"
    )["Predicted_LST"]
    .mean()
    .sort_values()
)

print(
    "\nMean tree probability by cooling priority:"
)

print(
    df.groupby(
        "Cooling_Priority"
    )["Tree_Probability"]
    .mean()
    .sort_values()
)

print(
    "\nTop 20 cooling-priority locations:"
)

top_locations = (
    df.sort_values(
        "Cooling_Priority_Score",
        ascending=False
    )
    .head(20)
)

print(
    top_locations[
        [
            "date",
            "latitude",
            "longitude",
            "Predicted_LST",
            "Tree_Probability",
            "Built_Probability",
            "Cooling_Priority_Score",
            "Cooling_Priority",
            "Recommended_Canopy_Increase_Percent"
        ]
    ].to_string(
        index=False
    )
)

output_columns = [
    "date",
    "latitude",
    "longitude",
    "LST",
    "Predicted_LST",
    "Heat_Class",
    "Heat_Score",
    "Tree_Probability",
    "Tree_Deficit",
    "Built_Probability",
    "Built_Score",
    "L_NDVI",
    "S2_NDVI",
    "Vegetation_Deficit",
    "Distance_To_Water",
    "Water_Distance_Score",
    "Albedo",
    "Albedo_Heat_Score",
    "Cooling_Priority_Score",
    "Cooling_Priority",
    "Canopy_Deficit",
    "Recommended_Canopy_Increase_Percent",
    "Recommendation"
]

available_columns = [
    column
    for column in output_columns
    if column in df.columns
]

df[
    available_columns
].to_csv(
    output_file,
    index=False
)

print(
    "\nCooling recommendation dataset saved successfully."
)

print(
    "Saved at:"
)

print(
    output_file
)