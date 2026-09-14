from pathlib import Path
import pandas as pd
import json

# Step 50: Export final analysis to website-ready JSON

# Paths

script_folder = Path(__file__).resolve().parent
project_folder = script_folder.parent

src_folder = (
    project_folder
    / "src"
)

website_folder = (
    project_folder
    / "website"
)

data_folder = (
    website_folder
    / "data"
)

data_folder.mkdir(
    parents=True,
    exist_ok=True
)

grid_file = (
    src_folder
    / "bengaluru_final_cooling_tree_plan_with_localities.csv"
)

hotspot_file = (
    src_folder
    / "bengaluru_final_hotspot_ranking.csv"
)

priority_file = (
    src_folder
    / "bengaluru_final_priority_summary.csv"
)

locality_file = (
    src_folder
    / "bengaluru_locality_heat_summary.csv"
)

# Load final datasets

grid = pd.read_csv(
    grid_file
)

hotspots = pd.read_csv(
    hotspot_file
)

priority = pd.read_csv(
    priority_file
)

localities = pd.read_csv(
    locality_file
)

print("Final project datasets loaded.")

print(
    "\nGrid cells:",
    len(grid)
)

print(
    "Hotspot clusters:",
    len(hotspots)
)

print(
    "Priority classes:",
    len(priority)
)

print(
    "Localities:",
    len(localities)
)

# Clean values for JSON

def clean_dataframe(df):

    df = df.copy()

    df = df.where(
        pd.notnull(df),
        None
    )

    return df


grid = clean_dataframe(
    grid
)

hotspots = clean_dataframe(
    hotspots
)

priority = clean_dataframe(
    priority
)

localities = clean_dataframe(
    localities
)

# Grid data

grid_columns = [
    "Grid_ID",
    "Center_Latitude",
    "Center_Longitude",
    "South_Latitude",
    "North_Latitude",
    "West_Longitude",
    "East_Longitude",
    "Area_Name",
    "Suburb",
    "Postcode",
    "Final_Median_LST",
    "Final_Max_LST",
    "Final_Hot_Frequency",
    "Final_Very_Hot_Frequency",
    "Final_Tree_Probability",
    "Final_Built_Probability",
    "Hybrid_Heat_Score",
    "Final_Cooling_Priority",
    "Suggested_Greening_Percent",
    "Tree_Cooling_Share",
    "Approx_Trees_To_Plant",
    "Trees_Per_Hectare",
    "Planning_Reliability",
    "Data_Source",
    "Recommended_Intervention"
]

available_grid_columns = [
    column
    for column in grid_columns
    if column in grid.columns
]

grid_export = grid[
    available_grid_columns
].copy()

grid_output = (
    data_folder
    / "grid_data.json"
)

grid_export.to_json(
    grid_output,
    orient="records",
    indent=2,
    force_ascii=False
)

# Hotspot cluster data

hotspot_columns = [
    "Planning_Rank",
    "Intensity_Rank",
    "Cluster_ID",
    "Planning_Category",
    "Dominant_Locality",
    "Localities",
    "Total_Cells",
    "Cluster_Area_km2",
    "High_Cells",
    "Very_High_Cells",
    "Mean_Median_LST",
    "Maximum_LST",
    "Mean_Heat_Score",
    "Mean_Hot_Frequency_Percent",
    "Total_Trees_To_Plant",
    "Evidence_Score",
    "Final_Intensity_Score",
    "Planning_Significance_Score"
]

available_hotspot_columns = [
    column
    for column in hotspot_columns
    if column in hotspots.columns
]

hotspot_export = hotspots[
    available_hotspot_columns
].copy()

hotspot_export = hotspot_export.sort_values(
    "Planning_Rank"
)

hotspot_output = (
    data_folder
    / "hotspot_clusters.json"
)

hotspot_export.to_json(
    hotspot_output,
    orient="records",
    indent=2,
    force_ascii=False
)

# Priority summary

priority_output = (
    data_folder
    / "priority_summary.json"
)

priority.to_json(
    priority_output,
    orient="records",
    indent=2,
    force_ascii=False
)

# Locality summary

locality_export = localities.copy()

if "High_Priority_Cells" in locality_export.columns:

    locality_export = (
        locality_export
        .sort_values(
            [
                "High_Priority_Cells",
                "Mean_Heat_Score"
            ],
            ascending=False
        )
    )

locality_output = (
    data_folder
    / "locality_summary.json"
)

locality_export.to_json(
    locality_output,
    orient="records",
    indent=2,
    force_ascii=False
)

# Project summary

total_cells = len(grid)

study_area = (
    grid[
        "Cell_Area_m2"
    ].sum()
    / 1_000_000
    if "Cell_Area_m2" in grid.columns
    else total_cells
)

high_cells = int(
    (
        grid[
            "Final_Cooling_Priority"
        ]
        == "High"
    ).sum()
)

very_high_cells = int(
    (
        grid[
            "Final_Cooling_Priority"
        ]
        == "Very High"
    ).sum()
)

high_very_high = (
    high_cells
    + very_high_cells
)

priority_percent = (
    high_very_high
    / total_cells
    * 100
)

mean_lst = float(
    grid[
        "Final_Median_LST"
    ]
    .mean()
)

highest_median_lst = float(
    grid[
        "Final_Median_LST"
    ]
    .max()
)

highest_max_lst = float(
    grid[
        "Final_Max_LST"
    ]
    .max()
)

total_trees = int(
    grid[
        "Approx_Trees_To_Plant"
    ]
    .sum()
)

