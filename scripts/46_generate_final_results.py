import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Step 46: Generate final results tables and charts

# Paths

script_folder = Path(__file__).resolve().parent
project_folder = script_folder.parent

priority_file = (
    project_folder
    / "src"
    / "bengaluru_final_priority_summary.csv"
)

ranking_file = (
    project_folder
    / "src"
    / "bengaluru_final_hotspot_ranking.csv"
)

grid_file = (
    project_folder
    / "src"
    / "bengaluru_final_cooling_tree_plan_with_localities.csv"
)

output_folder = (
    project_folder
    / "src"
    / "final_results"
)

output_folder.mkdir(
    parents=True,
    exist_ok=True
)

# Load datasets

priority = pd.read_csv(priority_file)
ranking = pd.read_csv(ranking_file)
grid = pd.read_csv(grid_file)

print("Datasets loaded successfully.")

print("\nPriority rows:")
print(len(priority))

print("\nHotspot clusters:")
print(len(ranking))

print("\nGrid cells:")
print(len(grid))

# Priority distribution table

priority_table = priority[
    [
        "Priority",
        "Cells",
        "Area_km2",
        "Study_Area_Percent",
        "Mean_Median_LST",
        "Maximum_LST",
        "Estimated_Trees"
    ]
].copy()

priority_table["Mean_Median_LST"] = (
    priority_table["Mean_Median_LST"]
    .round(2)
)

priority_table["Maximum_LST"] = (
    priority_table["Maximum_LST"]
    .round(2)
)

priority_table["Study_Area_Percent"] = (
    priority_table["Study_Area_Percent"]
    .round(2)
)

priority_table.to_csv(
    output_folder
    / "priority_summary_table.csv",
    index=False
)

print("\nCooling priority summary:")

print(
    priority_table.to_string(
        index=False
    )
)

# Top planning-significance hotspots

top_planning = (
    ranking
    .sort_values(
        "Planning_Rank"
    )
    .head(10)
    .copy()
)

top_planning_table = top_planning[
    [
        "Planning_Rank",
        "Dominant_Locality",
        "Planning_Category",
        "Cluster_Area_km2",
        "High_Cells",
        "Very_High_Cells",
        "Mean_Median_LST",
        "Maximum_LST",
        "Total_Trees_To_Plant",
        "Planning_Significance_Score"
    ]
].copy()

top_planning_table[
    "Mean_Median_LST"
] = (
    top_planning_table[
        "Mean_Median_LST"
    ]
    .round(2)
)

top_planning_table[
    "Maximum_LST"
] = (
    top_planning_table[
        "Maximum_LST"
    ]
    .round(2)
)

top_planning_table[
    "Planning_Significance_Score"
] = (
    top_planning_table[
        "Planning_Significance_Score"
    ]
    .round(2)
)

top_planning_table.to_csv(
    output_folder
    / "top_10_planning_hotspots.csv",
    index=False
)

print("\nTop 10 planning-significance hotspots:")

print(
    top_planning_table.to_string(
        index=False
    )
)

# Largest connected hotspots

largest = (
    ranking
    .sort_values(
        "Total_Cells",
        ascending=False
    )
    .head(10)
    .copy()
)

largest_table = largest[
    [
        "Dominant_Locality",
        "Cluster_Area_km2",
        "High_Cells",
        "Very_High_Cells",
        "Mean_Median_LST",
        "Maximum_LST",
        "Total_Trees_To_Plant",
        "Planning_Rank"
    ]
]

largest_table.to_csv(
    output_folder
    / "largest_connected_hotspots.csv",
    index=False
)

# Most intense hotspots

intense = (
    ranking
    .sort_values(
        "Intensity_Rank"
    )
    .head(10)
    .copy()
)

intense_table = intense[
    [
        "Intensity_Rank",
        "Dominant_Locality",
        "Total_Cells",
        "Mean_Median_LST",
        "Maximum_LST",
        "Mean_Hot_Frequency_Percent",
        "Final_Intensity_Score",
        "Planning_Rank"
    ]
]

intense_table.to_csv(
    output_folder
    / "top_10_intense_hotspots.csv",
    index=False
)

# Planning reliability summary

reliability_summary = (
    grid[
        "Planning_Reliability"
    ]
    .value_counts()
    .reset_index()
)

reliability_summary.columns = [
    "Planning_Reliability",
    "Cells"
]

reliability_summary[
    "Percent"
] = (
    reliability_summary[
        "Cells"
    ]
    / len(grid)
    * 100
)

