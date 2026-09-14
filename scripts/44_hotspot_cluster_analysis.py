import pandas as pd
import numpy as np
from pathlib import Path
from collections import deque

script_folder = Path(__file__).resolve().parent
project_folder = script_folder.parent

input_file = (
    project_folder
    / "src"
    / "bengaluru_final_cooling_tree_plan_with_localities.csv"
)

cluster_output = (
    project_folder
    / "src"
    / "bengaluru_hotspot_cluster_cells.csv"
)

summary_output = (
    project_folder
    / "src"
    / "bengaluru_hotspot_cluster_summary.csv"
)

df = pd.read_csv(
    input_file
)

print("Final locality dataset loaded.")

print("\nTotal cells:")
print(len(df))

hotspots = df[
    df[
        "Final_Cooling_Priority"
    ].isin(
        [
            "High",
            "Very High"
        ]
    )
].copy()

print("\nHigh + Very High cells:")
print(len(hotspots))

print("\nPriority distribution:")

print(
    hotspots[
        "Final_Cooling_Priority"
    ]
    .value_counts()
)

hotspot_lookup = {}

for index, row in hotspots.iterrows():

    coordinate = (
        int(row["Grid_X"]),
        int(row["Grid_Y"])
    )

    hotspot_lookup[
        coordinate
    ] = index

visited = set()

cluster_number = 0

cluster_assignments = {}

neighbor_directions = [
    (-1, -1),
    (-1, 0),
    (-1, 1),
    (0, -1),
    (0, 1),
    (1, -1),
    (1, 0),
    (1, 1)
]

for coordinate in hotspot_lookup:

    if coordinate in visited:
        continue

    cluster_number += 1

    queue = deque(
        [coordinate]
    )

    visited.add(
        coordinate
    )

    while queue:

        current_x, current_y = (
            queue.popleft()
        )

        row_index = hotspot_lookup[
            (
                current_x,
                current_y
            )
        ]

        cluster_assignments[
            row_index
        ] = cluster_number

        for dx, dy in neighbor_directions:

            neighbor = (
                current_x + dx,
                current_y + dy
            )

            if (
                neighbor in hotspot_lookup
                and neighbor not in visited
            ):

                visited.add(
                    neighbor
                )

                queue.append(
                    neighbor
                )

hotspots[
    "Cluster_ID"
] = (
    hotspots.index
    .map(
        cluster_assignments
    )
)

print("\nHotspot clusters found:")
print(cluster_number)


def most_common_value(series):

    cleaned = (
        series
        .dropna()
        .astype(str)
    )

    cleaned = cleaned[
        cleaned.str.strip() != ""
    ]

    if len(cleaned) == 0:
        return "Unknown"

    return (
        cleaned
        .value_counts()
        .index[0]
    )


def locality_list(series):

    values = (
        series
        .dropna()
        .astype(str)
        .str.strip()
    )

    values = values[
        values != ""
    ]

    counts = (
        values
        .value_counts()
    )

    return ", ".join(
        counts
        .head(8)
        .index
        .tolist()
    )


cluster_rows = []

for cluster_id, group in hotspots.groupby(
    "Cluster_ID"
):

    total_cells = len(group)

    high_cells = (
        group[
            "Final_Cooling_Priority"
        ]
        .eq(
            "High"
        )
        .sum()
    )

    very_high_cells = (
        group[
            "Final_Cooling_Priority"
        ]
        .eq(
            "Very High"
        )
        .sum()
    )

    cluster_area_km2 = (
        total_cells
    )

    mean_lst = (
        group[
            "Final_Median_LST"
        ]
        .mean()
    )

    maximum_lst = (
        group[
            "Final_Max_LST"
        ]
        .max()
    )

    mean_heat_score = (
        group[
            "Hybrid_Heat_Score"
        ]
        .mean()
    )

    maximum_heat_score = (
        group[
            "Hybrid_Heat_Score"
        ]
        .max()
    )

    mean_hot_frequency = (
        group[
            "Final_Hot_Frequency"
        ]
        .mean()
    )

    mean_tree_probability = (
        group[
            "Final_Tree_Probability"
        ]
        .mean()
    )

    mean_built_probability = (
        group[
            "Final_Built_Probability"
        ]
        .mean()
    )

    total_trees = int(
        group[
            "Approx_Trees_To_Plant"
        ]
        .sum()
    )

    total_tree_canopy_area = (
        group[
            "Tree_Canopy_Target_m2"
        ]
        .sum()
    )

    total_non_tree_area = (
        group[
            "Non_Tree_Cooling_Area_m2"
        ]
        .sum()
    )

    average_greening = (
        group[
            "Suggested_Greening_Percent"
        ]
        .mean()
    )

    center_latitude = (
        group[
            "Center_Latitude"
        ]
        .mean()
    )

    center_longitude = (
        group[
            "Center_Longitude"
        ]
        .mean()
    )

    dominant_locality = (
        most_common_value(
            group[
                "Area_Name"
            ]
        )
    )

    localities = (
        locality_list(
            group[
                "Area_Name"
            ]
        )
    )

    strongest_reliability = (
        group[
            "Planning_Reliability"
        ]
        .value_counts()
        .index[0]
    )

    strong_cells = (
        group[
            "Planning_Reliability"
        ]
        .eq(
            "Strong"
        )
        .sum()
    )

    moderate_cells = (
        group[
            "Planning_Reliability"
        ]
        .eq(
            "Moderate"
        )
        .sum()
    )

    limited_cells = (
        group[
            "Planning_Reliability"
        ]
        .eq(
            "Limited"
        )
        .sum()
    )

    model_only_cells = (
        group[
            "Planning_Reliability"
        ]
        .eq(
            "Model Only"
        )
        .sum()
    )

    cluster_rows.append(
        {
            "Cluster_ID": cluster_id,
            "Dominant_Locality": dominant_locality,
            "Localities": localities,

            "Center_Latitude": center_latitude,
            "Center_Longitude": center_longitude,

            "Total_Cells": total_cells,
            "Cluster_Area_km2": cluster_area_km2,

            "High_Cells": high_cells,
            "Very_High_Cells": very_high_cells,

            "Mean_Median_LST": mean_lst,
            "Maximum_LST": maximum_lst,

            "Mean_Heat_Score": mean_heat_score,
            "Maximum_Heat_Score": maximum_heat_score,

            "Mean_Hot_Frequency": mean_hot_frequency,

            "Mean_Tree_Probability": mean_tree_probability,
            "Mean_Built_Probability": mean_built_probability,

            "Average_Greening_Percent": average_greening,

            "Total_Trees_To_Plant": total_trees,

            "Tree_Canopy_Target_m2": total_tree_canopy_area,

            "Non_Tree_Cooling_Area_m2": total_non_tree_area,

            "Strong_Cells": strong_cells,
            "Moderate_Reliability_Cells": moderate_cells,
            "Limited_Cells": limited_cells,
            "Model_Only_Cells": model_only_cells,

            "Dominant_Planning_Reliability":
                strongest_reliability
        }
    )

