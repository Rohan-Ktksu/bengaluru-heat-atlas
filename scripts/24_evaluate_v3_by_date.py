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

csv_file = (
    project_folder
    / "src"
    / "bengaluru_multidate_v3_ml_dataset.csv"
)

df = pd.read_csv(csv_file)

features = [
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

df = df.dropna(
    subset=features + [
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

print("Training rows:")
print(len(train_df))

print("\nTesting rows:")
print(len(test_df))

print("\n2026 test dates:")
print(
    test_df["date"]
    .value_counts()
    .sort_index()
)

X_train = train_df[features]
y_train = train_df["LST"]

X_test = test_df[features]
y_test = test_df["LST"]

model = RandomForestRegressor(
    n_estimators=200,
    random_state=42,
    n_jobs=-1
)

print("\nTraining V3 model...")

model.fit(
    X_train,
    y_train
)

print("Model training completed.")

test_df["Predicted_LST"] = model.predict(
    X_test
)

overall_mae = mean_absolute_error(
    y_test,
    test_df["Predicted_LST"]
)

overall_rmse = np.sqrt(
    mean_squared_error(
        y_test,
        test_df["Predicted_LST"]
    )
)

overall_r2 = r2_score(
    y_test,
    test_df["Predicted_LST"]
)

print("\nOverall 2026 performance:")

print("MAE:", overall_mae)
print("RMSE:", overall_rmse)
print("R2:", overall_r2)

results = []

for date, date_df in test_df.groupby("date"):

    actual = date_df["LST"]
    predicted = date_df["Predicted_LST"]

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

    if len(date_df) > 1:

        r2 = r2_score(
            actual,
            predicted
        )

    else:

        r2 = np.nan

    mean_actual = actual.mean()

    mean_predicted = predicted.mean()

    bias = (
        mean_predicted
        - mean_actual
    )

    results.append({
        "Date": date,
        "Samples": len(date_df),
        "Actual_Mean_LST": mean_actual,
        "Predicted_Mean_LST": mean_predicted,
        "Bias": bias,
        "MAE": mae,
        "RMSE": rmse,
        "R2": r2
    })

date_results = pd.DataFrame(
    results
)

date_results = date_results.sort_values(
    "Date"
)

print("\nPerformance by 2026 Landsat date:")

print(
    date_results.to_string(
        index=False
    )
)

print("\nBest date by MAE:")

best_date = date_results.loc[
    date_results["MAE"].idxmin()
]

print(best_date)

print("\nWorst date by MAE:")

worst_date = date_results.loc[
    date_results["MAE"].idxmax()
]

print(worst_date)

output_file = (
    project_folder
    / "src"
    / "v3_2026_date_evaluation.csv"
)

date_results.to_csv(
    output_file,
    index=False
)

prediction_file = (
    project_folder
    / "src"
    / "v3_2026_predictions.csv"
)

columns_to_save = [
    "date",
    "latitude",
    "longitude",
    "LST",
    "Predicted_LST"
]

test_df[
    columns_to_save
].to_csv(
    prediction_file,
    index=False
)

print("\nEvaluation saved at:")
print(output_file)

print("\nPredictions saved at:")
print(prediction_file)