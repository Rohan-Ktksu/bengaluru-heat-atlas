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

baseline_file = (
    project_folder
    / "src"
    / "bengaluru_multidate_ml_dataset.csv"
)

enhanced_file = (
    project_folder
    / "src"
    / "bengaluru_multidate_enhanced_ml_dataset.csv"
)

baseline_df = pd.read_csv(
    baseline_file
)

enhanced_df = pd.read_csv(
    enhanced_file
)

baseline_features = [
    "L_NDVI",
    "NDBI",
    "NDWI",
    "S2_NDVI",
    "Air_Temp",
    "Wind_Speed",
    "Relative_Humidity"
]

enhanced_features = [
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
    "Precip_7Day"
]

baseline_df = baseline_df.dropna(
    subset=baseline_features + ["LST"]
)

enhanced_df = enhanced_df.dropna(
    subset=enhanced_features + ["LST"]
)

baseline_train = baseline_df[
    baseline_df["year"] <= 2025
]

baseline_test = baseline_df[
    baseline_df["year"] == 2026
]

enhanced_train = enhanced_df[
    enhanced_df["year"] <= 2025
]

enhanced_test = enhanced_df[
    enhanced_df["year"] == 2026
]

X_train_baseline = baseline_train[
    baseline_features
]

y_train_baseline = baseline_train[
    "LST"
]

X_test_baseline = baseline_test[
    baseline_features
]

y_test_baseline = baseline_test[
    "LST"
]

X_train_enhanced = enhanced_train[
    enhanced_features
]

y_train_enhanced = enhanced_train[
    "LST"
]

X_test_enhanced = enhanced_test[
    enhanced_features
]

y_test_enhanced = enhanced_test[
    "LST"
]

baseline_model = RandomForestRegressor(
    n_estimators=200,
    random_state=42,
    n_jobs=-1
)

enhanced_model = RandomForestRegressor(
    n_estimators=200,
    random_state=42,
    n_jobs=-1
)

baseline_model.fit(
    X_train_baseline,
    y_train_baseline
)

enhanced_model.fit(
    X_train_enhanced,
    y_train_enhanced
)

baseline_predictions = baseline_model.predict(
    X_test_baseline
)

enhanced_predictions = enhanced_model.predict(
    X_test_enhanced
)

baseline_mae = mean_absolute_error(
    y_test_baseline,
    baseline_predictions
)

baseline_rmse = np.sqrt(
    mean_squared_error(
        y_test_baseline,
        baseline_predictions
    )
)

baseline_r2 = r2_score(
    y_test_baseline,
    baseline_predictions
)

enhanced_mae = mean_absolute_error(
    y_test_enhanced,
    enhanced_predictions
)

enhanced_rmse = np.sqrt(
    mean_squared_error(
        y_test_enhanced,
        enhanced_predictions
    )
)

enhanced_r2 = r2_score(
    y_test_enhanced,
    enhanced_predictions
)

print("\nBaseline model")

print(
    "Training rows:",
    len(baseline_train)
)

print(
    "Testing rows:",
    len(baseline_test)
)

print(
    "MAE:",
    baseline_mae
)

print(
    "RMSE:",
    baseline_rmse
)

print(
    "R2:",
    baseline_r2
)

print("\nEnhanced model")

print(
    "Training rows:",
    len(enhanced_train)
)

print(
    "Testing rows:",
    len(enhanced_test)
)

print(
    "MAE:",
    enhanced_mae
)

print(
    "RMSE:",
    enhanced_rmse
)

print(
    "R2:",
    enhanced_r2
)

results = pd.DataFrame({
    "Model": [
        "Baseline",
        "Enhanced"
    ],
    "MAE": [
        baseline_mae,
        enhanced_mae
    ],
    "RMSE": [
        baseline_rmse,
        enhanced_rmse
    ],
    "R2": [
        baseline_r2,
        enhanced_r2
    ]
})

print("\nModel comparison:")
print(results)

importance = pd.DataFrame({
    "Feature": enhanced_features,
    "Importance": enhanced_model.feature_importances_
})

importance = importance.sort_values(
    "Importance",
    ascending=False
)

print("\nEnhanced model feature importance:")
print(importance)