cluster_summary = pd.DataFrame(
    cluster_rows
)

cluster_summary[
    "Mean_Hot_Frequency_Percent"
] = (
    cluster_summary[
        "Mean_Hot_Frequency"
    ]
    * 100
)

cluster_summary[
    "Mean_Tree_Probability_Percent"
] = (
    cluster_summary[
        "Mean_Tree_Probability"
    ]
    * 100
)

cluster_summary[
    "Mean_Built_Probability_Percent"
] = (
    cluster_summary[
        "Mean_Built_Probability"
    ]
    * 100
)

cluster_summary[
    "Cluster_Rank_Score"
] = (
    cluster_summary[
        "Mean_Heat_Score"
    ]
    * 0.45

    +

    cluster_summary[
        "Maximum_Heat_Score"
    ]
    * 0.25

    +

    cluster_summary[
        "Mean_Hot_Frequency_Percent"
    ]
    * 0.20

    +

    (
        cluster_summary[
            "Very_High_Cells"
        ]
        /
        cluster_summary[
            "Total_Cells"
        ]
        * 100
    )
    * 0.10
)

cluster_summary = (
    cluster_summary
    .sort_values(
        "Cluster_Rank_Score",
        ascending=False
    )
    .reset_index(
        drop=True
    )
)

cluster_summary[
    "Cluster_Rank"
] = (
    np.arange(
        1,
        len(cluster_summary) + 1
    )
)

print(
    "\nLargest hotspot clusters:"
)

largest_clusters = (
    cluster_summary
    .sort_values(
        "Total_Cells",
        ascending=False
    )
    .head(15)
)

print(
    largest_clusters[
        [
            "Cluster_ID",
            "Dominant_Locality",
            "Total_Cells",
            "Cluster_Area_km2",
            "High_Cells",
            "Very_High_Cells",
            "Mean_Median_LST",
            "Maximum_LST",
            "Mean_Heat_Score",
            "Total_Trees_To_Plant"
        ]
    ]
    .to_string(
        index=False
    )
)

print(
    "\nTop hotspot clusters by severity:"
)

print(
    cluster_summary[
        [
            "Cluster_Rank",
            "Cluster_ID",
            "Dominant_Locality",
            "Localities",
            "Total_Cells",
            "Very_High_Cells",
            "Mean_Median_LST",
            "Maximum_LST",
            "Mean_Hot_Frequency_Percent",
            "Mean_Built_Probability_Percent",
            "Average_Greening_Percent",
            "Total_Trees_To_Plant",
            "Cluster_Rank_Score"
        ]
    ]
    .head(20)
    .to_string(
        index=False
    )
)

print(
    "\nTotal hotspot area:"
)

print(
    cluster_summary[
        "Cluster_Area_km2"
    ]
    .sum(),
    "km²"
)

print(
    "\nTotal trees across High + Very High clusters:"
)

print(
    int(
        cluster_summary[
            "Total_Trees_To_Plant"
        ]
        .sum()
    )
)

hotspots.to_csv(
    cluster_output,
    index=False
)

cluster_summary.to_csv(
    summary_output,
    index=False
)

print(
    "\nSTEP 44 COMPLETE"
)

print(
    "\nCluster cell dataset saved at:"
)

print(
    cluster_output
)

print(
    "\nCluster summary saved at:"
)

print(
    summary_output
)