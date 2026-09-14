import pandas as pd
import numpy as np
from pathlib import Path

script_folder = Path(__file__).resolve().parent
project_folder = script_folder.parent

input_file = (
    project_folder
    / "src"
    / "bengaluru_hybrid_heat_grid.csv"
)

output_file = (
    project_folder
    / "src"
    / "bengaluru_final_cooling_tree_plan.csv"
)

df = pd.read_csv(input_file)

print("Hybrid heat grid loaded.")

print("\nTotal cells:")
print(len(df))

required_columns = [
    "Grid_ID",
    "Final_Median_LST",
    "Final_Hot_Frequency",
    "Final_Tree_Probability",
    "Final_Built_Probability",
    "Final_Cooling_Priority",
    "Hybrid_Heat_Score",
    "Data_Source",
    "Confidence_Level"
]

df = df.dropna(
    subset=required_columns
).copy()

print("\nUsable cells:")
print(len(df))

cell_area_m2 = 1000000
cell_area_hectares = 100

df["Cell_Area_m2"] = cell_area_m2
df["Cell_Area_hectares"] = cell_area_hectares


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


df["Min_Greening_Fraction"] = (
    df["Final_Cooling_Priority"]
    .apply(minimum_greening)
)

df["Max_Greening_Fraction"] = (
    df["Final_Cooling_Priority"]
    .apply(maximum_greening)
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


df["Tree_Need_Score"] = (
    1
    - normalize(
        df["Final_Tree_Probability"]
    )
)

df["Built_Intensity_Score"] = (
    normalize(
        df["Final_Built_Probability"]
    )
)

df["Heat_Need_Score"] = (
    normalize(
        df["Hybrid_Heat_Score"]
    )
)

df["Need_Factor"] = (
    0.40
    * df["Heat_Need_Score"]
    +
    0.35
    * df["Tree_Need_Score"]
    +
    0.25
    * df["Built_Intensity_Score"]
)

df["Suggested_Greening_Fraction"] = (
    df["Min_Greening_Fraction"]
    +
    (
        df["Max_Greening_Fraction"]
        - df["Min_Greening_Fraction"]
    )
    * df["Need_Factor"]
)

df["Suggested_Greening_Percent"] = (
    df["Suggested_Greening_Fraction"]
    * 100
)

df["Total_Cooling_Area_m2"] = (
    df["Cell_Area_m2"]
    * df["Suggested_Greening_Fraction"]
)


def tree_share(row):

    built = row["Final_Built_Probability"]

    if built >= 0.70:
        return 0.35

    elif built >= 0.50:
        return 0.50

    elif built >= 0.30:
        return 0.70

    else:
        return 0.85


df["Tree_Cooling_Share"] = (
    df.apply(
        tree_share,
        axis=1
    )
)

df["Tree_Canopy_Target_m2"] = (
    df["Total_Cooling_Area_m2"]
    * df["Tree_Cooling_Share"]
)

df["Non_Tree_Cooling_Area_m2"] = (
    df["Total_Cooling_Area_m2"]
    - df["Tree_Canopy_Target_m2"]
)

average_mature_canopy_per_tree_m2 = 30

df[
    "Assumed_Mature_Canopy_Per_Tree_m2"
] = average_mature_canopy_per_tree_m2

df["Approx_Trees_To_Plant"] = (
    np.ceil(
        df["Tree_Canopy_Target_m2"]
        / average_mature_canopy_per_tree_m2
    )
    .astype(int)
)

df["Trees_Per_Hectare"] = (
    df["Approx_Trees_To_Plant"]
    / df["Cell_Area_hectares"]
)


def intervention_type(row):

    built = row["Final_Built_Probability"]
    priority = row["Final_Cooling_Priority"]

    if priority == "Very High":

        if built >= 0.70:

            return (
                "Street trees + pocket parks + "
                "green roofs + cool roofs + "
                "reflective pavement"
            )

        elif built >= 0.50:

            return (
                "Street-tree corridors + pocket parks + "
                "green roofs + shaded public spaces"
            )

        else:

            return (
                "Large canopy expansion + urban forest + "
                "park restoration + shaded corridors"
            )

    elif priority == "High":

        if built >= 0.60:

            return (
                "Street trees + green roofs + "
                "cool roofs + shaded corridors"
            )

        else:

            return (
                "Tree canopy expansion + parks + "
                "connected green corridors"
            )

    elif priority == "Moderate":

        return (
            "Targeted tree planting + vegetation protection + "
            "local shade improvement"
        )

    else:

        return (
            "Maintain existing vegetation and "
            "monitor heat conditions"
        )


df["Recommended_Intervention"] = (
    df.apply(
        intervention_type,
        axis=1
    )
)


def planning_reliability(row):

    source = row["Data_Source"]

    if source == "Reliable Multi-Date Observation":

        if row["Confidence_Level"] in [
            "Very High",
            "High"
        ]:

            return "Strong"

        return "Moderate"

    elif source == "Limited Observation + V5":

        return "Limited"

    else:

        return "Model Only"


df["Planning_Reliability"] = (
    df.apply(
        planning_reliability,
        axis=1
    )
)

print("\nFinal priority distribution:")

print(
    df[
        "Final_Cooling_Priority"
    ]
    .value_counts()
)

print("\nEstimated trees by priority:")

print(
    df.groupby(
        "Final_Cooling_Priority"
    )[
        "Approx_Trees_To_Plant"
    ]
    .sum()
)

print("\nAverage trees per hectare:")

print(
    df.groupby(
        "Final_Cooling_Priority"
    )[
        "Trees_Per_Hectare"
    ]
    .mean()
)

print("\nTotal tree estimate:")

print(
    int(
        df[
            "Approx_Trees_To_Plant"
        ]
        .sum()
    )
)

print("\nTotal tree-canopy target area:")

print(
    df[
        "Tree_Canopy_Target_m2"
    ]
    .sum()
)

print("\nTotal non-tree cooling area:")

print(
    df[
        "Non_Tree_Cooling_Area_m2"
    ]
    .sum()
)

print("\nPlanning reliability:")

print(
    df[
        "Planning_Reliability"
    ]
    .value_counts()
)

top = (
    df.sort_values(
        "Hybrid_Heat_Score",
        ascending=False
    )
    .head(20)
)

print("\nTop 20 intervention areas:")

print(
    top[
        [
            "Grid_ID",
            "Center_Latitude",
            "Center_Longitude",
            "Final_Median_LST",
            "Final_Hot_Frequency",
            "Final_Tree_Probability",
            "Final_Built_Probability",
            "Hybrid_Heat_Score",
            "Final_Cooling_Priority",
            "Suggested_Greening_Percent",
            "Tree_Cooling_Share",
            "Approx_Trees_To_Plant",
            "Trees_Per_Hectare",
            "Planning_Reliability",
            "Recommended_Intervention"
        ]
    ]
    .to_string(
        index=False
    )
)

df.to_csv(
    output_file,
    index=False
)

print("\nSTEP 41 COMPLETE")

print("\nSaved at:")
print(output_file)