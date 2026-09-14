import pandas as pd
import numpy as np
from pathlib import Path

script_folder = Path(__file__).resolve().parent
project_folder = script_folder.parent

reliable_file = (
    project_folder
    / "src"
    / "bengaluru_persistent_hotspot_tree_plan.csv"
)

complete_file = (
    project_folder
    / "src"
    / "bengaluru_complete_persistent_heat.csv"
)

output_file = (
    project_folder
    / "src"
    / "bengaluru_hybrid_heat_grid.csv"
)

reliable_df = pd.read_csv(
    reliable_file
)

complete_df = pd.read_csv(
    complete_file
)

print("Reliable persistent dataset loaded:")
print(len(reliable_df))

print("\nComplete V5 grid loaded:")
print(len(complete_df))

reliable_columns = [
    "Grid_ID",
    "Median_Predicted_LST",
    "Mean_Predicted_LST",
    "Maximum_Predicted_LST",
    "Hot_Frequency",
    "Very_Hot_Frequency",
    "Median_L_NDVI",
    "Median_S2_NDVI",
    "Median_Tree_Probability",
    "Median_Built_Probability",
    "Median_Distance_To_Water",
    "Median_Albedo",
    "Persistent_Heat_Score",
    "Persistent_Cooling_Priority"
]

reliable = reliable_df[
    reliable_columns
].copy()

reliable = reliable.rename(
    columns={
        "Median_Predicted_LST":
            "Reliable_Median_LST",

        "Mean_Predicted_LST":
            "Reliable_Mean_LST",

        "Maximum_Predicted_LST":
            "Reliable_Max_LST",

        "Hot_Frequency":
            "Reliable_Hot_Frequency",

        "Very_Hot_Frequency":
            "Reliable_Very_Hot_Frequency",

        "Median_L_NDVI":
            "Reliable_L_NDVI",

        "Median_S2_NDVI":
            "Reliable_S2_NDVI",

        "Median_Tree_Probability":
            "Reliable_Tree_Probability",

        "Median_Built_Probability":
            "Reliable_Built_Probability",

        "Median_Distance_To_Water":
            "Reliable_Distance_To_Water",

        "Median_Albedo":
            "Reliable_Albedo",

        "Persistent_Heat_Score":
            "Reliable_Heat_Score",

        "Persistent_Cooling_Priority":
            "Reliable_Priority"
    }
)

hybrid = complete_df.merge(
    reliable,
    on="Grid_ID",
    how="left"
)

print(
    "\nReliable matches inside complete grid:"
)

print(
    hybrid[
        "Reliable_Median_LST"
    ]
    .notna()
    .sum()
)


def data_source(row):

    historical_dates = (
        row[
            "Historical_Unique_Dates"
        ]
    )

    reliable_value = (
        pd.notna(
            row[
                "Reliable_Median_LST"
            ]
        )
    )

    if reliable_value:

        return "Reliable Multi-Date Observation"

    elif historical_dates >= 1:

        return "Limited Observation + V5"

    else:

        return "V5 Prediction Only"


hybrid[
    "Data_Source"
] = (
    hybrid.apply(
        data_source,
        axis=1
    )
)


def confidence_level(row):

    dates = (
        row[
            "Historical_Unique_Dates"
        ]
    )

    source = (
        row[
            "Data_Source"
        ]
    )

    if source == "Reliable Multi-Date Observation":

        if dates >= 6:
            return "Very High"

        elif dates >= 5:
            return "High"

        else:
            return "Moderate"

    elif source == "Limited Observation + V5":

        return "Limited"

    else:

        return "Prediction Only"


hybrid[
    "Confidence_Level"
] = (
    hybrid.apply(
        confidence_level,
        axis=1
    )
)

hybrid[
    "Final_Median_LST"
] = np.where(
    hybrid[
        "Reliable_Median_LST"
    ].notna(),

    hybrid[
        "Reliable_Median_LST"
    ],

    hybrid[
        "Median_Predicted_LST"
    ]
)

