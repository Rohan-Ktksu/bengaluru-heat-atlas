from pathlib import Path
import pandas as pd

# Step 48: Generate validation and limitations summary

# Paths

script_folder = Path(__file__).resolve().parent
project_folder = script_folder.parent

validation_file = (
    project_folder
    / "src"
    / "complete_grid_validation.csv"
)

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
    / "validation_and_limitations.txt"
)

# Load datasets

validation = pd.read_csv(
    validation_file
)

grid = pd.read_csv(
    grid_file
)

ranking = pd.read_csv(
    ranking_file
)

print("Validation dataset loaded.")
print("Matched reliable cells:", len(validation))

print("\nFinal grid loaded.")
print("Grid cells:", len(grid))

print("\nHotspot clusters loaded.")
print("Clusters:", len(ranking))

# Complete-grid validation statistics

validation_mae = (
    validation[
        "Absolute_LST_Difference"
    ]
    .mean()
)

validation_rmse = (
    (
        validation[
            "LST_Difference"
        ] ** 2
    )
    .mean()
    ** 0.5
)

validation_correlation = (
    validation[
        [
            "Old_Median_LST",
            "New_Median_LST"
        ]
    ]
    .corr()
    .iloc[0, 1]
)

priority_match_percent = (
    validation[
        "Priority_Match"
    ]
    .mean()
    * 100
)

median_absolute_difference = (
    validation[
        "Absolute_LST_Difference"
    ]
    .median()
)

percentile_90_difference = (
    validation[
        "Absolute_LST_Difference"
    ]
    .quantile(
        0.90
    )
)

# Reliability statistics

reliability_counts = (
    grid[
        "Planning_Reliability"
    ]
    .value_counts()
)

strong_cells = int(
    reliability_counts.get(
        "Strong",
        0
    )
)

moderate_cells = int(
    reliability_counts.get(
        "Moderate",
        0
    )
)

limited_cells = int(
    reliability_counts.get(
        "Limited",
        0
    )
)

model_only_cells = int(
    reliability_counts.get(
        "Model Only",
        0
    )
)

# Data source statistics

source_counts = (
    grid[
        "Data_Source"
    ]
    .value_counts()
)

reliable_source_cells = int(
    source_counts.get(
        "Reliable Multi-Date Observation",
        0
    )
)

limited_source_cells = int(
    source_counts.get(
        "Limited Observation + V5",
        0
    )
)

prediction_only_cells = int(
    source_counts.get(
        "V5 Prediction Only",
        0
    )
)

# Hotspot statistics

hot = grid[
    grid[
        "Final_Cooling_Priority"
    ]
    .isin(
        [
            "High",
            "Very High"
        ]
    )
].copy()

hot_cells = len(hot)

hot_reliable = int(
    hot[
        "Data_Source"
    ]
    .eq(
        "Reliable Multi-Date Observation"
    )
    .sum()
)

hot_limited = int(
    hot[
        "Data_Source"
    ]
    .eq(
        "Limited Observation + V5"
    )
    .sum()
)

hot_prediction_only = int(
    hot[
        "Data_Source"
    ]
    .eq(
        "V5 Prediction Only"
    )
    .sum()
)

# Tree-planning statistics

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