priority_trees = int(
    grid.loc[
        grid[
            "Final_Cooling_Priority"
        ]
        .isin(
            [
                "High",
                "Very High"
            ]
        ),
        "Approx_Trees_To_Plant"
    ]
    .sum()
)

reliable_cells = int(
    (
        grid[
            "Data_Source"
        ]
        == "Reliable Multi-Date Observation"
    ).sum()
)

limited_cells = int(
    (
        grid[
            "Data_Source"
        ]
        == "Limited Observation + V5"
    ).sum()
)

prediction_only_cells = int(
    (
        grid[
            "Data_Source"
        ]
        == "V5 Prediction Only"
    ).sum()
)

top_hotspot = (
    hotspots
    .sort_values(
        "Planning_Rank"
    )
    .iloc[0]
)

project_summary = {
    "project_name": (
        "Bengaluru Urban Heat Mitigation "
        "Decision Support System"
    ),

    "grid_resolution_km": 1,

    "total_grid_cells": total_cells,

    "study_area_km2": round(
        float(study_area),
        2
    ),

    "high_priority_cells": high_cells,

    "very_high_priority_cells": very_high_cells,

    "high_and_very_high_cells": high_very_high,

    "high_and_very_high_percent": round(
        priority_percent,
        2
    ),

    "mean_median_lst_c": round(
        mean_lst,
        2
    ),

    "highest_median_lst_c": round(
        highest_median_lst,
        2
    ),

    "highest_max_lst_c": round(
        highest_max_lst,
        2
    ),

    "hotspot_clusters": len(
        hotspots
    ),

    "scenario_based_trees": total_trees,

    "high_priority_area_trees": priority_trees,

    "reliable_observation_cells": reliable_cells,

    "limited_plus_v5_cells": limited_cells,

    "prediction_only_cells": prediction_only_cells,

    "top_hotspot": {
        "planning_rank": int(
            top_hotspot[
                "Planning_Rank"
            ]
        ),

        "cluster_id": int(
            top_hotspot[
                "Cluster_ID"
            ]
        ),

        "locality": str(
            top_hotspot[
                "Dominant_Locality"
            ]
        ),

        "planning_category": str(
            top_hotspot[
                "Planning_Category"
            ]
        ),

        "cluster_area_km2": float(
            top_hotspot[
                "Cluster_Area_km2"
            ]
        ),

        "high_cells": int(
            top_hotspot[
                "High_Cells"
            ]
        ),

        "very_high_cells": int(
            top_hotspot[
                "Very_High_Cells"
            ]
        ),

        "mean_median_lst_c": round(
            float(
                top_hotspot[
                    "Mean_Median_LST"
                ]
            ),
            2
        ),

        "maximum_lst_c": round(
            float(
                top_hotspot[
                    "Maximum_LST"
                ]
            ),
            2
        ),

        "trees": int(
            top_hotspot[
                "Total_Trees_To_Plant"
            ]
        ),

        "planning_significance_score": round(
            float(
                top_hotspot[
                    "Planning_Significance_Score"
                ]
            ),
            2
        )
    }
}

project_summary_output = (
    data_folder
    / "project_summary.json"
)

with open(
    project_summary_output,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        project_summary,
        file,
        indent=2,
        ensure_ascii=False
    )

# Website metadata

metadata = {
    "analysis_year": 2026,

    "grid_resolution": "Approximately 1 km x 1 km",

    "prediction_dates": [
        "2026-01-27",
        "2026-02-12",
        "2026-02-28",
        "2026-03-16",
        "2026-04-01",
        "2026-04-17",
        "2026-05-03"
    ],

    "satellite_sources": [
        "Landsat",
        "Sentinel-2",
        "Dynamic World"
    ],

    "model": "V5 LST prediction model",

    "model_features": 25,

    "analysis_method": (
        "Hybrid multi-date observation "
        "and V5 prediction"
    ),

    "priority_classes": [
        "Low",
        "Moderate",
        "High",
        "Very High"
    ],

    "tree_estimate_note": (
        "Tree values are scenario-based planning "
        "estimates and are not exact planting requirements."
    ),

    "temperature_note": (
        "LST represents land surface temperature "
        "and should not be interpreted as air temperature."
    ),

    "study_area_note": (
        "The study area represents the rectangular "
        "analysis grid and not the official administrative "
        "area of Bengaluru or BBMP."
    )
}

metadata_output = (
    data_folder
    / "metadata.json"
)

with open(
    metadata_output,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        metadata,
        file,
        indent=2,
        ensure_ascii=False
    )

# Verify exported files

print(
    "\nSTEP 50 COMPLETE"
)

print(
    "\nWebsite data folder:"
)

print(
    data_folder
)

print(
    "\nFiles created:"
)

for file in sorted(
    data_folder.glob(
        "*.json"
    )
):

    size_kb = (
        file.stat().st_size
        / 1024
    )

    print(
        file.name,
        "-",
        round(
            size_kb,
            2
        ),
        "KB"
    )

print(
    "\nWebsite summary:"
)

print(
    "Grid cells:",
    total_cells
)

print(
    "Study area:",
    round(
        study_area,
        2
    ),
    "km2"
)

print(
    "High + Very High:",
    high_very_high
)

print(
    "Priority area:",
    round(
        priority_percent,
        2
    ),
    "%"
)

print(
    "Hotspot clusters:",
    len(
        hotspots
    )
)

print(
    "Scenario trees:",
    total_trees
)

print(
    "Top hotspot:",
    top_hotspot[
        "Dominant_Locality"
    ]
)