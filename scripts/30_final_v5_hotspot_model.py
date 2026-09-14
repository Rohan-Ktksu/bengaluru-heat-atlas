import pandas as pd
import numpy as np
import joblib
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

model_file = (
    project_folder
    / "models"
    / "urban_heat_model_v5.pkl"
)

output_file = (
    project_folder
    / "src"
    / "v5_2026_hotspot_predictions.csv"
)

model_file.parent.mkdir(
    parents=True,
    exist_ok=True
)

df = pd.read_csv(
    dataset_file
)

print("V5 dataset loaded.")

print("\nTotal rows:")
print(len(df))

print("\nUnique dates:")
print(df["date"].nunique())

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
    features
    + [
        "LST",
        "year",
        "date",
        "latitude",
        "longitude"
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

X_train = train_df[
    features
]

y_train = train_df[
    "LST"
]

X_test = test_df[
    features
]

y_test = test_df[
    "LST"
]

print(
    "\nTraining final V5 model..."
)

model = RandomForestRegressor(
    n_estimators=200,
    random_state=42,
    n_jobs=-1
)

model.fit(
    X_train,
    y_train
)

print(
    "Model training completed."
)

predictions = model.predict(
    X_test
)

test_df[
    "Predicted_LST"
] = predictions

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

print(
    "\nFinal V5 performance:"
)

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

joblib.dump(
    {
        "model": model,
        "features": features
    },
    model_file
)

print(
    "\nFinal V5 model saved at:"
)

print(
    model_file
)

low_threshold = (
    test_df[
        "Predicted_LST"
    ]
    .quantile(
        0.25
    )
)

high_threshold = (
    test_df[
        "Predicted_LST"
    ]
    .quantile(
        0.75
    )
)

very_high_threshold = (
    test_df[
        "Predicted_LST"
    ]
    .quantile(
        0.90
    )
)

print(
    "\nHotspot thresholds:"
)

print(
    "Low/Moderate:",
    low_threshold
)

print(
    "Moderate/High:",
    high_threshold
)

print(
    "High/Very High:",
    very_high_threshold
)

def classify_heat(
    temperature
):

    if temperature < low_threshold:

        return "Low"

    elif temperature < high_threshold:

        return "Moderate"

    elif temperature < very_high_threshold:

        return "High"

    else:

        return "Very High"


test_df[
    "Heat_Class"
] = (
    test_df[
        "Predicted_LST"
    ]
    .apply(
        classify_heat
    )
)

test_df[
    "Prediction_Error"
] = (
    test_df[
        "Predicted_LST"
    ]
    - test_df[
        "LST"
    ]
)

test_df[
    "Absolute_Error"
] = (
    test_df[
        "Prediction_Error"
    ]
    .abs()
)

print(
    "\nHeat class distribution:"
)

print(
    test_df[
        "Heat_Class"
    ]
    .value_counts()
)

print(
    "\nMean predicted LST by heat class:"
)

print(
    test_df
    .groupby(
        "Heat_Class"
    )[
        "Predicted_LST"
    ]
    .mean()
    .sort_values()
)

output_columns = [
    "date",
    "latitude",
    "longitude",
    "LST",
    "Predicted_LST",
    "Prediction_Error",
    "Absolute_Error",
    "Heat_Class",
    "L_NDVI",
    "S2_NDVI",
    "NDBI",
    "NDWI",
    "Tree_Probability",
    "Built_Probability",
    "Albedo",
    "Distance_To_Water",
    "Elevation",
    "Soil_Moisture",
    "Air_Temp",
    "Overpass_Air_Temp"
]

test_df[
    output_columns
].to_csv(
    output_file,
    index=False
)

print(
    "\nHotspot predictions saved at:"
)

print(
    output_file
)

print(
    "\nFirst 10 hotspot predictions:"
)

print(
    test_df[
        [
            "date",
            "latitude",
            "longitude",
            "Predicted_LST",
            "Heat_Class"
        ]
    ]
    .head(
        10
    )
    .to_string(
        index=False
    )
)