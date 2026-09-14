from pathlib import Path
import pandas as pd

# Step 47: Generate final methodology summary

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

methodology_file = (
    output_folder
    / "methodology_summary.txt"
)

# Load final datasets

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

# V5 model features

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
    "Overpass_Relative_Humidity",
    "Overpass_Wind_Speed",
    "Overpass_Solar_Radiation",
    "Overpass_Cloud_Cover"
]

print(
    "\nV5 feature count:",
    len(v5_features)
)

# Final grid statistics

total_cells = len(grid)

high_cells = (
    grid[
        "Final_Cooling_Priority"
    ]
    .isin(
        [
            "High"
        ]
    )
    .sum()
)

very_high_cells = (
    grid[
        "Final_Cooling_Priority"
    ]
    .isin(
        [
            "Very High"
        ]
    )
    .sum()
)

hot_cells = (
    high_cells
    + very_high_cells
)

total_trees = int(
    grid[
        "Approx_Trees_To_Plant"
    ]
    .sum()
)

# Observation support

reliable_cells = (
    grid[
        "Data_Source"
    ]
    .eq(
        "Reliable Multi-Date Observation"
    )
    .sum()
)

limited_cells = (
    grid[
        "Data_Source"
    ]
    .eq(
        "Limited Observation + V5"
    )
    .sum()
)

prediction_only_cells = (
    grid[
        "Data_Source"
    ]
    .eq(
        "V5 Prediction Only"
    )
    .sum()
)

# Prepare methodology text

lines = []

lines.append(
    "BENGALURU URBAN HEAT MITIGATION PROJECT"
)

lines.append(
    "FINAL METHODOLOGY SUMMARY"
)

lines.append("")

lines.append(
    "1. STUDY AREA"
)

lines.append("")

lines.append(
    "The Bengaluru study region was divided into approximately 1 km x 1 km grid cells."
)

lines.append(
    f"The final complete analysis contains {total_cells} grid cells, representing approximately {total_cells} km2."
)

lines.append("")

lines.append(
    "2. REMOTE-SENSING DATA"
)

lines.append("")

lines.append(
    "Landsat imagery was used for land-surface and spectral information."
)

lines.append(
    "Sentinel-2 imagery was used to provide additional vegetation information at higher spatial resolution."
)

lines.append(
    "Dynamic World land-cover probabilities were used to represent built-up and tree-cover characteristics."
)

lines.append(
    "Elevation and distance-to-water information were included as spatial environmental variables."
)

lines.append("")

lines.append(
    "3. SPECTRAL AND LAND-SURFACE FEATURES"
)

lines.append("")

lines.append(
    "The remote-sensing feature set includes Landsat NDVI, NDBI, NDWI, Sentinel-2 NDVI, albedo, built probability, tree probability, elevation and distance to water."
)

lines.append("")

lines.append(
    "NDVI represents vegetation condition."
)

lines.append(
    "NDBI represents built-up characteristics."
)

lines.append(
    "NDWI represents surface-water or moisture-related characteristics."
)

lines.append(
    "Tree probability represents the likelihood of tree cover."
)

lines.append(
    "Built probability represents the likelihood of built-up land cover."
)

lines.append("")

lines.append(
    "4. WEATHER AND TEMPORAL FEATURES"
)

lines.append("")

lines.append(
    "Weather variables were integrated with satellite observations to improve land-surface-temperature prediction."
)

lines.append(
    "The model includes air temperature, wind speed, relative humidity, soil moisture, precipitation, solar radiation and cloud cover."
)

lines.append(
    "Three-day and seven-day temporal weather features were also included."
)

lines.append(
    "Weather conditions near the satellite overpass time were represented using overpass-specific meteorological features."
)

lines.append("")

lines.append(
    "5. V5 LAND-SURFACE-TEMPERATURE MODEL"
)

lines.append("")

lines.append(
    f"The final V5 prediction model uses {len(v5_features)} input features."
)

