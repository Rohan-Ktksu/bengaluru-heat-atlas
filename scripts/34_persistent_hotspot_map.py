import pandas as pd
import numpy as np
import folium
from pathlib import Path


# =====================================================
# STEP 34
# Persistent Hotspot + Tree Recommendation Map
# Corrected Grid Alignment Version
# =====================================================


# -----------------------------------------------------
# 1. File paths
# -----------------------------------------------------

script_folder = Path(__file__).resolve().parent
project_folder = script_folder.parent

input_file = (
    project_folder
    / "src"
    / "bengaluru_persistent_hotspot_tree_plan.csv"
)

output_file = (
    project_folder
    / "src"
    / "bengaluru_persistent_hotspot_tree_map.html"
)


# -----------------------------------------------------
# 2. Load dataset
# -----------------------------------------------------

df = pd.read_csv(input_file)

print("Persistent hotspot tree plan loaded.")

print("\nTotal reliable grid cells:")
print(len(df))


# -----------------------------------------------------
# 3. Observation confidence
# -----------------------------------------------------

def confidence_level(unique_dates):

    if unique_dates >= 6:
        return "Very High"

    elif unique_dates >= 5:
        return "High"

    elif unique_dates >= 4:
        return "Moderate"

    else:
        return "Basic"


df["Confidence"] = (
    df["Unique_Dates"]
    .apply(confidence_level)
)

print("\nConfidence distribution:")
print(df["Confidence"].value_counts())


# -----------------------------------------------------
# 4. Grid configuration
#
# MUST match Step 33
# -----------------------------------------------------

cell_size_m = 1000

lat_m_per_degree = 111320

mean_latitude = df["Latitude"].mean()

lon_m_per_degree = (
    111320
    * np.cos(
        np.radians(mean_latitude)
    )
)


# -----------------------------------------------------
# 5. Extract Grid_X and Grid_Y
#
# Grid_ID example:
#
# 8408_1460
#
# Grid_X = 8408
# Grid_Y = 1460
# -----------------------------------------------------

grid_parts = (
    df["Grid_ID"]
    .astype(str)
    .str.split(
        "_",
        expand=True
    )
)

df["Grid_X"] = (
    grid_parts[0]
    .astype(int)
)

df["Grid_Y"] = (
    grid_parts[1]
    .astype(int)
)


# -----------------------------------------------------
# 6. Calculate EXACT grid boundaries
#
# Step 33 originally created:
#
# Grid_X = floor(X_Meters / 1000)
# Grid_Y = floor(Y_Meters / 1000)
#
# Therefore:
#
# west  = Grid_X * 1000
# east  = west + 1000
#
# south = Grid_Y * 1000
# north = south + 1000
# -----------------------------------------------------

df["West_Meters"] = (
    df["Grid_X"]
    * cell_size_m
)

df["East_Meters"] = (
    df["West_Meters"]
    + cell_size_m
)

df["South_Meters"] = (
    df["Grid_Y"]
    * cell_size_m
)

df["North_Meters"] = (
    df["South_Meters"]
    + cell_size_m
)


# -----------------------------------------------------
# 7. Convert projected grid boundaries back to
# latitude / longitude
# -----------------------------------------------------

df["West_Longitude"] = (
    df["West_Meters"]
    / lon_m_per_degree
)

df["East_Longitude"] = (
    df["East_Meters"]
    / lon_m_per_degree
)

df["South_Latitude"] = (
    df["South_Meters"]
    / lat_m_per_degree
)

df["North_Latitude"] = (
    df["North_Meters"]
    / lat_m_per_degree
)


# -----------------------------------------------------
# 8. Calculate true grid center
# -----------------------------------------------------

df["Grid_Center_Latitude"] = (
    (
        df["South_Latitude"]
        + df["North_Latitude"]
    )
    / 2
)

df["Grid_Center_Longitude"] = (
    (
        df["West_Longitude"]
        + df["East_Longitude"]
    )
    / 2
)


# -----------------------------------------------------
# 9. Map center
# -----------------------------------------------------

center_latitude = (
    df["Grid_Center_Latitude"]
    .mean()
)

center_longitude = (
    df["Grid_Center_Longitude"]
    .mean()
)


# -----------------------------------------------------
# 10. Create map
# -----------------------------------------------------

heat_map = folium.Map(
    location=[
        center_latitude,
        center_longitude
    ],
    zoom_start=11,
    tiles="OpenStreetMap",
    control_scale=True
)


# -----------------------------------------------------
# 11. Create priority layers
# -----------------------------------------------------

low_layer = folium.FeatureGroup(
    name="Low Priority",
    show=True
)

moderate_layer = folium.FeatureGroup(
    name="Moderate Priority",
    show=True
)

high_layer = folium.FeatureGroup(
    name="High Priority",
    show=True
)

very_high_layer = folium.FeatureGroup(
    name="Very High Priority",
    show=True
)

layers = {
    "Low": low_layer,
    "Moderate": moderate_layer,
    "High": high_layer,
    "Very High": very_high_layer
}


# -----------------------------------------------------
# 12. Priority colors
# -----------------------------------------------------

priority_colors = {
    "Low": "green",
    "Moderate": "yellow",
    "High": "orange",
    "Very High": "red"
}


# -----------------------------------------------------
# 13. Draw exact grid cells
# -----------------------------------------------------