tree_canopy_area = (
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

# Build validation and limitations summary

lines = []

lines.append(
    "BENGALURU URBAN HEAT MITIGATION PROJECT"
)

lines.append(
    "VALIDATION, CONFIDENCE AND LIMITATIONS"
)

lines.append("")

lines.append(
    "1. COMPLETE-GRID VALIDATION"
)

lines.append("")

lines.append(
    f"The complete-grid V5 prediction surface was compared against {len(validation)} cells from the earlier reliable multi-date hotspot analysis."
)

lines.append(
    f"Mean absolute difference between the two median-LST surfaces: {validation_mae:.2f} C."
)

lines.append(
    f"Root mean square difference: {validation_rmse:.2f} C."
)

lines.append(
    f"Median absolute difference: {median_absolute_difference:.2f} C."
)

lines.append(
    f"90th percentile absolute difference: {percentile_90_difference:.2f} C."
)

lines.append(
    f"Correlation between the two median-LST surfaces: {validation_correlation:.3f}."
)

lines.append(
    f"Exact cooling-priority agreement: {priority_match_percent:.2f}%."
)

lines.append("")

lines.append(
    "These statistics describe agreement between the original persistent-analysis surface and the complete-grid V5 surface."
)

lines.append(
    "They should not be reported as the independent test accuracy of the V5 machine-learning model."
)

lines.append("")

lines.append(
    "2. WHY A HYBRID APPROACH WAS USED"
)

lines.append("")

lines.append(
    "The complete-grid V5 prediction surface did not reproduce all observed hotspot patterns sufficiently well."
)

lines.append(
    "Several strong historical hotspot cells were reduced substantially when represented only by complete-grid V5 predictions."
)

lines.append(
    "Therefore, reliable multi-date hotspot observations were preserved instead of being replaced by V5 predictions."
)

lines.append(
    "V5 was used primarily to supplement limited-observation areas and to provide predictions for cells with no historical observations."
)

lines.append("")

lines.append(
    "The final heat surface is therefore a hybrid evidence surface rather than a purely model-generated temperature surface."
)

lines.append("")

lines.append(
    "3. PLANNING RELIABILITY"
)

lines.append("")

lines.append(
    f"Strong planning-reliability cells: {strong_cells}"
)

lines.append(
    f"Moderate planning-reliability cells: {moderate_cells}"
)

lines.append(
    f"Limited planning-reliability cells: {limited_cells}"
)

lines.append(
    f"Model-only cells: {model_only_cells}"
)

lines.append("")

lines.append(
    "Planning reliability indicates the strength of observational support behind each grid cell."
)

lines.append(
    "It does not represent a formal statistical confidence interval."
)

lines.append("")

lines.append(
    "4. DATA-SOURCE COVERAGE"
)

lines.append("")

lines.append(
    f"Reliable multi-date observation cells: {reliable_source_cells}"
)

lines.append(
    f"Limited observation plus V5 cells: {limited_source_cells}"
)

lines.append(
    f"V5 prediction-only cells: {prediction_only_cells}"
)

lines.append("")

lines.append(
    "Prediction-only cells should be interpreted more cautiously because they lack direct multi-date historical support in the final persistent analysis."
)

lines.append("")

lines.append(
    "5. HOTSPOT EVIDENCE"
)

lines.append("")

lines.append(
    f"High and Very High priority cells: {hot_cells}"
)

lines.append(
    f"High/Very High cells supported by reliable multi-date observations: {hot_reliable}"
)

lines.append(
    f"High/Very High cells supported by limited observations plus V5: {hot_limited}"
)

lines.append(
    f"High/Very High cells based on V5 prediction only: {hot_prediction_only}"
)

lines.append("")

lines.append(
    "The strongest hotspot conclusions should be based primarily on reliable and moderate-observation cells rather than prediction-only cells."
)

lines.append("")

lines.append(
    "6. APRIL 17, 2026 OUTLIER"
)

lines.append("")

lines.append(
    "The 17 April 2026 Landsat date showed unusually poor V5 agreement compared with the other 2026 evaluation dates."
)

lines.append(
    "The model substantially overpredicted mean LST for that date."
)

lines.append(
    "This period coincided with hot pre-monsoon conditions and changing atmospheric conditions over Bengaluru."
)

lines.append(
    "The date was retained rather than manually removed because it represents a real difficult prediction regime."
)

lines.append(
    "The project reduces the influence of individual extreme dates by using multi-date persistent-heat analysis and median temperature measures."
)

lines.append("")

lines.append(
    "7. CLOUD AND SATELLITE DATA LIMITATIONS"
)

lines.append("")

lines.append(
    "Landsat and Sentinel observations can be affected by cloud cover, cloud shadows, atmospheric effects and differences in acquisition date."
)

lines.append(
    "Some Landsat-derived values were unavailable in individual grid cells after cloud masking."
)

lines.append(
    "Missing slowly changing spatial features were filled using the median value for the same grid cell across other available dates."
)

lines.append(
    "If no same-cell value was available, a date-level median and then an overall median were used as fallback values."
)

lines.append("")

lines.append(
    "8. TEMPORAL SAMPLING LIMITATION"
)

lines.append("")

lines.append(
    "The persistent 2026 analysis is based on seven Landsat dates rather than continuous daily satellite observations."
)

lines.append(
    "Therefore, the project represents sampled seasonal heat behaviour rather than every short-duration heat event."
)

lines.append(
    "Additional cloud-free scenes and future years would improve temporal robustness."
)

lines.append("")

lines.append(
    "9. WEATHER-DATA LIMITATION"
)

lines.append("")

lines.append(
    "Meteorological variables were integrated with satellite features, but regional atmospheric datasets do not fully capture street-scale urban microclimates."
)

lines.append(
    "Local shading, traffic, building geometry, construction materials and anthropogenic heat can create variations below the resolution of the atmospheric datasets."
)

lines.append("")

lines.append(
    "10. MACHINE-LEARNING LIMITATION"
)

lines.append("")

lines.append(
    "The V5 model improves coverage but does not replace satellite-measured LST."
)

lines.append(
    "Random Forest regression can smooth extreme temperature behaviour toward patterns represented more strongly in the training data."
)

lines.append(
    "This was one reason the hybrid final heat surface was preferred over a purely V5-generated surface."
)

lines.append("")

lines.append(
    "11. COOLING-PRIORITY CLASSIFICATION"
)

lines.append("")

lines.append(
    "The final Low, Moderate, High and Very High classes are relative planning categories."
)

lines.append(
    "Their boundaries were generated from the heat-score distribution rather than from universal physiological or legal temperature thresholds."
)

lines.append(
    "Therefore, the statement that 25% of the study grid is High or Very High follows directly from the percentile-based planning classification."
)

lines.append(
    "It should not be interpreted as meaning exactly 25% of Bengaluru exceeds an externally defined dangerous-temperature threshold."
)

lines.append("")

lines.append(
    "12. TREE-COUNT ASSUMPTION"
)

lines.append("")

lines.append(
    f"The final planning scenario estimates approximately {total_trees:,} trees across the complete study grid."
)

lines.append(
    f"Approximately {hotspot_trees:,} trees are associated with High and Very High priority areas."
)

lines.append(
    "Tree calculations assume approximately 30 square metres of mature effective canopy per tree."
)

lines.append(
    "The calculation represents a planning scenario rather than an exact biological planting requirement."
)

lines.append(
    "Species, spacing, survival rate, mature canopy size, road width, underground utilities, land ownership and available planting space must be assessed before implementation."
)

lines.append("")

lines.append(
    "13. NON-TREE COOLING"
)

lines.append("")

lines.append(
    f"Scenario-based tree-canopy target area: {tree_canopy_area:,.0f} m2."
)

lines.append(
    f"Scenario-based non-tree cooling area: {non_tree_area:,.0f} m2."
)

lines.append(
    "Highly built-up cells are not assumed to solve all heat mitigation through trees."
)

lines.append(
    "The project also recommends green roofs, cool roofs, reflective surfaces, pocket parks, shaded corridors and other complementary interventions."
)

lines.append("")

lines.append(
    "14. LOCALITY-NAME LIMITATION"
)

lines.append("")

lines.append(
    "Locality names were obtained through reverse geocoding of grid-cell centre coordinates."
)

lines.append(
    "A 1 km cell can overlap several neighbourhoods, so the returned locality should be treated as a convenient geographic label rather than an exact administrative boundary."
)

lines.append("")

lines.append(
    "15. STUDY-BOUNDARY LIMITATION"
)

lines.append("")

lines.append(
    "The final analysis uses the rectangular Bengaluru study region defined for the remote-sensing workflow."
)

lines.append(
    "The 1,320 km2 figure refers to this analysis grid and should not be presented as the official administrative area of Bengaluru or BBMP."
)

lines.append(
    "A future version can clip results to official BBMP ward or metropolitan boundaries."
)

lines.append("")

lines.append(
    "16. SAFE INTERPRETATION OF RESULTS"
)

lines.append("")

lines.append(
    "The project can support statements about relative urban heat patterns, persistent hotspot locations, cooling-priority zones and scenario-based mitigation requirements."
)

lines.append(
    "The project should not claim that the model measures exact street-level temperatures everywhere."
)

lines.append(
    "The project should not claim that the estimated tree count is the exact number Bengaluru must plant."
)

lines.append(
    "The project should not treat model-only cells as having the same observational confidence as reliable multi-date cells."
)

lines.append("")

lines.append(
    "17. RECOMMENDED FUTURE VALIDATION"
)

lines.append("")

lines.append(
    "Future validation should include ground-based weather stations, mobile temperature surveys, additional Landsat years, more cloud-free dates and local urban morphology data."
)

lines.append(
    "Validation against ward-level heat observations would further improve the planning usefulness of the system."
)

# Save summary

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

print("\nSTEP 48 COMPLETE")

print("\nValidation summary:")
print("Matched reliable cells:", len(validation))
print("Complete-grid comparison MAE:", validation_mae)
print("Complete-grid comparison RMSE:", validation_rmse)
print("Complete-grid correlation:", validation_correlation)
print("Priority exact match:", priority_match_percent)

print("\nReliability summary:")
print("Strong:", strong_cells)
print("Moderate:", moderate_cells)
print("Limited:", limited_cells)
print("Model Only:", model_only_cells)

print("\nValidation and limitations saved at:")
print(output_file)