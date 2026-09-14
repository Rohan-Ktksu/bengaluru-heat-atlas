from pathlib import Path
import pandas as pd

# Step 49: Generate final conclusion and future scope

# Paths

script_folder = Path(__file__).resolve().parent
project_folder = script_folder.parent

grid_file = (
    project_folder
    / "src"
    / "bengaluru_final_cooling_tree_plan_with_localities.csv"
)

ranking_file = (
    project_folder
    / "src"
    / "bengaluru_final_hotspot_ranking.csv"
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

output_file = (
    output_folder
    / "conclusion_and_future_scope.txt"
)

# Load datasets

grid = pd.read_csv(
    grid_file
)

ranking = pd.read_csv(
    ranking_file
)

print("Final datasets loaded.")

print(
    "\nGrid cells:",
    len(grid)
)

print(
    "Hotspot clusters:",
    len(ranking)
)

# Study statistics

total_cells = len(grid)

study_area_km2 = (
    grid[
        "Cell_Area_m2"
    ].sum()
    / 1_000_000
)

high_cells = (
    grid[
        "Final_Cooling_Priority"
    ]
    .eq(
        "High"
    )
    .sum()
)

very_high_cells = (
    grid[
        "Final_Cooling_Priority"
    ]
    .eq(
        "Very High"
    )
    .sum()
)

priority_cells = (
    high_cells
    + very_high_cells
)

priority_percent = (
    priority_cells
    / total_cells
    * 100
)

# Temperature statistics

mean_lst = (
    grid[
        "Final_Median_LST"
    ]
    .mean()
)

highest_median_lst = (
    grid[
        "Final_Median_LST"
    ]
    .max()
)

highest_max_lst = (
    grid[
        "Final_Max_LST"
    ]
    .max()
)

priority_mean_lst = (
    grid[
        grid[
            "Final_Cooling_Priority"
        ]
        .isin(
            [
                "High",
                "Very High"
            ]
        )
    ][
        "Final_Median_LST"
    ]
    .mean()
)

# Data source statistics

source_counts = (
    grid[
        "Data_Source"
    ]
    .value_counts()
)

reliable_cells = int(
    source_counts.get(
        "Reliable Multi-Date Observation",
        0
    )
)

limited_cells = int(
    source_counts.get(
        "Limited Observation + V5",
        0
    )
)

prediction_cells = int(
    source_counts.get(
        "V5 Prediction Only",
        0
    )
)

# Tree planning

total_trees = int(
    grid[
        "Approx_Trees_To_Plant"
    ]
    .sum()
)

priority_trees = int(
    grid[
        grid[
            "Final_Cooling_Priority"
        ]
        .isin(
            [
                "High",
                "Very High"
            ]
        )
    ][
        "Approx_Trees_To_Plant"
    ]
    .sum()
)

# Hotspot ranking

top_hotspot = (
    ranking
    .sort_values(
        "Planning_Rank"
    )
    .iloc[0]
)

top_locality = (
    top_hotspot[
        "Dominant_Locality"
    ]
)

top_cluster_area = (
    top_hotspot[
        "Cluster_Area_km2"
    ]
)

top_cluster_cells = (
    top_hotspot[
        "Total_Cells"
    ]
)

top_cluster_high = (
    top_hotspot[
        "High_Cells"
    ]
)

top_cluster_very_high = (
    top_hotspot[
        "Very_High_Cells"
    ]
)

top_cluster_trees = int(
    top_hotspot[
        "Total_Trees_To_Plant"
    ]
)

top_cluster_score = (
    top_hotspot[
        "Planning_Significance_Score"
    ]
)

# Build conclusion

lines = []

lines.append(
    "BENGALURU URBAN HEAT MITIGATION PROJECT"
)

lines.append(
    "FINAL CONCLUSION AND FUTURE SCOPE"
)

lines.append("")

lines.append(
    "1. PROJECT CONCLUSION"
)

lines.append("")

lines.append(
    "This project developed a spatial decision-support framework for identifying persistent urban heat hotspots and planning cooling interventions across the Bengaluru study region."
)

lines.append(
    "The workflow combines satellite remote sensing, meteorological information, land-cover characteristics, machine-learning prediction and spatial hotspot analysis."
)

lines.append("")

lines.append(
    f"The final analysis contains {total_cells} approximately 1 km grid cells covering about {study_area_km2:.0f} km2 of the defined study region."
)

lines.append(
    "Each grid cell was evaluated using multi-date heat behaviour rather than relying on a single satellite observation."
)

lines.append("")

lines.append(
    "2. COMPLETE SPATIAL COVERAGE"
)

lines.append("")

lines.append(
    "One of the main outcomes of the project was the creation of a complete heat-analysis grid."
)

lines.append(
    "The original satellite observations contained spatial and temporal gaps caused mainly by cloud masking and differences in usable observations."
)

lines.append(
    "The V5 machine-learning model was used to supplement these gaps and provide complete spatial coverage."
)

lines.append("")

lines.append(
    f"Reliable multi-date observations were available for {reliable_cells} cells."
)

lines.append(
    f"Limited observations supplemented with V5 were used for {limited_cells} cells."
)

lines.append(
    f"Only {prediction_cells} cells depended completely on V5 predictions."
)

lines.append("")

lines.append(
    "3. HYBRID HEAT ANALYSIS"
)

lines.append("")

lines.append(
    "Validation showed that replacing all historical observations with model predictions would remove or weaken several observed hotspot patterns."
)

lines.append(
    "For this reason, the final system uses a hybrid approach."
)

lines.append(
    "Reliable multi-date observations are preserved where available, while V5 predictions provide additional support for limited and missing observations."
)

lines.append(
    "This allows the system to maintain observational evidence while still producing a complete Bengaluru heat surface."
)

lines.append("")

lines.append(
    "4. URBAN HEAT RESULTS"
)

lines.append("")

lines.append(
    f"The mean median LST across the complete study grid was approximately {mean_lst:.2f} C."
)

lines.append(
    f"The highest grid-cell median LST was approximately {highest_median_lst:.2f} C."
)

lines.append(
    f"The highest maximum LST recorded in the final dataset was approximately {highest_max_lst:.2f} C."
)

lines.append("")

lines.append(
    f"A total of {priority_cells} cells were classified as High or Very High cooling priority."
)

lines.append(
    f"This represents {priority_percent:.1f}% of the analysis grid, or approximately {priority_cells} km2."
)

lines.append(
    f"The mean median LST across these priority areas was approximately {priority_mean_lst:.2f} C."
)

lines.append("")

lines.append(
    "These categories represent relative planning priorities within the study region and should not be interpreted as universal dangerous-temperature thresholds."
)

lines.append("")

lines.append(
    "5. HOTSPOT CLUSTERS"
)

lines.append("")

lines.append(
    f"The spatial analysis identified {len(ranking)} connected High and Very High hotspot clusters."
)

lines.append(
    "Connected clustering allows the project to distinguish large continuous heat zones from isolated individual hot cells."
)

lines.append("")

lines.append(
    f"The highest planning-significance cluster was centred around {top_locality}."
)

lines.append(
    f"This cluster covered approximately {top_cluster_area:.0f} km2 and contained {int(top_cluster_cells)} priority grid cells."
)

lines.append(
    f"It contained {int(top_cluster_high)} High cells and {int(top_cluster_very_high)} Very High cells."
)

lines.append(
    f"Its planning-significance score was {top_cluster_score:.2f}."
)

lines.append("")

lines.append(
    "6. COOLING INTERVENTION PLANNING"
)

lines.append("")

lines.append(
    "The project converts heat analysis into practical cooling-planning information."
)

lines.append(
    "Recommendations include street-tree corridors, canopy expansion, urban forests, park restoration, pocket parks, shaded public spaces, green roofs, cool roofs and reflective pavement."
)

lines.append("")

lines.append(
    f"The complete planning scenario estimates approximately {total_trees:,} trees."
)

lines.append(
    f"Approximately {priority_trees:,} of these trees are associated with High and Very High priority areas."
)

lines.append(
    f"The highest-ranked hotspot cluster alone has a planning estimate of approximately {top_cluster_trees:,} trees."
)

lines.append("")

lines.append(
    "These values are scenario-based planning estimates and should not be interpreted as exact planting requirements."
)

lines.append("")

lines.append(
    "7. MAIN CONTRIBUTION"
)

lines.append("")

lines.append(
    "The main contribution of this project is not simply the prediction of land surface temperature."
)

lines.append(
    "The system converts multiple environmental datasets into a spatial planning workflow that answers three practical questions:"
)

lines.append("")

lines.append(
    "Where are persistent urban heat hotspots located?"
)

lines.append(
    "Which hotspot areas should receive cooling intervention first?"
)

lines.append(
    "What type and approximate scale of cooling intervention may be appropriate?"
)

lines.append("")

lines.append(
    "This makes the project suitable as the foundation for an urban heat decision-support system."
)

lines.append("")

lines.append(
    "8. FUTURE SCOPE"
)

lines.append("")

lines.append(
    "The current system can be expanded in several directions."
)

lines.append("")

lines.append(
    "8.1 Additional Satellite Years"
)

lines.append("")

lines.append(
    "Future analysis should include multiple years of Landsat and Sentinel imagery."
)

lines.append(
    "This would allow the system to distinguish persistent long-term hotspots from unusual conditions occurring within a single year."
)

lines.append("")

lines.append(
    "8.2 Ground Validation"
)

lines.append("")

lines.append(
    "Ground-based temperature observations can be integrated from weather stations, IoT sensors or mobile temperature surveys."
)

lines.append(
    "These measurements would improve validation of satellite-derived and model-predicted heat patterns."
)

lines.append("")

lines.append(
    "8.3 Official Administrative Boundaries"
)

lines.append("")

lines.append(
    "Future versions can integrate official BBMP ward and Bengaluru administrative boundaries."
)

lines.append(
    "This would allow heat and cooling statistics to be reported directly by ward instead of only by grid cell and reverse-geocoded locality."
)

lines.append("")

lines.append(
    "8.4 Population and Vulnerability"
)

lines.append("")

lines.append(
    "Population density, elderly population, schools, hospitals, informal settlements and socioeconomic indicators can be added."
)

lines.append(
    "This would allow the system to move from heat-priority mapping toward heat-risk and vulnerability mapping."
)

lines.append("")

lines.append(
    "8.5 Urban Morphology"
)

lines.append("")

lines.append(
    "Building height, road density, impervious-surface fraction, sky-view factor and local shading can improve neighbourhood-scale heat modelling."
)

lines.append("")

lines.append(
    "8.6 Tree-Species Planning"
)

lines.append("")

lines.append(
    "The current tree calculation estimates canopy requirements."
)

lines.append(
    "Future work can recommend locally suitable tree species based on canopy size, water demand, survival rate, road width, soil conditions and available planting space."
)

lines.append("")

lines.append(
    "8.7 Cooling Impact Simulation"
)

lines.append("")

lines.append(
    "A future model can estimate expected temperature reduction after different interventions."
)

lines.append(
    "For example, the system could compare scenarios such as increasing tree canopy by 10%, applying cool roofs or combining vegetation and reflective surfaces."
)

lines.append("")

lines.append(
    "8.8 Real-Time Weather Integration"
)

lines.append("")

lines.append(
    "Real-time and forecast weather information can be integrated to create short-term urban heat alerts."
)

lines.append(
    "The current persistent-hotspot map could then be combined with forecast heat conditions."
)

lines.append("")

lines.append(
    "8.9 Interactive Web Decision-Support System"
)

lines.append("")

lines.append(
    "The next stage of the project is to publish the final analysis through an interactive website."
)

lines.append(
    "Users will be able to explore the Bengaluru heat map, select grid cells, inspect locality-level results, view hotspot rankings and examine cooling recommendations."
)

lines.append(
    "The website can also display planning reliability so that observed and model-supported results are clearly distinguished."
)

lines.append("")

lines.append(
    "8.10 Automated Processing"
)

lines.append("")

lines.append(
    "The complete workflow can eventually be automated so that new satellite observations update the heat map and planning indicators without rebuilding the analysis manually."
)

lines.append("")

lines.append(
    "9. FINAL STATEMENT"
)

lines.append("")

lines.append(
    "The project demonstrates how Earth-observation data and machine learning can be transformed into actionable urban heat-mitigation information."
)

lines.append(
    "Rather than displaying temperature alone, the final framework identifies persistent hotspots, evaluates evidence strength, prioritizes intervention areas and provides scenario-based cooling recommendations."
)

lines.append(
    "The resulting datasets provide the foundation for the final Bengaluru Urban Heat Mitigation web-based decision-support system."
)

# Save conclusion

with open(
    output_file,
    "w",
    encoding="utf-8"
) as file:

    file.write(
        "\n".join(
            lines
        )
    )

print(
    "\nSTEP 49 COMPLETE"
)

print(
    "\nProject summary:"
)

print(
    "Study grid:",
    total_cells,
    "cells"
)

print(
    "Study area:",
    round(
        study_area_km2,
        2
    ),
    "km2"
)

print(
    "High + Very High:",
    priority_cells
)

print(
    "Priority percentage:",
    round(
        priority_percent,
        2
    )
)

print(
    "Hotspot clusters:",
    len(ranking)
)

print(
    "Top hotspot:",
    top_locality
)

print(
    "Scenario-based trees:",
    total_trees
)

print(
    "\nConclusion and future scope saved at:"
)

print(
    output_file
)