import pandas as pd
import numpy as np
from pathlib import Path

# Step 45: Final hotspot analysis and planning-significance ranking

# Paths

script_folder = Path(__file__).resolve().parent
project_folder = script_folder.parent

grid_file = (
    project_folder
    / "src"
    / "bengaluru_final_cooling_tree_plan_with_localities.csv"
)

cluster_file = (
    project_folder
    / "src"
    / "bengaluru_hotspot_cluster_summary.csv"
)

ranking_output = (
    project_folder
    / "src"
    / "bengaluru_final_hotspot_ranking.csv"
)

priority_output = (
    project_folder
    / "src"
    / "bengaluru_final_priority_summary.csv"
)

report_output = (
    project_folder
    / "src"
    / "bengaluru_final_analysis_summary.txt"
)


# Load datasets

grid = pd.read_csv(grid_file)
clusters = pd.read_csv(cluster_file)

print("Final Bengaluru grid loaded.")
print("Grid cells:", len(grid))

print("\nHotspot cluster dataset loaded.")
print("Clusters:", len(clusters))


# Basic study-area statistics

total_cells = len(grid)

cell_area_km2 = 1.0

total_area_km2 = (
    total_cells * cell_area_km2
)

print("\nSTUDY AREA")

print("Total grid cells:", total_cells)

print(
    "Approximate study area:",
    total_area_km2,
    "km²"
)


# Priority summary

priority_order = [
    "Low",
    "Moderate",
    "High",
    "Very High"
]

priority_rows = []

for priority in priority_order:

    subset = grid[
        grid["Final_Cooling_Priority"] == priority
    ]

    cells = len(subset)

    area = (
        cells * cell_area_km2
    )

    percent = (
        cells
        / total_cells
        * 100
    )

    if cells > 0:

        mean_lst = (
            subset[
                "Final_Median_LST"
            ]
            .mean()
        )

        max_lst = (
            subset[
                "Final_Max_LST"
            ]
            .max()
        )

        mean_heat_score = (
            subset[
                "Hybrid_Heat_Score"
            ]
            .mean()
        )

        trees = int(
            subset[
                "Approx_Trees_To_Plant"
            ]
            .sum()
        )

    else:

        mean_lst = np.nan
        max_lst = np.nan
        mean_heat_score = np.nan
        trees = 0

    priority_rows.append(
        {
            "Priority": priority,
            "Cells": cells,
            "Area_km2": area,
            "Study_Area_Percent": percent,
            "Mean_Median_LST": mean_lst,
            "Maximum_LST": max_lst,
            "Mean_Heat_Score": mean_heat_score,
            "Estimated_Trees": trees
        }
    )


priority_summary = pd.DataFrame(
    priority_rows
)

priority_summary.to_csv(
    priority_output,
    index=False
)

print("\nCOOLING PRIORITY DISTRIBUTION")

print(
    priority_summary.to_string(
        index=False
    )
)


# High and Very High statistics

hot = grid[
    grid[
        "Final_Cooling_Priority"
    ].isin(
        [
            "High",
            "Very High"
        ]
    )
].copy()

hot_cells = len(hot)

hot_area = (
    hot_cells
    * cell_area_km2
)

hot_percent = (
    hot_cells
    / total_cells
    * 100
)

print("\nHIGH + VERY HIGH PRIORITY")

print(
    "Cells:",
    hot_cells
)

print(
    "Area:",
    hot_area,
    "km²"
)

print(
    "Percentage:",
    hot_percent
)


# Reliability statistics

print("\nPLANNING RELIABILITY")

reliability_counts = (
    grid[
        "Planning_Reliability"
    ]
    .value_counts()
)

print(
    reliability_counts
)

print(
    "\nHotspot reliability:"
)

hot_reliability = (
    hot[
        "Planning_Reliability"
    ]
    .value_counts()
)

print(
    hot_reliability
)


# Data-source statistics

print("\nDATA SOURCE")

print(
    grid[
        "Data_Source"
    ]
    .value_counts()
)

print(
    "\nHotspot data sources:"
)

print(
    hot[
        "Data_Source"
    ]
    .value_counts()
)


# Temperature statistics

print("\nTEMPERATURE STATISTICS")

mean_median_lst = (
    grid[
        "Final_Median_LST"
    ]
    .mean()
)

median_median_lst = (
    grid[
        "Final_Median_LST"
    ]
    .median()
)

highest_median_lst = (
    grid[
        "Final_Median_LST"
    ]
    .max()
)

highest_maximum_lst = (
    grid[
        "Final_Max_LST"
    ]
    .max()
)