lines.append("")

for number, feature in enumerate(
    v5_features,
    start=1
):

    lines.append(
        f"{number}. {feature}"
    )

lines.append("")

lines.append(
    "The trained V5 model predicts land surface temperature for each grid cell and observation date."
)

lines.append(
    "The same saved feature order was used during complete-grid prediction to ensure compatibility with the trained model."
)

lines.append("")

lines.append(
    "6. COMPLETE BENGALURU GRID"
)

lines.append("")

lines.append(
    "A complete rectangular 1 km analysis grid was created so that spatial gaps in the original observations would not appear as blank cells in the final planning map."
)

lines.append(
    "Seven prediction dates were processed for every grid cell."
)

lines.append(
    "This produced 9,240 date-level grid predictions."
)

lines.append("")

lines.append(
    "The seven prediction dates were:"
)

lines.append(
    "27 January 2026"
)

lines.append(
    "12 February 2026"
)

lines.append(
    "28 February 2026"
)

lines.append(
    "16 March 2026"
)

lines.append(
    "1 April 2026"
)

lines.append(
    "17 April 2026"
)

lines.append(
    "3 May 2026"
)

lines.append("")

lines.append(
    "7. OBSERVATION SUPPORT"
)

lines.append("")

lines.append(
    f"Reliable multi-date observation cells: {reliable_cells}"
)

lines.append(
    f"Limited observation plus V5 cells: {limited_cells}"
)

lines.append(
    f"V5 prediction-only cells: {prediction_only_cells}"
)

lines.append("")

lines.append(
    "Cells with sufficient historical multi-date observations were retained as the strongest source of persistent-heat evidence."
)

lines.append(
    "Where historical support was limited, V5 predictions were used to provide additional spatial and temporal support."
)

lines.append(
    "Cells without historical observations were represented using V5 prediction only."
)

lines.append("")

lines.append(
    "8. HYBRID HEAT GRID"
)

lines.append("")

lines.append(
    "The final heat grid uses a hybrid strategy instead of replacing reliable historical observations with complete-grid predictions."
)

lines.append(
    "Reliable multi-date observations were retained where available."
)

lines.append(
    "Limited-observation cells were supplemented using V5 predictions."
)

lines.append(
    "Prediction-only cells were included with lower planning confidence."
)

lines.append("")

lines.append(
    "This approach preserves strong observed hotspot evidence while providing complete spatial coverage."
)

lines.append("")

lines.append(
    "9. PERSISTENT HEAT ANALYSIS"
)

lines.append("")

lines.append(
    "Heat priority was not based only on a single hot satellite image."
)

lines.append(
    "Persistent heat was evaluated using multi-date temperature behaviour, including median predicted LST, maximum LST, hot frequency and very-hot frequency."
)

lines.append(
    "Tree-cover and built-up probabilities were also incorporated into the heat-priority analysis."
)

lines.append("")

lines.append(
    "10. COOLING PRIORITY"
)

lines.append("")

lines.append(
    "Each grid cell was assigned one of four final cooling-priority classes:"
)

lines.append(
    "Low"
)

lines.append(
    "Moderate"
)

lines.append(
    "High"
)

lines.append(
    "Very High"
)

lines.append("")

lines.append(
    f"High-priority cells: {high_cells}"
)

lines.append(
    f"Very-High-priority cells: {very_high_cells}"
)

lines.append(
    f"Combined High and Very High cells: {hot_cells}"
)

lines.append(
    f"Combined priority area: approximately {hot_cells} km2."
)

lines.append("")

lines.append(
    "11. COOLING INTERVENTION PLAN"
)

lines.append("")

lines.append(
    "The cooling plan considers both tree-based and non-tree cooling interventions."
)

lines.append(
    "Tree interventions include street trees, canopy expansion, pocket parks, urban forests, park restoration and shaded corridors."
)

lines.append(
    "Built-up locations can also require green roofs, cool roofs, reflective pavement and other non-tree cooling measures."
)

