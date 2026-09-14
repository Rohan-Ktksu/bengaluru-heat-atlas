import pandas as pd
import numpy as np
from pathlib import Path

script_folder = Path(__file__).resolve().parent
project_folder = script_folder.parent

old_file = (
    project_folder
    / "src"
    / "bengaluru_persistent_hotspot_tree_plan.csv"
)

new_file = (
    project_folder
    / "src"
    / "bengaluru_complete_persistent_heat.csv"
)

output_file = (
    project_folder
    / "src"
    / "complete_grid_validation.csv"
)

old_df = pd.read_csv(old_file)
new_df = pd.read_csv(new_file)

print("Original reliable dataset:")
print(len(old_df))

print("\nComplete prediction dataset:")
print(len(new_df))

old_columns = [
    "Grid_ID",
    "Median_Predicted_LST",
    "Hot_Frequency",
    "Very_Hot_Frequency",
    "Persistent_Heat_Score",
    "Persistent_Cooling_Priority"
]

old = old_df[old_columns].copy()

old = old.rename(
    columns={
        "Median_Predicted_LST": "Old_Median_LST",
        "Hot_Frequency": "Old_Hot_Frequency",
        "Very_Hot_Frequency": "Old_Very_Hot_Frequency",
        "Persistent_Heat_Score": "Old_Heat_Score",
        "Persistent_Cooling_Priority": "Old_Priority"
    }
)

new_columns = [
    "Grid_ID",
    "Median_Predicted_LST",
    "Hot_Frequency",
    "Very_Hot_Frequency",
    "Persistent_Heat_Score",
    "Persistent_Cooling_Priority",
    "Historical_Unique_Dates",
    "Observation_Support"
]

new = new_df[new_columns].copy()

new = new.rename(
    columns={
        "Median_Predicted_LST": "New_Median_LST",
        "Hot_Frequency": "New_Hot_Frequency",
        "Very_Hot_Frequency": "New_Very_Hot_Frequency",
        "Persistent_Heat_Score": "New_Heat_Score",
        "Persistent_Cooling_Priority": "New_Priority"
    }
)

comparison = old.merge(
    new,
    on="Grid_ID",
    how="inner"
)

print("\nReliable cells matched:")
print(len(comparison))

comparison["LST_Difference"] = (
    comparison["New_Median_LST"]
    - comparison["Old_Median_LST"]
)

comparison["Absolute_LST_Difference"] = (
    comparison["LST_Difference"].abs()
)

comparison["Hot_Frequency_Difference"] = (
    comparison["New_Hot_Frequency"]
    - comparison["Old_Hot_Frequency"]
)

comparison["Very_Hot_Frequency_Difference"] = (
    comparison["New_Very_Hot_Frequency"]
    - comparison["Old_Very_Hot_Frequency"]
)

comparison["Priority_Match"] = (
    comparison["Old_Priority"]
    == comparison["New_Priority"]
)

mae = (
    comparison["Absolute_LST_Difference"]
    .mean()
)

rmse = np.sqrt(
    np.mean(
        comparison["LST_Difference"] ** 2
    )
)

correlation = (
    comparison[
        [
            "Old_Median_LST",
            "New_Median_LST"
        ]
    ]
    .corr()
    .iloc[0, 1]
)

priority_match_percent = (
    comparison["Priority_Match"]
    .mean()
    * 100
)

print("\nMedian LST comparison:")

print("MAE:", mae)
print("RMSE:", rmse)
print("Correlation:", correlation)

print("\nPriority exact-match percentage:")
print(priority_match_percent)

print("\nPriority comparison:")

print(
    pd.crosstab(
        comparison["Old_Priority"],
        comparison["New_Priority"]
    )
)

print("\nMean absolute LST difference:")
print(
    comparison[
        "Absolute_LST_Difference"
    ].mean()
)

print("\nMedian absolute LST difference:")
print(
    comparison[
        "Absolute_LST_Difference"
    ].median()
)

print("\n90th percentile absolute difference:")
print(
    comparison[
        "Absolute_LST_Difference"
    ].quantile(0.90)
)

print("\nMean hot-frequency difference:")
print(
    comparison[
        "Hot_Frequency_Difference"
    ].mean()
)

print("\nMean very-hot-frequency difference:")
print(
    comparison[
        "Very_Hot_Frequency_Difference"
    ].mean()
)

print("\nLargest disagreements:")

largest = (
    comparison
    .sort_values(
        "Absolute_LST_Difference",
        ascending=False
    )
    .head(20)
)

print(
    largest[
        [
            "Grid_ID",
            "Historical_Unique_Dates",
            "Observation_Support",
            "Old_Median_LST",
            "New_Median_LST",
            "LST_Difference",
            "Old_Priority",
            "New_Priority",
            "Priority_Match"
        ]
    ]
    .to_string(
        index=False
    )
)

comparison.to_csv(
    output_file,
    index=False
)

print("\nValidation saved at:")
print(output_file)