hot_mean_lst = (
    hot[
        "Final_Median_LST"
    ]
    .mean()
)

print(
    "Mean median LST:",
    mean_median_lst
)

print(
    "Median median LST:",
    median_median_lst
)

print(
    "Highest median LST:",
    highest_median_lst
)

print(
    "Highest maximum LST:",
    highest_maximum_lst
)

print(
    "High + Very High mean median LST:",
    hot_mean_lst
)


# Cooling intervention statistics

print("\nCOOLING INTERVENTIONS")

total_trees = int(
    grid[
        "Approx_Trees_To_Plant"
    ]
    .sum()
)

hotspot_trees = int(
    hot[
        "Approx_Trees_To_Plant"
    ]
    .sum()
)

tree_area = (
    grid[
        "Tree_Canopy_Target_m2"
    ]
    .sum()
)

non_tree_area = (
    grid[
        "Non_Tree_Cooling_Area_m2"
    ]
    .sum()
)

print(
    "Total planning-scenario trees:",
    total_trees
)

print(
    "Trees in High + Very High areas:",
    hotspot_trees
)

print(
    "Tree canopy target area:",
    tree_area,
    "m²"
)

print(
    "Non-tree cooling target area:",
    non_tree_area,
    "m²"
)


# Normalization function

def normalize(series):

    minimum = series.min()
    maximum = series.max()

    if maximum == minimum:

        return pd.Series(
            0.0,
            index=series.index
        )

    return (
        (series - minimum)
        /
        (maximum - minimum)
    )


# Cluster area score

clusters[
    "Area_Score"
] = normalize(
    np.log1p(
        clusters[
            "Total_Cells"
        ]
    )
)


# Heat score normalization

clusters[
    "Mean_Heat_Score_Normalized"
] = normalize(
    clusters[
        "Mean_Heat_Score"
    ]
)

clusters[
    "Maximum_Heat_Score_Normalized"
] = normalize(
    clusters[
        "Maximum_Heat_Score"
    ]
)


# Very High hotspot contribution

clusters[
    "Very_High_Share"
] = (
    clusters[
        "Very_High_Cells"
    ]
    /
    clusters[
        "Total_Cells"
    ]
)

clusters[
    "Very_High_Count_Score"
] = normalize(
    np.log1p(
        clusters[
            "Very_High_Cells"
        ]
    )
)


# Hot-frequency score

clusters[
    "Hot_Frequency_Score"
] = normalize(
    clusters[
        "Mean_Hot_Frequency"
    ]
)


# Evidence and reliability score

clusters[
    "Evidence_Score"
] = (
    (
        clusters[
            "Strong_Cells"
        ]
        * 1.00
    )
    +
    (
        clusters[
            "Moderate_Reliability_Cells"
        ]
        * 0.75
    )
    +
    (
        clusters[
            "Limited_Cells"
        ]
        * 0.40
    )
    +
    (
        clusters[
            "Model_Only_Cells"
        ]
        * 0.20
    )
) / clusters[
    "Total_Cells"
]


# Hotspot intensity score

clusters[
    "Final_Intensity_Score"
] = (
    0.40
    * clusters[
        "Mean_Heat_Score_Normalized"
    ]

    +

    0.25
    * clusters[
        "Maximum_Heat_Score_Normalized"
    ]

    +

    0.20
    * clusters[
        "Hot_Frequency_Score"
    ]

    +

    0.15
    * clusters[
        "Very_High_Share"
    ]
) * 100


# Planning-significance score

clusters[
    "Planning_Significance_Score"
] = (
    0.30
    * clusters[
        "Area_Score"
    ]

    +

    0.20
    * clusters[
        "Very_High_Count_Score"
    ]

    +

    0.20
    * clusters[
        "Mean_Heat_Score_Normalized"
    ]

    +

    0.10
    * clusters[
        "Hot_Frequency_Score"
    ]

    +

    0.10
    * clusters[
        "Maximum_Heat_Score_Normalized"
    ]

    +

    0.10
    * clusters[
        "Evidence_Score"
    ]
) * 100


# Rank clusters by intensity

clusters[
    "Intensity_Rank"
] = (
    clusters[
        "Final_Intensity_Score"
    ]
    .rank(
        method="min",
        ascending=False
    )
    .astype(int)
)


# Rank clusters by planning significance

clusters[
    "Planning_Rank"
] = (
    clusters[
        "Planning_Significance_Score"
    ]
    .rank(
        method="min",
        ascending=False
    )
    .astype(int)
)

clusters = (
    clusters
    .sort_values(
        "Planning_Rank"
    )
    .reset_index(
        drop=True
    )
)


# Planning category