lines.append("")

lines.append(
    f"The complete planning scenario estimates approximately {total_trees:,} trees across the study grid."
)

lines.append(
    "This value is a scenario-based planning estimate and is not an exact ecological requirement."
)

lines.append("")

lines.append(
    "12. LOCALITY MAPPING"
)

lines.append("")

lines.append(
    "Grid-cell coordinates were reverse-geocoded to provide locality names for interpretation and website presentation."
)

lines.append(
    "Of the 1,320 final grid cells, locality names were obtained for 1,318 cells."
)

lines.append("")

lines.append(
    "13. CONNECTED HOTSPOT CLUSTERS"
)

lines.append("")

lines.append(
    f"The final analysis identified {len(ranking)} connected High and Very High hotspot clusters."
)

lines.append(
    "Adjacent priority cells were grouped so that the project could identify larger heat zones rather than reporting isolated grid cells only."
)

lines.append("")

lines.append(
    "14. HOTSPOT INTENSITY"
)

lines.append("")

lines.append(
    "Hotspot intensity combines mean heat score, maximum heat score, hot-frequency behaviour and the proportion of Very High cells."
)

lines.append("")

lines.append(
    "Intensity Score ="
)

lines.append(
    "40% Mean Heat Score + 25% Maximum Heat Score + 20% Hot Frequency + 15% Very High Share"
)

lines.append("")

lines.append(
    "15. PLANNING SIGNIFICANCE"
)

lines.append("")

lines.append(
    "Planning significance was designed to identify hotspots that matter most for large-scale cooling intervention."
)

lines.append("")

lines.append(
    "Planning Significance Score ="
)

lines.append(
    "30% Cluster Area + 20% Very High Cell Count + 20% Mean Heat Score + 10% Hot Frequency + 10% Maximum Heat Score + 10% Evidence Score"
)

lines.append("")

lines.append(
    "This prevents a single extremely hot 1 km cell from automatically being considered more important than a large connected persistent hotspot."
)

lines.append("")

lines.append(
    "16. EVIDENCE SCORE"
)

lines.append("")

lines.append(
    "Planning reliability was incorporated into hotspot ranking using an evidence score."
)

lines.append(
    "Strong cells receive the highest evidence weight, followed by Moderate, Limited and Model-Only cells."
)

lines.append("")

lines.append(
    "17. FINAL PROJECT OUTPUT"
)

lines.append("")

lines.append(
    "The final system provides:"
)

lines.append(
    "Complete 1 km Bengaluru heat coverage"
)

lines.append(
    "Multi-date LST predictions"
)

lines.append(
    "Persistent heat assessment"
)

lines.append(
    "Cooling-priority classification"
)

lines.append(
    "Locality-level identification"
)

lines.append(
    "Connected hotspot detection"
)

lines.append(
    "Tree and non-tree cooling recommendations"
)

lines.append(
    "Hotspot intensity ranking"
)

lines.append(
    "Planning-significance ranking"
)

lines.append(
    "Planning reliability information"
)

lines.append("")

lines.append(
    "These outputs form the analytical foundation for the final interactive website and decision-support dashboard."
)

# Save methodology summary

with open(
    methodology_file,
    "w",
    encoding="utf-8"
) as file:

    file.write(
        "\n".join(
            lines
        )
    )

print(
    "\nSTEP 47 COMPLETE"
)

print(
    "\nMethodology summary saved at:"
)

print(
    methodology_file
)

print(
    "\nSummary statistics:"
)

print(
    "Total cells:",
    total_cells
)

print(
    "Reliable cells:",
    reliable_cells
)

print(
    "Limited + V5 cells:",
    limited_cells
)

print(
    "V5-only cells:",
    prediction_only_cells
)

print(
    "High + Very High cells:",
    hot_cells
)

print(
    "Connected hotspot clusters:",
    len(ranking)
)

print(
    "Scenario-based trees:",
    total_trees
)