import pandas as pd
import numpy as np
import joblib
from pathlib import Path

script_folder = Path(__file__).resolve().parent
project_folder = script_folder.parent

input_file = (
    project_folder
    / "src"
    / "bengaluru_complete_v5_features.csv"
)
grid_file = (
    project_folder
    / "src"
    / "bengaluru_complete_1km_grid.csv"
)
model_file = (
    project_folder
    / "models"
    / "urban_heat_model_v5.pkl"
)

prediction_output = (
    project_folder
    / "src"
    / "bengaluru_complete_v5_predictions.csv"
)

summary_output = (
    project_folder
    / "src"
    / "bengaluru_complete_persistent_heat.csv"
)

df = pd.read_csv(
    input_file
)
grid_df = pd.read_csv(
    grid_file
)

boundary_columns = [
    "Grid_ID",
    "South_Latitude",
    "North_Latitude",
    "West_Longitude",
    "East_Longitude"
]

grid_bounds = (
    grid_df[
        boundary_columns
    ]
    .drop_duplicates(
        subset="Grid_ID"
    )
)

df = df.merge(
    grid_bounds,
    on="Grid_ID",
    how="left"
)

print(
    "\nGrid boundaries merged."
)

print(
    "Missing South_Latitude:",
    df["South_Latitude"].isna().sum()
)

print(
    "Missing North_Latitude:",
    df["North_Latitude"].isna().sum()
)

print(
    "Missing West_Longitude:",
    df["West_Longitude"].isna().sum()
)

print(
    "Missing East_Longitude:",
    df["East_Longitude"].isna().sum()
)
print("Complete V5 feature dataset loaded.")

print("\nTotal rows:")
print(len(df))

print("\nUnique grid cells:")
print(df["Grid_ID"].nunique())

print("\nUnique dates:")
print(df["date"].nunique())

print("\nLoading V5 model package...")

model_package = joblib.load(
    model_file
)

if not isinstance(
    model_package,
    dict
):

    raise ValueError(
        "V5 model file is not a dictionary package."
    )

if "model" not in model_package:

    raise ValueError(
        "The saved V5 package does not contain a 'model' key."
    )

if "features" not in model_package:

    raise ValueError(
        "The saved V5 package does not contain a 'features' key."
    )

model = model_package[
    "model"
]

v5_features = model_package[
    "features"
]

print(
    "V5 model extracted successfully."
)

print(
    "\nSaved model feature count:"
)

print(
    len(v5_features)
)

print(
    "\nSaved model features:"
)

for feature in v5_features:

    print(
        feature
    )

missing_columns = [
    feature
    for feature in v5_features
    if feature not in df.columns
]

if missing_columns:

    raise ValueError(
        "Missing features in complete dataset: "
        + str(missing_columns)
    )

X = df[
    v5_features
].copy()

X = X.replace(
    [
        np.inf,
        -np.inf
    ],
    np.nan
)

missing_values = (
    X.isna()
    .sum()
    .sum()
)

print(
    "\nMissing model values:"
)

print(
    missing_values
)

if missing_values > 0:

    print(
        "\nMissing values by feature:"
    )

    print(
        X.isna()
        .sum()[
            X.isna()
            .sum() > 0
        ]
    )

    raise ValueError(
        "Prediction stopped because "
        "missing V5 feature values remain."
    )

if hasattr(
    model,
    "n_features_in_"
):

    print(
        "\nModel expects:"
    )

    print(
        model.n_features_in_,
        "features"
    )

    if (
        model.n_features_in_
        != len(v5_features)
    ):

        raise ValueError(
            "Feature-count mismatch between "
            "saved feature list and model."
        )

print(
    "\nPredicting LST for complete Bengaluru grid..."
)

predictions = model.predict(
    X
)

df[
    "Predicted_LST"
] = predictions

print(
    "Prediction completed successfully."
)

print(
    "\nPredicted LST statistics:"
)

print(
    df[
        "Predicted_LST"
    ]
    .describe()
)

