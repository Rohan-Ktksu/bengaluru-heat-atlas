import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# STEP 37
# Build Complete V5 Feature Matrix
# ============================================================


# ------------------------------------------------------------
# 1. Paths
# ------------------------------------------------------------

script_folder = Path(__file__).resolve().parent
project_folder = script_folder.parent

spatial_file = (
    project_folder
    / "src"
    / "bengaluru_complete_grid_spatial_features.csv"
)

v5_file = (
    project_folder
    / "src"
    / "bengaluru_multidate_v5_overpass_ml_dataset.csv"
)

output_file = (
    project_folder
    / "src"
    / "bengaluru_complete_v5_features.csv"
)


# ------------------------------------------------------------
# 2. Load datasets
# ------------------------------------------------------------

spatial = pd.read_csv(
    spatial_file
)

v5 = pd.read_csv(
    v5_file
)

print("Step 36 spatial dataset loaded.")
print("Rows:", len(spatial))

print("\nOriginal V5 dataset loaded.")
print("Rows:", len(v5))


# ------------------------------------------------------------
# 3. Standardize dates
# ------------------------------------------------------------

spatial["date"] = pd.to_datetime(
    spatial["date"]
)

v5["date"] = pd.to_datetime(
    v5["date"]
)


# ------------------------------------------------------------
# 4. Check expected spatial dataset
# ------------------------------------------------------------

print("\nSpatial unique grid cells:")
print(
    spatial["Grid_ID"].nunique()
)

print("\nSpatial unique dates:")
print(
    spatial["date"].nunique()
)

print("\nRows by date:")
print(
    spatial["date"]
    .value_counts()
    .sort_index()
)


# ------------------------------------------------------------
# 5. Spatial features
# ------------------------------------------------------------

spatial_features = [
    "L_NDVI",
    "NDBI",
    "NDWI",
    "S2_NDVI",
    "Elevation",
    "Built_Probability",
    "Tree_Probability",
    "Albedo",
    "Distance_To_Water"
]


# ------------------------------------------------------------
# 6. Missing values BEFORE filling
# ------------------------------------------------------------

print("\nMissing spatial values BEFORE filling:")

for feature in spatial_features:

    print(
        feature,
        ":",
        spatial[feature]
        .isna()
        .sum()
    )


# ------------------------------------------------------------
# 7. Fill spatial values using same-cell median
#
# Example:
#
# April 17 NDVI missing
#       ↓
# use that same 1 km cell's median NDVI
# from its other available 2026 dates
# ------------------------------------------------------------

for feature in spatial_features:

    cell_median = (
        spatial
        .groupby("Grid_ID")[feature]
        .transform("median")
    )

    spatial[feature] = (
        spatial[feature]
        .fillna(cell_median)
    )


# ------------------------------------------------------------
# 8. Remaining missing values
#
# If a particular grid cell has no valid value on ANY
# 2026 date, use the median for that DATE.
# ------------------------------------------------------------

for feature in spatial_features:

    date_median = (
        spatial
        .groupby("date")[feature]
        .transform("median")
    )

    spatial[feature] = (
        spatial[feature]
        .fillna(date_median)
    )


# ------------------------------------------------------------
# 9. Final fallback
#
# This should normally be unnecessary.
# Use overall median only if something remains missing.
# ------------------------------------------------------------

for feature in spatial_features:

    if spatial[feature].isna().any():

        overall_median = (
            spatial[feature]
            .median()
        )

        spatial[feature] = (
            spatial[feature]
            .fillna(overall_median)
        )


print("\nMissing spatial values AFTER filling:")

for feature in spatial_features:

    print(
        feature,
        ":",
        spatial[feature]
        .isna()
        .sum()
    )


# ------------------------------------------------------------
# 10. Atmospheric V5 features
# ------------------------------------------------------------

atmospheric_features = [
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
    "Overpass_Air_Temp",
    "Overpass_Wind_Speed",
    "Overpass_Relative_Humidity",
    "Overpass_Solar_Radiation",
    "Overpass_Cloud_Cover"
]


# ------------------------------------------------------------
# 11. Verify atmospheric columns
# ------------------------------------------------------------

missing_columns = [
    feature
    for feature in atmospheric_features
    if feature not in v5.columns
]

if missing_columns:

    raise ValueError(
        "Missing atmospheric columns in V5 dataset: "
        + str(missing_columns)
    )


# ------------------------------------------------------------
# 12. Restrict atmospheric source to target dates
# ------------------------------------------------------------

target_dates = (
    spatial["date"]
    .drop_duplicates()
)

v5_target = (
    v5[
        v5["date"].isin(
            target_dates
        )
    ]
    .copy()
)