hybrid[
    "Final_Mean_LST"
] = np.where(
    hybrid[
        "Reliable_Mean_LST"
    ].notna(),

    hybrid[
        "Reliable_Mean_LST"
    ],

    hybrid[
        "Mean_Predicted_LST"
    ]
)

hybrid[
    "Final_Max_LST"
] = np.where(
    hybrid[
        "Reliable_Max_LST"
    ].notna(),

    hybrid[
        "Reliable_Max_LST"
    ],

    hybrid[
        "Maximum_Predicted_LST"
    ]
)

hybrid[
    "Final_Hot_Frequency"
] = np.where(
    hybrid[
        "Reliable_Hot_Frequency"
    ].notna(),

    hybrid[
        "Reliable_Hot_Frequency"
    ],

    hybrid[
        "Hot_Frequency"
    ]
)

hybrid[
    "Final_Very_Hot_Frequency"
] = np.where(
    hybrid[
        "Reliable_Very_Hot_Frequency"
    ].notna(),

    hybrid[
        "Reliable_Very_Hot_Frequency"
    ],

    hybrid[
        "Very_Hot_Frequency"
    ]
)

hybrid[
    "Final_L_NDVI"
] = np.where(
    hybrid[
        "Reliable_L_NDVI"
    ].notna(),

    hybrid[
        "Reliable_L_NDVI"
    ],

    hybrid[
        "Median_L_NDVI"
    ]
)

hybrid[
    "Final_S2_NDVI"
] = np.where(
    hybrid[
        "Reliable_S2_NDVI"
    ].notna(),

    hybrid[
        "Reliable_S2_NDVI"
    ],

    hybrid[
        "Median_S2_NDVI"
    ]
)

hybrid[
    "Final_Tree_Probability"
] = np.where(
    hybrid[
        "Reliable_Tree_Probability"
    ].notna(),

    hybrid[
        "Reliable_Tree_Probability"
    ],

    hybrid[
        "Median_Tree_Probability"
    ]
)

hybrid[
    "Final_Built_Probability"
] = np.where(
    hybrid[
        "Reliable_Built_Probability"
    ].notna(),

    hybrid[
        "Reliable_Built_Probability"
    ],

    hybrid[
        "Median_Built_Probability"
    ]
)

hybrid[
    "Final_Distance_To_Water"
] = np.where(
    hybrid[
        "Reliable_Distance_To_Water"
    ].notna(),

    hybrid[
        "Reliable_Distance_To_Water"
    ],

    hybrid[
        "Distance_To_Water"
    ]
)

hybrid[
    "Final_Albedo"
] = np.where(
    hybrid[
        "Reliable_Albedo"
    ].notna(),

    hybrid[
        "Reliable_Albedo"
    ],

    hybrid[
        "Median_Albedo"
    ]
)


def normalize(series):

    minimum = (
        series.min()
    )

    maximum = (
        series.max()
    )

    if maximum == minimum:

        return pd.Series(
            0.0,
            index=series.index
        )

    return (
        series - minimum
    ) / (
        maximum - minimum
    )


hybrid[
    "Heat_Intensity_Score"
] = normalize(
    hybrid[
        "Final_Median_LST"
    ]
)

hybrid[
    "Hot_Frequency_Score"
] = (
    hybrid[
        "Final_Hot_Frequency"
    ]
    .clip(
        0,
        1
    )
)

hybrid[
    "Very_Hot_Frequency_Score"
] = (
    hybrid[
        "Final_Very_Hot_Frequency"
    ]
    .clip(
        0,
        1
    )
)

hybrid[
    "Low_Tree_Score"
] = (
    1
    - normalize(
        hybrid[
            "Final_Tree_Probability"
        ]
    )
)

hybrid[
    "Built_Score"
] = normalize(
    hybrid[
        "Final_Built_Probability"
    ]
)