date_summary = (
    df.groupby(
        "date"
    )
    .agg(
        Cells=(
            "Grid_ID",
            "nunique"
        ),
        Mean_Predicted_LST=(
            "Predicted_LST",
            "mean"
        ),
        Median_Predicted_LST=(
            "Predicted_LST",
            "median"
        ),
        Minimum_Predicted_LST=(
            "Predicted_LST",
            "min"
        ),
        Maximum_Predicted_LST=(
            "Predicted_LST",
            "max"
        )
    )
    .reset_index()
)

print(
    "\nPrediction summary by date:"
)

print(
    date_summary.to_string(
        index=False
    )
)

hot_threshold = (
    df[
        "Predicted_LST"
    ]
    .quantile(
        0.75
    )
)

very_hot_threshold = (
    df[
        "Predicted_LST"
    ]
    .quantile(
        0.90
    )
)

print(
    "\nHot threshold:"
)

print(
    hot_threshold
)

print(
    "\nVery hot threshold:"
)

print(
    very_hot_threshold
)

df[
    "Is_Hot"
] = (
    df[
        "Predicted_LST"
    ]
    >= hot_threshold
)

df[
    "Is_Very_Hot"
] = (
    df[
        "Predicted_LST"
    ]
    >= very_hot_threshold
)

persistent = (
    df.groupby(
        "Grid_ID"
    )
    .agg(

        Grid_X=(
            "Grid_X",
            "first"
        ),

        Grid_Y=(
            "Grid_Y",
            "first"
        ),

        Center_Latitude=(
            "Center_Latitude",
            "first"
        ),

        Center_Longitude=(
            "Center_Longitude",
            "first"
        ),

        South_Latitude=(
            "South_Latitude",
            "first"
        ),

        North_Latitude=(
            "North_Latitude",
            "first"
        ),

        West_Longitude=(
            "West_Longitude",
            "first"
        ),

        East_Longitude=(
            "East_Longitude",
            "first"
        ),

        Historical_Samples=(
            "Historical_Samples",
            "first"
        ),

        Historical_Unique_Dates=(
            "Historical_Unique_Dates",
            "first"
        ),

        Observation_Support=(
            "Observation_Support",
            "first"
        ),

        Prediction_Dates=(
            "date",
            "nunique"
        ),

        Mean_Predicted_LST=(
            "Predicted_LST",
            "mean"
        ),

        Median_Predicted_LST=(
            "Predicted_LST",
            "median"
        ),

        Minimum_Predicted_LST=(
            "Predicted_LST",
            "min"
        ),

        Maximum_Predicted_LST=(
            "Predicted_LST",
            "max"
        ),

        LST_StdDev=(
            "Predicted_LST",
            "std"
        ),

        Hot_Frequency=(
            "Is_Hot",
            "mean"
        ),

        Very_Hot_Frequency=(
            "Is_Very_Hot",
            "mean"
        ),

        Median_L_NDVI=(
            "L_NDVI",
            "median"
        ),

        Median_S2_NDVI=(
            "S2_NDVI",
            "median"
        ),

        Median_NDBI=(
            "NDBI",
            "median"
        ),

        Median_NDWI=(
            "NDWI",
            "median"
        ),

        Median_Tree_Probability=(
            "Tree_Probability",
            "median"
        ),

        Median_Built_Probability=(
            "Built_Probability",
            "median"
        ),

        Median_Albedo=(
            "Albedo",
            "median"
        ),

        Elevation=(
            "Elevation",
            "median"
        ),

        Distance_To_Water=(
            "Distance_To_Water",
            "median"
        )

    )
    .reset_index()
)

print(
    "\nPersistent grid cells:"
)

print(
    len(persistent)
)

incomplete_cells = persistent[
    persistent[
        "Prediction_Dates"
    ] != 7
]

print(
    "\nCells without all 7 predictions:"
)

print(
    len(incomplete_cells)
)


def normalize(
    series
):

    minimum = (
        series.min()
    )

    maximum = (
        series.max()
    )

    if maximum == minimum:

        return pd.Series(
            0,
            index=series.index
        )

    return (
        (
            series - minimum
        )
        /
        (
            maximum - minimum
        )
        * 100
    )


