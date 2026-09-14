import pandas as pd
import numpy as np
from pathlib import Path

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

script_folder = Path(__file__).resolve().parent
project_folder = script_folder.parent

dataset_file = (
    project_folder
    / "src"
    / "bengaluru_multidate_v5_overpass_ml_dataset.csv"
)

comparison_file = (
    project_folder
    / "src"
    / "v3_v4_v5_model_comparison.csv"
)

date_file = (
    project_folder
    / "src"
    / "v3_v4_v5_date_comparison.csv"
)

importance_file = (
    project_folder
    / "src"
    / "v5_feature_importance.csv"
)

prediction_file = (
    project_folder
    / "src"
    / "v5_2026_predictions.csv"
)

df = pd.read_csv(dataset_file)

print("V5 dataset loaded.")

print("\nTotal rows:")
print(len(df))

print("\nUnique dates:")
print(df["date"].nunique())

v3_features = [
    "L_NDVI",
    "NDBI",
    "NDWI",
    "S2_NDVI",
    "Air_Temp",
    "Wind_Speed",
    "Relative_Humidity",
    "Soil_Moisture",
    "Daily_Precipitation",
    "Precip_3Day",
    "Precip_7Day",
    "Solar_Radiation",
    "Cloud_Cover",
    "Air_Temp_3Day",
    "Air_Temp_7Day"
]

v4_features = [
    "L_NDVI",
    "NDBI",
    "NDWI",
    "S2_NDVI",
    "Air_Temp",
    "Wind_Speed",
    "Relative_Humidity",
    "Soil_Moisture",
    "Daily_Precipitation",
    "Precip_3Day",
    "Precip_7Day",
    "Solar_Radiation",
    "Cloud_Cover",
    "Air_Temp_3Day",
    "Air_Temp_7Day",
    "Elevation",
    "Built_Probability",
    "Tree_Probability",
    "Albedo",
    "Distance_To_Water"
]

v5_features = [
    "L_NDVI",
    "NDBI",
    "NDWI",
    "S2_NDVI",
    "Air_Temp",
    "Wind_Speed",
    "Relative_Humidity",
    "Soil_Moisture",
    "Daily_Precipitation",
    "Precip_3Day",
    "Precip_7Day",
    "Solar_Radiation",
    "Cloud_Cover",
    "Air_Temp_3Day",
    "Air_Temp_7Day",
    "Elevation",
    "Built_Probability",
    "Tree_Probability",
    "Albedo",
    "Distance_To_Water",
    "Overpass_Air_Temp",
    "Overpass_Relative_Humidity",
    "Overpass_Wind_Speed",
    "Overpass_Solar_Radiation",
    "Overpass_Cloud_Cover"
]

required_columns = (
    v5_features
    + [
        "LST",
        "year",
        "date"
    ]
)

df = df.dropna(
    subset=required_columns
).copy()

print("\nUsable rows:")
print(len(df))

train_df = df[
    df["year"] <= 2025
].copy()

test_df = df[
    df["year"] == 2026
].copy()

print("\nTraining rows:")
print(len(train_df))

print("\nTesting rows:")
print(len(test_df))

print("\n2026 test dates:")

print(
    test_df["date"]
    .value_counts()
    .sort_index()
)

y_train = train_df["LST"]
y_test = test_df["LST"]

models = {}

results = []

model_definitions = {
    "V3 Atmospheric History": v3_features,
    "V4 Spatial": v4_features,
    "V5 Overpass": v5_features
}

for model_name, features in model_definitions.items():

    print(
        "\nTraining:",
        model_name
    )

    X_train = train_df[
        features
    ]

    X_test = test_df[
        features
    ]

    model = RandomForestRegressor(
        n_estimators=200,
        random_state=42,
        n_jobs=-1
    )

    model.fit(
        X_train,
        y_train
    )

    predictions = model.predict(
        X_test
    )

    mae = mean_absolute_error(
        y_test,
        predictions
    )

    rmse = np.sqrt(
        mean_squared_error(
            y_test,
            predictions
        )
    )

    r2 = r2_score(
        y_test,
        predictions
    )

    models[model_name] = {
        "model": model,
        "features": features,
        "predictions": predictions
    }

    results.append({
        "Model": model_name,
        "Features": len(features),
        "MAE": mae,
        "RMSE": rmse,
        "R2": r2
    })

    print(
        "MAE:",
        mae
    )

    print(
        "RMSE:",
        rmse
    )

    print(
        "R2:",
        r2
    )