hybrid[
    "Water_Distance_Score"
] = normalize(
    hybrid[
        "Final_Distance_To_Water"
    ]
)

hybrid[
    "Low_Albedo_Score"
] = (
    1
    - normalize(
        hybrid[
            "Final_Albedo"
        ]
    )
)

hybrid[
    "Hybrid_Heat_Score"
] = (

    0.30
    * hybrid[
        "Heat_Intensity_Score"
    ]

    +

    0.25
    * hybrid[
        "Hot_Frequency_Score"
    ]

    +

    0.10
    * hybrid[
        "Very_Hot_Frequency_Score"
    ]

    +

    0.15
    * hybrid[
        "Low_Tree_Score"
    ]

    +

    0.10
    * hybrid[
        "Built_Score"
    ]

    +

    0.05
    * hybrid[
        "Water_Distance_Score"
    ]

    +

    0.05
    * hybrid[
        "Low_Albedo_Score"
    ]
)

hybrid[
    "Hybrid_Heat_Score"
] = (
    hybrid[
        "Hybrid_Heat_Score"
    ]
    * 100
)

moderate_threshold = (
    hybrid[
        "Hybrid_Heat_Score"
    ]
    .quantile(
        0.50
    )
)

high_threshold = (
    hybrid[
        "Hybrid_Heat_Score"
    ]
    .quantile(
        0.75
    )
)

very_high_threshold = (
    hybrid[
        "Hybrid_Heat_Score"
    ]
    .quantile(
        0.90
    )
)

print(
    "\nHybrid heat thresholds:"
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


def priority_class(score):

    if score >= very_high_threshold:

        return "Very High"

    elif score >= high_threshold:

        return "High"

    elif score >= moderate_threshold:

        return "Moderate"

    else:

        return "Low"


hybrid[
    "Final_Cooling_Priority"
] = (
    hybrid[
        "Hybrid_Heat_Score"
    ]
    .apply(
        priority_class
    )
)

print(
    "\nData source distribution:"
)

print(
    hybrid[
        "Data_Source"
    ]
    .value_counts()
)

print(
    "\nConfidence distribution:"
)

print(
    hybrid[
        "Confidence_Level"
    ]
    .value_counts()
)

print(
    "\nFinal priority distribution:"
)

print(
    hybrid[
        "Final_Cooling_Priority"
    ]
    .value_counts()
)

print(
    "\nMean Final LST by priority:"
)

print(
    hybrid
    .groupby(
        "Final_Cooling_Priority"
    )[
        "Final_Median_LST"
    ]
    .mean()
    .sort_values()
)

print(
    "\nData source vs priority:"
)

print(
    pd.crosstab(
        hybrid[
            "Data_Source"
        ],
        hybrid[
            "Final_Cooling_Priority"
        ]
    )
)

print(
    "\nTop 20 hybrid hotspots:"
)

top_cells = (
    hybrid
    .sort_values(
        "Hybrid_Heat_Score",
        ascending=False
    )
    .head(
        20
    )
)

print(
    top_cells[
        [
            "Grid_ID",
            "Center_Latitude",
            "Center_Longitude",
            "Historical_Unique_Dates",
            "Data_Source",
            "Confidence_Level",
            "Final_Median_LST",
            "Final_Max_LST",
            "Final_Hot_Frequency",
            "Final_Very_Hot_Frequency",
            "Final_Tree_Probability",
            "Final_Built_Probability",
            "Hybrid_Heat_Score",
            "Final_Cooling_Priority"
        ]
    ]
    .to_string(
        index=False
    )
)

hybrid.to_csv(
    output_file,
    index=False
)

print(
    "\n======================================"
)

print(
    "STEP 40 COMPLETE"
)

print(
    "======================================"
)

print(
    "\nTotal hybrid cells:"
)

print(
    len(hybrid)
)

print(
    "\nSaved at:"
)

print(
    output_file
)