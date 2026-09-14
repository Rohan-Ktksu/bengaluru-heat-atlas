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

v1_file = (
    project_folder
    / "src"
    / "bengaluru_multidate_ml_dataset.csv"
)

v2_file = (
    project_folder
    / "src"
    / "bengaluru_multidate_enhanced_ml_dataset.csv"
)

v3_file = (
    project_folder
    / "src"
    / "bengaluru_multidate_v3_ml_dataset.csv"
)

v1_df = pd.read_csv(v1_file)
v2_df = pd.read_csv(v2_file)
v3_df = pd.read_csv(v3_file)

v1_features = [
    "L_NDVI",
    "NDBI",
    "NDWI",
    "S2_NDVI",
    "Air_Temp",
    "Wind_Speed",
    "Relative_Humidity"
]

v2_features = [
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


def train_and_evaluate(
    df,
    features,
    model_name
):

    df = df.dropna(
        subset=features + ["LST", "year"]
    )

    train_df = df[
        df["year"] <= 2025
    ].copy()

    test_df = df[
        df["year"] == 2026
    ].copy()

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

    print(
        "\n",
        model_name
    )

    print(
        "Features:",
        len(features)
    )

    print(
        "Training rows:",
        len(train_df)
    )

    print(
        "Testing rows:",
        len(test_df)
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

    importance = pd.DataFrame({
        "Feature": features,
        "Importance": model.feature_importances_
    })

    importance = importance.sort_values(
        "Importance",
        ascending=False
    )

    print(
        "\nFeature importance:"
    )

    print(
        importance
    )

    return {
        "Model": model_name,
        "Features": len(features),
        "Train_Rows": len(train_df),
        "Test_Rows": len(test_df),
        "MAE": mae,
        "RMSE": rmse,
        "R2": r2
    }


v1_result = train_and_evaluate(
    v1_df,
    v1_features,
    "V1 Baseline"
)

v2_result = train_and_evaluate(
    v2_df,
    v2_features,
    "V2 Enhanced"
)

v3_result = train_and_evaluate(
    v3_df,
    v3_features,
    "V3 Atmospheric History"
)

results = pd.DataFrame([
    v1_result,
    v2_result,
    v3_result
])

print(
    "\nFinal model comparison:"
)

print(
    results[
        [
            "Model",
            "Features",
            "MAE",
            "RMSE",
            "R2"
        ]
    ]
)

best_model = results.loc[
    results["RMSE"].idxmin()
]

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