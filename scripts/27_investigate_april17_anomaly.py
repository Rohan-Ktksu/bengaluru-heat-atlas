import pandas as pd
import numpy as np
from pathlib import Path

script_folder = Path(__file__).resolve().parent
project_folder = script_folder.parent

dataset_file = (
    project_folder
    / "src"
    / "bengaluru_multidate_v4_spatial_ml_dataset.csv"
)

prediction_file = (
    project_folder
    / "src"
    / "v3_v4_date_comparison.csv"
)

output_file = (
    project_folder
    / "src"
    / "april17_anomaly_analysis.csv"
)

df = pd.read_csv(dataset_file)

df["date"] = pd.to_datetime(df["date"])

dates_to_check = pd.to_datetime([
    "2026-03-16",
    "2026-04-01",
    "2026-04-17",
    "2026-05-03"
])

features = [
    "LST",
    "Air_Temp",
    "Air_Temp_3Day",
    "Air_Temp_7Day",
    "Relative_Humidity",
    "Wind_Speed",
    "Soil_Moisture",
    "Daily_Precipitation",
    "Precip_3Day",
    "Precip_7Day",
    "Solar_Radiation",
    "Cloud_Cover",
    "L_NDVI",
    "S2_NDVI",
    "NDBI",
    "NDWI",
    "Albedo",
    "Built_Probability",
    "Tree_Probability",
    "Distance_To_Water",
    "Elevation"
]

available_features = [
    feature
    for feature in features
    if feature in df.columns
]

selected = df[
    df["date"].isin(dates_to_check)
].copy()

print("\nRows by date:")

print(
    selected["date"]
    .dt.strftime("%Y-%m-%d")
    .value_counts()
    .sort_index()
)

summary_rows = []

for date, group in selected.groupby("date"):

    row = {
        "Date": date.strftime("%Y-%m-%d"),
        "Samples": len(group)
    }

    for feature in available_features:

        row[f"{feature}_Mean"] = (
            group[feature].mean()
        )

        row[f"{feature}_Std"] = (
            group[feature].std()
        )

        row[f"{feature}_Min"] = (
            group[feature].min()
        )

        row[f"{feature}_Max"] = (
            group[feature].max()
        )

    summary_rows.append(row)

summary = pd.DataFrame(
    summary_rows
)

summary = summary.sort_values(
    "Date"
)

print("\nMean conditions by date:\n")

mean_columns = [
    "Date",
    "Samples"
]

for feature in available_features:

    mean_columns.append(
        f"{feature}_Mean"
    )

print(
    summary[
        mean_columns
    ].to_string(
        index=False
    )
)

target_date = pd.Timestamp(
    "2026-04-17"
)

target = selected[
    selected["date"] == target_date
]

other_dates = selected[
    selected["date"] != target_date
]

print(
    "\nApril 17 compared with surrounding dates:\n"
)

comparison_rows = []

for feature in available_features:

    april_mean = (
        target[feature].mean()
    )

    surrounding_mean = (
        other_dates[feature].mean()
    )

    surrounding_std = (
        other_dates[feature].std()
    )

    difference = (
        april_mean
        - surrounding_mean
    )

    if (
        pd.notna(surrounding_std)
        and surrounding_std != 0
    ):

        z_score = (
            difference
            / surrounding_std
        )

    else:

        z_score = np.nan

    if surrounding_mean != 0:

        percent_difference = (
            difference
            / abs(surrounding_mean)
        ) * 100

    else:

        percent_difference = np.nan

    comparison_rows.append({
        "Feature": feature,
        "April17_Mean": april_mean,
        "Surrounding_Mean": surrounding_mean,
        "Difference": difference,
        "Percent_Difference": percent_difference,
        "Z_Score": z_score
    })

comparison = pd.DataFrame(
    comparison_rows
)

comparison["Absolute_Z"] = (
    comparison["Z_Score"]
    .abs()
)

comparison = comparison.sort_values(
    "Absolute_Z",
    ascending=False
)

print(
    comparison[
        [
            "Feature",
            "April17_Mean",
            "Surrounding_Mean",
            "Difference",
            "Percent_Difference",
            "Z_Score"
        ]
    ].to_string(
        index=False
    )
)

print(
    "\nMost unusual April 17 variables:\n"
)

print(
    comparison[
        [
            "Feature",
            "Difference",
            "Z_Score"
        ]
    ]
    .head(10)
    .to_string(
        index=False
    )
)

if prediction_file.exists():

    prediction_results = pd.read_csv(
        prediction_file
    )

    april_prediction = prediction_results[
        prediction_results["Date"].astype(str)
        == "2026-04-17"
    ]

    if len(april_prediction) > 0:

        print(
            "\nApril 17 model performance:\n"
        )

        print(
            april_prediction.to_string(
                index=False
            )
        )

summary.to_csv(
    output_file,
    index=False
)

comparison_output = (
    project_folder
    / "src"
    / "april17_feature_anomalies.csv"
)

comparison.to_csv(
    comparison_output,
    index=False
)

print(
    "\nAnalysis saved at:"
)

print(
    output_file
)

print(
    "\nFeature anomaly ranking saved at:"
)

print(
    comparison_output
)