reliability_summary[
    "Percent"
] = (
    reliability_summary[
        "Percent"
    ]
    .round(2)
)

reliability_summary.to_csv(
    output_folder
    / "planning_reliability_summary.csv",
    index=False
)

# Data-source summary

source_summary = (
    grid[
        "Data_Source"
    ]
    .value_counts()
    .reset_index()
)

source_summary.columns = [
    "Data_Source",
    "Cells"
]

source_summary[
    "Percent"
] = (
    source_summary[
        "Cells"
    ]
    / len(grid)
    * 100
)

source_summary[
    "Percent"
] = (
    source_summary[
        "Percent"
    ]
    .round(2)
)

source_summary.to_csv(
    output_folder
    / "data_source_summary.csv",
    index=False
)

# Chart 1: Cooling priority distribution

priority_order = [
    "Low",
    "Moderate",
    "High",
    "Very High"
]

priority_chart = (
    priority
    .set_index("Priority")
    .reindex(priority_order)
)

plt.figure(
    figsize=(8, 5)
)

plt.bar(
    priority_chart.index,
    priority_chart["Cells"]
)

plt.title(
    "Bengaluru Cooling Priority Distribution"
)

plt.xlabel(
    "Cooling Priority"
)

plt.ylabel(
    "Number of 1 km Grid Cells"
)

plt.tight_layout()

plt.savefig(
    output_folder
    / "01_cooling_priority_distribution.png",
    dpi=300
)

plt.close()

# Chart 2: Mean LST by priority

plt.figure(
    figsize=(8, 5)
)

plt.bar(
    priority_chart.index,
    priority_chart[
        "Mean_Median_LST"
    ]
)

plt.title(
    "Mean Land Surface Temperature by Cooling Priority"
)

plt.xlabel(
    "Cooling Priority"
)

plt.ylabel(
    "Mean Median LST (°C)"
)

plt.tight_layout()

plt.savefig(
    output_folder
    / "02_mean_lst_by_priority.png",
    dpi=300
)

plt.close()

# Chart 3: Estimated trees by priority

plt.figure(
    figsize=(8, 5)
)

plt.bar(
    priority_chart.index,
    priority_chart[
        "Estimated_Trees"
    ]
)

plt.title(
    "Scenario-Based Tree Requirement by Cooling Priority"
)

plt.xlabel(
    "Cooling Priority"
)

plt.ylabel(
    "Estimated Trees"
)

plt.tight_layout()

plt.savefig(
    output_folder
    / "03_trees_by_priority.png",
    dpi=300
)

plt.close()

# Chart 4: Top planning-significance clusters

plot_top = (
    ranking
    .sort_values(
        "Planning_Rank"
    )
    .head(10)
    .sort_values(
        "Planning_Significance_Score"
    )
)

plt.figure(
    figsize=(10, 6)
)

plt.barh(
    plot_top[
        "Dominant_Locality"
    ],
    plot_top[
        "Planning_Significance_Score"
    ]
)

plt.title(
    "Top 10 Hotspot Clusters by Planning Significance"
)

plt.xlabel(
    "Planning Significance Score"
)

plt.ylabel(
    "Dominant Locality"
)

plt.tight_layout()

plt.savefig(
    output_folder
    / "04_top_planning_hotspots.png",
    dpi=300
)

plt.close()

# Chart 5: Largest hotspot clusters

plot_largest = (
    ranking
    .sort_values(
        "Total_Cells",
        ascending=False
    )
    .head(10)
    .sort_values(
        "Cluster_Area_km2"
    )
)

plt.figure(
    figsize=(10, 6)
)

plt.barh(
    plot_largest[
        "Dominant_Locality"
    ],
    plot_largest[
        "Cluster_Area_km2"
    ]
)

plt.title(
    "Largest Connected High-Priority Heat Clusters"
)

plt.xlabel(
    "Cluster Area (km²)"
)

plt.ylabel(
    "Dominant Locality"
)

plt.tight_layout()

plt.savefig(
    output_folder
    / "05_largest_hotspot_clusters.png",
    dpi=300
)

plt.close()

# Chart 6: Most intense hotspots

plot_intense = (
    ranking
    .sort_values(
        "Intensity_Rank"
    )
    .head(10)
    .sort_values(
        "Final_Intensity_Score"
    )
)

plt.figure(
    figsize=(10, 6)
)

plt.barh(
    plot_intense[
        "Dominant_Locality"
    ],
    plot_intense[
        "Final_Intensity_Score"
    ]
)