def planning_category(rank):

    if rank <= 5:

        return "Critical"

    elif rank <= 15:

        return "Major"

    elif rank <= 30:

        return "Secondary"

    else:

        return "Localized"


clusters[
    "Planning_Category"
] = (
    clusters[
        "Planning_Rank"
    ]
    .apply(
        planning_category
    )
)


# Top planning-significance hotspots

print(
    "\nTOP PLANNING-SIGNIFICANCE HOTSPOTS"
)

columns_to_show = [
    "Planning_Rank",
    "Cluster_ID",
    "Planning_Category",
    "Dominant_Locality",
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

print(
    clusters[
        columns_to_show
    ]
    .head(
        20
    )
    .to_string(
        index=False
    )
)


# Largest connected hotspots

print(
    "\nLARGEST CONNECTED HOTSPOTS"
)

largest_clusters = (
    clusters
    .sort_values(
        "Total_Cells",
        ascending=False
    )
)

print(
    largest_clusters[
        [
            "Cluster_ID",
            "Dominant_Locality",
            "Localities",
            "Total_Cells",
            "Very_High_Cells",
            "Mean_Median_LST",
            "Maximum_LST",
            "Total_Trees_To_Plant",
            "Planning_Rank"
        ]
    ]
    .head(
        15
    )
    .to_string(
        index=False
    )
)


# Most intense hotspots

print(
    "\nMOST INTENSE HOTSPOTS"
)

intense_clusters = (
    clusters
    .sort_values(
        "Intensity_Rank"
    )
)

print(
    intense_clusters[
        [
            "Intensity_Rank",
            "Cluster_ID",
            "Dominant_Locality",
            "Total_Cells",
            "Mean_Median_LST",
            "Maximum_LST",
            "Mean_Hot_Frequency_Percent",
            "Final_Intensity_Score",
            "Planning_Rank"
        ]
    ]
    .head(
        15
    )
    .to_string(
        index=False
    )
)


# Save final cluster ranking

clusters.to_csv(
    ranking_output,
    index=False
)


# Prepare final report summary

top_cluster = (
    clusters.iloc[0]
)

summary_lines = []

summary_lines.append(
    "BENGALURU URBAN HEAT MITIGATION - FINAL ANALYSIS"
)

summary_lines.append("")

summary_lines.append(
    f"Total study grid cells: {total_cells}"
)

summary_lines.append(
    f"Approximate study area: {total_area_km2:.0f} km2"
)

summary_lines.append("")

summary_lines.append(
    f"High + Very High priority cells: {hot_cells}"
)

summary_lines.append(
    f"High + Very High area: {hot_area:.0f} km2"
)

summary_lines.append(
    f"High + Very High share: {hot_percent:.2f}%"
)

summary_lines.append("")

summary_lines.append(
    f"Connected hotspot clusters: {len(clusters)}"
)

summary_lines.append("")

summary_lines.append(
    "Highest planning-significance cluster:"
)

summary_lines.append(
    f"Cluster ID: {int(top_cluster['Cluster_ID'])}"
)

summary_lines.append(
    f"Dominant locality: {top_cluster['Dominant_Locality']}"
)

summary_lines.append(
    f"Area: {top_cluster['Cluster_Area_km2']:.0f} km2"
)

summary_lines.append(
    f"High cells: {int(top_cluster['High_Cells'])}"
)

summary_lines.append(
    f"Very High cells: {int(top_cluster['Very_High_Cells'])}"
)

summary_lines.append(
    f"Mean median LST: {top_cluster['Mean_Median_LST']:.2f} C"
)

summary_lines.append(
    f"Maximum LST: {top_cluster['Maximum_LST']:.2f} C"
)

summary_lines.append(
    f"Planning-scenario trees: {int(top_cluster['Total_Trees_To_Plant'])}"
)

summary_lines.append("")

summary_lines.append(
    f"Total planning-scenario trees across study area: {total_trees}"
)

summary_lines.append(
    f"Trees associated with High + Very High areas: {hotspot_trees}"
)

summary_lines.append("")

summary_lines.append(
    "Tree numbers are scenario-based planning estimates, not measured ecological requirements."
)


# Save final text summary

with open(
    report_output,
    "w",
    encoding="utf-8"
) as file:

    file.write(
        "\n".join(
            summary_lines
        )
    )


# Final output

print(
    "\nSTEP 45 COMPLETE"
)

print(
    "\nFinal hotspot ranking saved at:"
)

print(
    ranking_output
)

print(
    "\nPriority summary saved at:"
)

print(
    priority_output
)

print(
    "\nReport summary saved at:"
)

print(
    report_output
)