print("\nV5 rows matching target dates:")
print(
    len(v5_target)
)

print("\nAtmospheric source dates:")
print(
    sorted(
        v5_target["date"]
        .dt.strftime("%Y-%m-%d")
        .unique()
    )
)


# ------------------------------------------------------------
# 13. Build one atmospheric record per date
#
# Median is used because the ERA5 atmospheric variables
# should be essentially common/date-level variables in our
# earlier extraction.
# ------------------------------------------------------------

atmospheric_by_date = (
    v5_target
    .groupby("date")[
        atmospheric_features
    ]
    .median()
    .reset_index()
)


print("\nAtmospheric records created:")
print(
    len(atmospheric_by_date)
)


# ------------------------------------------------------------
# 14. Show atmospheric values by date
# ------------------------------------------------------------

print("\nDate-level atmospheric summary:")

display_columns = [
    "date",
    "Air_Temp",
    "Overpass_Air_Temp",
    "Relative_Humidity",
    "Cloud_Cover",
    "Soil_Moisture"
]

print(
    atmospheric_by_date[
        display_columns
    ]
    .to_string(
        index=False
    )
)


# ------------------------------------------------------------
# 15. Merge atmospheric features onto complete grid
# ------------------------------------------------------------

complete = spatial.merge(
    atmospheric_by_date,
    on="date",
    how="left"
)


print("\nRows after atmospheric merge:")
print(
    len(complete)
)


# ------------------------------------------------------------
# 16. Define exact V5 model feature order
#
# IMPORTANT:
# Keep this identical to V5 model training.
# ------------------------------------------------------------

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
    "Overpass_Wind_Speed",
    "Overpass_Relative_Humidity",
    "Overpass_Solar_Radiation",
    "Overpass_Cloud_Cover"
]


# ------------------------------------------------------------
# 17. Validate all V5 columns
# ------------------------------------------------------------

missing_v5_columns = [
    feature
    for feature in v5_features
    if feature not in complete.columns
]

if missing_v5_columns:

    raise ValueError(
        "Missing V5 features after merge: "
        + str(missing_v5_columns)
    )


# ------------------------------------------------------------
# 18. Check missing values in final model matrix
# ------------------------------------------------------------

print("\nFinal V5 feature missing values:")

total_missing = 0

for feature in v5_features:

    missing = (
        complete[feature]
        .isna()
        .sum()
    )

    total_missing += missing

    print(
        feature,
        ":",
        missing
    )


print("\nTotal missing V5 feature values:")
print(
    total_missing
)


# ------------------------------------------------------------
# 19. Check infinities
# ------------------------------------------------------------

numeric_matrix = (
    complete[
        v5_features
    ]
    .replace(
        [np.inf, -np.inf],
        np.nan
    )
)

infinite_or_invalid = (
    numeric_matrix
    .isna()
    .sum()
    .sum()
)

print(
    "\nInvalid / infinite values after check:"
)

print(
    infinite_or_invalid
)


if infinite_or_invalid > 0:

    print(
        "\nWARNING:"
        " Invalid model values remain."
    )

else:

    print(
        "\nV5 feature matrix is complete."
    )


# ------------------------------------------------------------
# 20. Add year
# ------------------------------------------------------------

complete["year"] = (
    complete["date"]
    .dt.year
)


# ------------------------------------------------------------
# 21. Sort
# ------------------------------------------------------------

complete = (
    complete
    .sort_values(
        [
            "date",
            "Grid_Y",
            "Grid_X"
        ]
    )
    .reset_index(
        drop=True
    )
)


# ------------------------------------------------------------
# 22. Save
# ------------------------------------------------------------

complete.to_csv(
    output_file,
    index=False
)


# ------------------------------------------------------------
# 23. Final summary
# ------------------------------------------------------------

print("\n======================================")
print("STEP 37 COMPLETE")
print("======================================")

print("\nTotal rows:")
print(
    len(complete)
)

print("\nUnique grid cells:")
print(
    complete["Grid_ID"]
    .nunique()
)

print("\nUnique dates:")
print(
    complete["date"]
    .nunique()
)

print("\nRows by date:")

print(
    complete["date"]
    .value_counts()
    .sort_index()
)

print("\nObservation support:")

if "Observation_Support" in complete.columns:

    # Each cell occurs on seven dates,
    # so show unique-cell distribution instead.
    support_summary = (
        complete[
            [
                "Grid_ID",
                "Observation_Support"
            ]
        ]
        .drop_duplicates()
        ["Observation_Support"]
        .value_counts()
    )

    print(
        support_summary
    )

print("\nExpected V5 features:")
print(
    len(v5_features)
)

print("\nSaved at:")
print(
    output_file
)