plt.title(
    "Top 10 Hotspot Clusters by Heat Intensity"
)

plt.xlabel(
    "Final Intensity Score"
)

plt.ylabel(
    "Dominant Locality"
)

plt.tight_layout()

plt.savefig(
    output_folder
    / "06_most_intense_hotspots.png",
    dpi=300
)

plt.close()

# Chart 7: Planning reliability

plt.figure(
    figsize=(8, 5)
)

plt.bar(
    reliability_summary[
        "Planning_Reliability"
    ],
    reliability_summary[
        "Cells"
    ]
)

plt.title(
    "Planning Reliability of Grid Cells"
)

plt.xlabel(
    "Reliability"
)

plt.ylabel(
    "Number of Grid Cells"
)

plt.tight_layout()

plt.savefig(
    output_folder
    / "07_planning_reliability.png",
    dpi=300
)

plt.close()

# Chart 8: Data source distribution

plt.figure(
    figsize=(9, 5)
)

plt.bar(
    source_summary[
        "Data_Source"
    ],
    source_summary[
        "Cells"
    ]
)

plt.title(
    "Data Source Distribution"
)

plt.xlabel(
    "Data Source"
)

plt.ylabel(
    "Number of Grid Cells"
)

plt.xticks(
    rotation=15,
    ha="right"
)

plt.tight_layout()

plt.savefig(
    output_folder
    / "08_data_source_distribution.png",
    dpi=300
)

plt.close()

# Final findings summary

high_cells = int(
    priority.loc[
        priority[
            "Priority"
        ] == "High",
        "Cells"
    ]
    .iloc[0]
)

very_high_cells = int(
    priority.loc[
        priority[
            "Priority"
        ] == "Very High",
        "Cells"
    ]
    .iloc[0]
)

high_very_high = (
    high_cells
    + very_high_cells
)

high_share = (
    high_very_high
    / len(grid)
    * 100
)

total_trees = int(
    grid[
        "Approx_Trees_To_Plant"
    ]
    .sum()
)

hotspot_trees = int(
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

top_cluster = (
    ranking
    .sort_values(
        "Planning_Rank"
    )
    .iloc[0]
)

summary_lines = [
    "BENGALURU URBAN HEAT MITIGATION - FINAL RESULTS",
    "",
    f"Total study area: approximately {len(grid)} km²",
    f"Total grid cells: {len(grid)}",
    "",
    f"High priority cells: {high_cells}",
    f"Very High priority cells: {very_high_cells}",
    f"Combined High + Very High area: {high_very_high} km²",
    f"Share of study area: {high_share:.2f}%",
    "",
    f"Mean median LST across study area: {grid['Final_Median_LST'].mean():.2f} °C",
    f"Highest median LST: {grid['Final_Median_LST'].max():.2f} °C",
    f"Highest maximum LST: {grid['Final_Max_LST'].max():.2f} °C",
    "",
    f"Connected hotspot clusters identified: {len(ranking)}",
    "",
    "Top planning-significance hotspot:",
    f"Locality: {top_cluster['Dominant_Locality']}",
    f"Cluster area: {top_cluster['Cluster_Area_km2']:.0f} km²",
    f"High cells: {int(top_cluster['High_Cells'])}",
    f"Very High cells: {int(top_cluster['Very_High_Cells'])}",
    f"Mean median LST: {top_cluster['Mean_Median_LST']:.2f} °C",
    f"Maximum LST: {top_cluster['Maximum_LST']:.2f} °C",
    f"Planning significance score: {top_cluster['Planning_Significance_Score']:.2f}",
    "",
    f"Total scenario-based tree estimate: {total_trees:,}",
    f"Trees associated with High + Very High areas: {hotspot_trees:,}",
    "",
    "Tree estimates are scenario-based planning values and should not be interpreted as exact ecological requirements."
]

summary_file = (
    output_folder
    / "final_findings_summary.txt"
)

with open(
    summary_file,
    "w",
    encoding="utf-8"
) as file:

    file.write(
        "\n".join(
            summary_lines
        )
    )

print("\nSTEP 46 COMPLETE")

print("\nOutput folder:")
print(output_folder)

print("\nCharts created:")
print("01_cooling_priority_distribution.png")
print("02_mean_lst_by_priority.png")
print("03_trees_by_priority.png")
print("04_top_planning_hotspots.png")
print("05_largest_hotspot_clusters.png")
print("06_most_intense_hotspots.png")
print("07_planning_reliability.png")
print("08_data_source_distribution.png")

print("\nFinal findings summary:")
print(summary_file)