for _, row in df.iterrows():

    priority = (
        row[
            "Persistent_Cooling_Priority"
        ]
    )

    color = priority_colors.get(
        priority,
        "gray"
    )

    layer = layers.get(
        priority,
        low_layer
    )

    bounds = [
        [
            row["South_Latitude"],
            row["West_Longitude"]
        ],
        [
            row["North_Latitude"],
            row["East_Longitude"]
        ]
    ]

    popup_html = f"""
    <div style="
        width: 340px;
        font-family: Arial;
        font-size: 13px;
    ">

    <h3 style="margin-bottom:5px;">
    Bengaluru Heat-Mitigation Area
    </h3>

    <hr>

    <b>Grid ID:</b>
    {row['Grid_ID']}
    <br>

    <b>Priority:</b>
    {priority}
    <br>

    <b>Confidence:</b>
    {row['Confidence']}
    <br>

    <b>Observation Dates:</b>
    {int(row['Unique_Dates'])}

    <hr>

    <b>Median Predicted LST:</b>
    {row['Median_Predicted_LST']:.2f} °C
    <br>

    <b>Maximum Predicted LST:</b>
    {row['Maximum_Predicted_LST']:.2f} °C
    <br>

    <b>Hot Frequency:</b>
    {row['Hot_Frequency'] * 100:.1f} %
    <br>

    <b>Very Hot Frequency:</b>
    {row['Very_Hot_Frequency'] * 100:.1f} %
    <br>

    <b>Persistent Heat Score:</b>
    {row['Persistent_Heat_Score']:.1f} / 100

    <hr>

    <b>Tree Probability:</b>
    {row['Median_Tree_Probability']:.3f}
    <br>

    <b>Built Probability:</b>
    {row['Median_Built_Probability']:.3f}
    <br>

    <b>Landsat NDVI:</b>
    {row['Median_L_NDVI']:.3f}
    <br>

    <b>Sentinel-2 NDVI:</b>
    {row['Median_S2_NDVI']:.3f}

    <hr>

    <b>Suggested Additional Greening:</b>
    {row['Suggested_Greening_Percent']:.1f} %
    <br>

    <b>Approx. Trees to Plant:</b>
    {int(row['Approx_Trees_To_Plant']):,}
    <br>

    <b>Trees per Hectare:</b>
    {row['Trees_Per_Hectare']:.1f}
    <br>

    <b>Cell Area:</b>
    {row['Cell_Area_hectares']:.0f} hectares

    <hr>

    <b>Recommended Action:</b>
    <br>

    {row['Recommended_Action']}

    <hr>

    <small>
    Tree numbers are scenario-based planning estimates.
    They assume approximately
    {row['Assumed_Mature_Canopy_Per_Tree_m2']:.0f} m²
    mature effective canopy per tree.
    </small>

    </div>
    """

    folium.Rectangle(
        bounds=bounds,

        # Thin border makes adjacent cells
        # visually blend together better
        color=color,
        weight=0.6,

        fill=True,
        fill_color=color,

        # Slightly stronger fill
        fill_opacity=0.52,

        popup=folium.Popup(
            popup_html,
            max_width=400
        ),

        tooltip=(
            f"{priority} | "
            f"{row['Median_Predicted_LST']:.1f}°C | "
            f"{row['Hot_Frequency'] * 100:.0f}% hot | "
            f"{int(row['Approx_Trees_To_Plant']):,} trees"
        )
    ).add_to(layer)


# -----------------------------------------------------
# 14. Add layers
# -----------------------------------------------------

low_layer.add_to(heat_map)
moderate_layer.add_to(heat_map)
high_layer.add_to(heat_map)
very_high_layer.add_to(heat_map)


# -----------------------------------------------------
# 15. Legend
# -----------------------------------------------------

legend_html = """
<div style="
position: fixed;
bottom: 40px;
left: 40px;
width: 235px;
background-color: white;
border: 1px solid #777;
z-index: 9999;
font-size: 14px;
padding: 12px;
border-radius: 6px;
">

<b>Persistent Cooling Priority</b>

<br><br>

<span style="
background:green;
display:inline-block;
width:16px;
height:16px;">
</span>
&nbsp; Low

<br><br>

<span style="
background:yellow;
display:inline-block;
width:16px;
height:16px;">
</span>
&nbsp; Moderate

<br><br>

<span style="
background:orange;
display:inline-block;
width:16px;
height:16px;">
</span>
&nbsp; High

<br><br>

<span style="
background:red;
display:inline-block;
width:16px;
height:16px;">
</span>
&nbsp; Very High

<br><br>

<small>
1 km × 1 km analysis cells.<br>
Minimum 3 observation dates.
</small>

</div>
"""

heat_map.get_root().html.add_child(
    folium.Element(
        legend_html
    )
)


# -----------------------------------------------------
# 16. Layer control
# -----------------------------------------------------

folium.LayerControl(
    collapsed=False
).add_to(
    heat_map
)


# -----------------------------------------------------
# 17. Fit map automatically to grid extent
# -----------------------------------------------------

heat_map.fit_bounds(
    [
        [
            df["South_Latitude"].min(),
            df["West_Longitude"].min()
        ],
        [
            df["North_Latitude"].max(),
            df["East_Longitude"].max()
        ]
    ]
)


# -----------------------------------------------------
# 18. Save map
# -----------------------------------------------------

heat_map.save(
    output_file
)

print(
    "\nCorrected persistent hotspot map created."
)

print("\nSaved at:")
print(output_file)

print(
    "\nPriority distribution:"
)

print(
    df[
        "Persistent_Cooling_Priority"
    ]
    .value_counts()
)

print(
    "\nConfidence distribution:"
)

print(
    df[
        "Confidence"
    ]
    .value_counts()
)

print(
    "\nTotal estimated trees:"
)

print(
    int(
        df[
            "Approx_Trees_To_Plant"
        ]
        .sum()
    )
)

print(
    "\nGrid boundary check:"
)

print(
    df[
        [
            "Grid_ID",
            "South_Latitude",
            "North_Latitude",
            "West_Longitude",
            "East_Longitude"
        ]
    ]
    .head()
    .to_string(
        index=False
    )
)