temperature_score = normalize(
    persistent[
        "Median_Predicted_LST"
    ]
)

hot_frequency_score = (
    persistent[
        "Hot_Frequency"
    ]
    * 100
)

very_hot_frequency_score = (
    persistent[
        "Very_Hot_Frequency"
    ]
    * 100
)

built_score = (
    persistent[
        "Median_Built_Probability"
    ]
    .clip(
        0,
        1
    )
    * 100
)

persistent[
    "Persistent_Heat_Score"
] = (

    temperature_score
    * 0.40

    +

    hot_frequency_score
    * 0.35

    +

    very_hot_frequency_score
    * 0.15

    +

    built_score
    * 0.10
)

moderate_threshold = (
    persistent[
        "Persistent_Heat_Score"
    ]
    .quantile(
        0.50
    )
)

high_threshold = (
    persistent[
        "Persistent_Heat_Score"
    ]
    .quantile(
        0.75
    )
)

very_high_threshold = (
    persistent[
        "Persistent_Heat_Score"
    ]
    .quantile(
        0.90
    )
)

print(
    "\nPersistent heat thresholds:"
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


def cooling_priority(
    score
):

    if score >= very_high_threshold:

        return "Very High"

    elif score >= high_threshold:

        return "High"

    elif score >= moderate_threshold:

        return "Moderate"

    else:

        return "Low"


persistent[
    "Persistent_Cooling_Priority"
] = (
    persistent[
        "Persistent_Heat_Score"
    ]
    .apply(
        cooling_priority
    )
)


def prediction_source(
    row
):

    dates = (
        row[
            "Historical_Unique_Dates"
        ]
    )

    if dates >= 5:

        return (
            "Strong historical support + V5"
        )

    elif dates >= 3:

        return (
            "Historical support + V5"
        )

    elif dates >= 1:

        return (
            "Limited historical support + V5"
        )

    else:

        return (
            "V5 prediction only"
        )


persistent[
    "Prediction_Source"
] = (
    persistent.apply(
        prediction_source,
        axis=1
    )
)

print(
    "\nComplete-grid priority distribution:"
)

print(
    persistent[
        "Persistent_Cooling_Priority"
    ]
    .value_counts()
)

print(
    "\nMean median LST by priority:"
)

print(
    persistent
    .groupby(
        "Persistent_Cooling_Priority"
    )[
        "Median_Predicted_LST"
    ]
    .mean()
    .sort_values()
)

print(
    "\nObservation support vs cooling priority:"
)

print(
    pd.crosstab(
        persistent[
            "Observation_Support"
        ],
        persistent[
            "Persistent_Cooling_Priority"
        ]
    )
)

top_hotspots = (
    persistent
    .sort_values(
        "Persistent_Heat_Score",
        ascending=False
    )
    .head(
        20
    )
)

print(
    "\nTop 20 complete-grid hotspots:"
)

print(
    top_hotspots[
        [
            "Grid_ID",
            "Center_Latitude",
            "Center_Longitude",
            "Historical_Unique_Dates",
            "Observation_Support",
            "Median_Predicted_LST",
            "Maximum_Predicted_LST",
            "Hot_Frequency",
            "Very_Hot_Frequency",
            "Median_Tree_Probability",
            "Median_Built_Probability",
            "Persistent_Heat_Score",
            "Persistent_Cooling_Priority",
            "Prediction_Source"
        ]
    ]
    .to_string(
        index=False
    )
)

df.to_csv(
    prediction_output,
    index=False
)

persistent.to_csv(
    summary_output,
    index=False
)

print(
    "\n======================================"
)

print(
    "STEP 38 COMPLETE"
)

print(
    "======================================"
)

print(
    "\nPrediction rows:"
)

print(
    len(df)
)

print(
    "\nPersistent grid cells:"
)

print(
    len(persistent)
)

print(
    "\nUnique prediction dates:"
)

print(
    df[
        "date"
    ]
    .nunique()
)

print(
    "\nDate-level predictions saved at:"
)

print(
    prediction_output
)

print(
    "\nPersistent heat dataset saved at:"
)

print(
    summary_output
)