comparison = pd.DataFrame(
    results
)

comparison = comparison.sort_values(
    "RMSE"
)

print(
    "\nFinal model comparison:"
)

print(
    comparison.to_string(
        index=False
    )
)

best_model = comparison.iloc[0]

print(
    "\nBest model based on RMSE:"
)

print(
    best_model["Model"]
)

print(
    "Best MAE:",
    best_model["MAE"]
)

print(
    "Best RMSE:",
    best_model["RMSE"]
)

print(
    "Best R2:",
    best_model["R2"]
)

v5_model = models[
    "V5 Overpass"
]["model"]

v5_importance = pd.DataFrame({
    "Feature": v5_features,
    "Importance": v5_model.feature_importances_
})

v5_importance = (
    v5_importance
    .sort_values(
        "Importance",
        ascending=False
    )
)

print(
    "\nV5 feature importance:"
)

print(
    v5_importance.to_string(
        index=False
    )
)

test_df[
    "V3_Predicted_LST"
] = models[
    "V3 Atmospheric History"
]["predictions"]

test_df[
    "V4_Predicted_LST"
] = models[
    "V4 Spatial"
]["predictions"]

test_df[
    "V5_Predicted_LST"
] = models[
    "V5 Overpass"
]["predictions"]

date_results = []

for date, date_df in test_df.groupby(
    "date"
):

    actual = date_df[
        "LST"
    ]

    row = {
        "Date": date,
        "Samples": len(date_df),
        "Actual_Mean_LST": actual.mean()
    }

    for short_name in [
        "V3",
        "V4",
        "V5"
    ]:

        prediction_column = (
            short_name
            + "_Predicted_LST"
        )

        predicted = date_df[
            prediction_column
        ]

        mae = mean_absolute_error(
            actual,
            predicted
        )

        rmse = np.sqrt(
            mean_squared_error(
                actual,
                predicted
            )
        )

        r2 = r2_score(
            actual,
            predicted
        )

        bias = (
            predicted.mean()
            - actual.mean()
        )

        row[
            short_name
            + "_Predicted_Mean_LST"
        ] = predicted.mean()

        row[
            short_name
            + "_Bias"
        ] = bias

        row[
            short_name
            + "_MAE"
        ] = mae

        row[
            short_name
            + "_RMSE"
        ] = rmse

        row[
            short_name
            + "_R2"
        ] = r2

    date_results.append(
        row
    )

date_results_df = pd.DataFrame(
    date_results
)

date_results_df = (
    date_results_df
    .sort_values(
        "Date"
    )
)

print(
    "\nDate-by-date comparison:"
)

print(
    date_results_df.to_string(
        index=False
    )
)

april17 = date_results_df[
    date_results_df[
        "Date"
    ].astype(str)
    == "2026-04-17"
]

if len(april17) > 0:

    print(
        "\nApril 17 comparison:"
    )

    print(
        april17.to_string(
            index=False
        )
    )

comparison.to_csv(
    comparison_file,
    index=False
)

date_results_df.to_csv(
    date_file,
    index=False
)

v5_importance.to_csv(
    importance_file,
    index=False
)

prediction_columns = [
    "date",
    "latitude",
    "longitude",
    "LST",
    "V3_Predicted_LST",
    "V4_Predicted_LST",
    "V5_Predicted_LST"
]

available_prediction_columns = [
    column
    for column in prediction_columns
    if column in test_df.columns
]

test_df[
    available_prediction_columns
].to_csv(
    prediction_file,
    index=False
)

print(
    "\nModel comparison saved at:"
)

print(
    comparison_file
)

print(
    "\nDate comparison saved at:"
)

print(
    date_file
)

print(
    "\nV5 feature importance saved at:"
)

print(
    importance_file
)

print(
    "\nV5 predictions saved at:"
)

print(
    prediction_file
)