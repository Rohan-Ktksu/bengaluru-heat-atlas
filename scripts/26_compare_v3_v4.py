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

v4_file = (
    project_folder
    / "src"
    / "bengaluru_multidate_v4_spatial_ml_dataset.csv"
)

df = pd.read_csv(v4_file)

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

df = df.dropna(
    subset=v4_features + [
        "LST",
        "year",
        "date"
    ]
)

train_df = df[
    df["year"] <= 2025
].copy()

test_df = df[
    df["year"] == 2026
].copy()

print("Total usable rows:")
print(len(df))

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

X_train_v3 = train_df[
    v3_features
]

X_test_v3 = test_df[
    v3_features
]

X_train_v4 = train_df[
    v4_features
]

X_test_v4 = test_df[
    v4_features
]

y_train = train_df[
    "LST"
]

y_test = test_df[
    "LST"
]

v3_model = RandomForestRegressor(
    n_estimators=200,
    random_state=42,
    n_jobs=-1
)

v4_model = RandomForestRegressor(
    n_estimators=200,
    random_state=42,
    n_jobs=-1
)

print("\nTraining V3 feature model...")

v3_model.fit(
    X_train_v3,
    y_train
)

print("Training V4 spatial model...")

v4_model.fit(
    X_train_v4,
    y_train
)

v3_predictions = v3_model.predict(
    X_test_v3
)

v4_predictions = v4_model.predict(
    X_test_v4
)

v3_mae = mean_absolute_error(
    y_test,
    v3_predictions
)

v3_rmse = np.sqrt(
    mean_squared_error(
        y_test,
        v3_predictions
    )
)

v3_r2 = r2_score(
    y_test,
    v3_predictions
)

v4_mae = mean_absolute_error(
    y_test,
    v4_predictions
)

v4_rmse = np.sqrt(
    mean_squared_error(
        y_test,
        v4_predictions
    )
)

v4_r2 = r2_score(
    y_test,
    v4_predictions
)

print("\nV3 features on common V4 dataset")

print(
    "MAE:",
    v3_mae
)

print(
    "RMSE:",
    v3_rmse
)

print(
    "R2:",
    v3_r2
)

print("\nV4 spatial model")

print(
    "MAE:",
    v4_mae
)

print(
    "RMSE:",
    v4_rmse
)

print(
    "R2:",
    v4_r2
)

comparison = pd.DataFrame({
    "Model": [
        "V3 Common Dataset",
        "V4 Spatial"
    ],
    "Features": [
        len(v3_features),
        len(v4_features)
    ],
    "MAE": [
        v3_mae,
        v4_mae
    ],
    "RMSE": [
        v3_rmse,
        v4_rmse
    ],
    "R2": [
        v3_r2,
        v4_r2
    ]
})

print("\nOverall comparison:")

print(
    comparison
)

importance = pd.DataFrame({
    "Feature": v4_features,
    "Importance": v4_model.feature_importances_
})

importance = importance.sort_values(
    "Importance",
    ascending=False
)

print("\nV4 feature importance:")

print(
    importance.to_string(
        index=False
    )
)

test_df["V3_Predicted_LST"] = (
    v3_predictions
)

test_df["V4_Predicted_LST"] = (
    v4_predictions
)

date_results = []

for date, date_df in test_df.groupby(
    "date"
):

    actual = date_df[
        "LST"
    ]

    v3_pred = date_df[
        "V3_Predicted_LST"
    ]

    v4_pred = date_df[
        "V4_Predicted_LST"
    ]

    v3_date_mae = mean_absolute_error(
        actual,
        v3_pred
    )

    v3_date_rmse = np.sqrt(
        mean_squared_error(
            actual,
            v3_pred
        )
    )

    v3_date_r2 = r2_score(
        actual,
        v3_pred
    )

    v4_date_mae = mean_absolute_error(
        actual,
        v4_pred
    )

    v4_date_rmse = np.sqrt(
        mean_squared_error(
            actual,
            v4_pred
        )
    )

    v4_date_r2 = r2_score(
        actual,
        v4_pred
    )

    v3_bias = (
        v3_pred.mean()
        - actual.mean()
    )

    v4_bias = (
        v4_pred.mean()
        - actual.mean()
    )

    date_results.append({
        "Date": date,
        "Samples": len(date_df),

        "V3_MAE": v3_date_mae,
        "V3_RMSE": v3_date_rmse,
        "V3_R2": v3_date_r2,
        "V3_Bias": v3_bias,

        "V4_MAE": v4_date_mae,
        "V4_RMSE": v4_date_rmse,
        "V4_R2": v4_date_r2,
        "V4_Bias": v4_bias
    })

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

comparison_file = (
    project_folder
    / "src"
    / "v3_v4_model_comparison.csv"
)

comparison.to_csv(
    comparison_file,
    index=False
)

date_file = (
    project_folder
    / "src"
    / "v3_v4_date_comparison.csv"
)

date_results_df.to_csv(
    date_file,
    index=False
)

importance_file = (
    project_folder
    / "src"
    / "v4_feature_importance.csv"
)

importance.to_csv(
    importance_file,
    index=False
)

print(
    "\nComparison saved at:"
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
    "\nV4 feature importance saved at:"
)

print(
    importance_file
)