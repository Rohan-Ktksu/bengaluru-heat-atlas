import pandas as pd
import folium
from pathlib import Path


# ============================================================
# STEP 42
# FINAL BENGALURU COOLING PRIORITY MAP
# ============================================================


# ------------------------------------------------------------
# 1. Paths
# ------------------------------------------------------------

script_folder = Path(__file__).resolve().parent
project_folder = script_folder.parent

input_file = (
    project_folder
    / "src"
    / "bengaluru_final_cooling_tree_plan.csv"
)

output_file = (
    project_folder
    / "src"
    / "bengaluru_final_cooling_priority_map.html"
)


# ------------------------------------------------------------
# 2. Load final cooling plan
# ------------------------------------------------------------

df = pd.read_csv(input_file)

print("Final cooling plan loaded.")

print("\nTotal grid cells:")
print(len(df))

print("\nPriority distribution:")
print(
    df["Final_Cooling_Priority"].value_counts()
)

print("\nPlanning reliability:")
print(
    df["Planning_Reliability"].value_counts()
)


# ------------------------------------------------------------
# 3. Check required columns
# ------------------------------------------------------------

required_columns = [
    "Grid_ID",
    "Center_Latitude",
    "Center_Longitude",
    "South_Latitude",
    "North_Latitude",
    "West_Longitude",
    "East_Longitude",
    "Final_Median_LST",
    "Final_Max_LST",
    "Final_Hot_Frequency",
    "Final_Tree_Probability",
    "Final_Built_Probability",
    "Hybrid_Heat_Score",
    "Final_Cooling_Priority",
    "Suggested_Greening_Percent",
    "Approx_Trees_To_Plant",
    "Trees_Per_Hectare",
    "Non_Tree_Cooling_Area_m2",
    "Data_Source",
    "Confidence_Level",
    "Planning_Reliability",
    "Recommended_Intervention"
]

missing = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing:
    raise ValueError(
        "Missing required columns: "
        + str(missing)
    )


# ------------------------------------------------------------
# 4. Bengaluru map centre
# ------------------------------------------------------------

map_latitude = df["Center_Latitude"].mean()
map_longitude = df["Center_Longitude"].mean()

print("\nMap centre:")
print(map_latitude, map_longitude)


# ------------------------------------------------------------
# 5. Create map
#
# OpenStreetMap does not require CARTO API key.
# ------------------------------------------------------------

m = folium.Map(
    location=[
        map_latitude,
        map_longitude
    ],
    zoom_start=11,
    tiles="OpenStreetMap",
    control_scale=True,
    prefer_canvas=True
)


# ------------------------------------------------------------
# 6. Priority colours
# ------------------------------------------------------------

priority_colors = {
    "Low": "#2ECC71",
    "Moderate": "#F1C40F",
    "High": "#E67E22",
    "Very High": "#E74C3C"
}


# ------------------------------------------------------------
# 7. Reliability border styles
# ------------------------------------------------------------

reliability_styles = {
    "Strong": {
        "weight": 2.5,
        "opacity": 1.0
    },

    "Moderate": {
        "weight": 2.0,
        "opacity": 0.9
    },

    "Limited": {
        "weight": 1.3,
        "opacity": 0.75
    },

    "Model Only": {
        "weight": 1.0,
        "opacity": 0.55
    }
}


# ------------------------------------------------------------
# 8. Feature groups
# ------------------------------------------------------------

low_group = folium.FeatureGroup(
    name="Low Priority",
    show=True
)

moderate_group = folium.FeatureGroup(
    name="Moderate Priority",
    show=True
)

high_group = folium.FeatureGroup(
    name="High Priority",
    show=True
)

very_high_group = folium.FeatureGroup(
    name="Very High Priority",
    show=True
)


priority_groups = {
    "Low": low_group,
    "Moderate": moderate_group,
    "High": high_group,
    "Very High": very_high_group
}


# ------------------------------------------------------------
# 9. Add all 1320 cells
# ------------------------------------------------------------

for _, row in df.iterrows():

    priority = row["Final_Cooling_Priority"]

    color = priority_colors.get(
        priority,
        "#808080"
    )

    reliability = row[
        "Planning_Reliability"
    ]

    border_style = reliability_styles.get(
        reliability,
        {
            "weight": 1,
            "opacity": 0.7
        }
    )

    trees = int(
        row[
            "Approx_Trees_To_Plant"
        ]
    )

    non_tree_area = (
        row[
            "Non_Tree_Cooling_Area_m2"
        ]
    )

    hot_frequency_percent = (
        row[
            "Final_Hot_Frequency"
        ]
        * 100
    )

    tree_probability_percent = (
        row[
            "Final_Tree_Probability"
        ]
        * 100
    )

    built_probability_percent = (
        row[
            "Final_Built_Probability"
        ]
        * 100
    )

    popup_html = f"""
    <div style="
        width: 350px;
        font-family: Arial, sans-serif;
        font-size: 13px;
    ">

        <h3 style="margin-bottom:8px;">
            Bengaluru Cooling Plan
        </h3>

        <hr>

        <b>Grid ID:</b>
        {row['Grid_ID']}
        <br>

        <b>Cooling Priority:</b>
        {priority}
        <br>

        <b>Heat Score:</b>
        {row['Hybrid_Heat_Score']:.2f} / 100
        <br><br>

        <b>Median LST:</b>
        {row['Final_Median_LST']:.2f} °C
        <br>

        <b>Maximum LST:</b>
        {row['Final_Max_LST']:.2f} °C
        <br>

        <b>Hot Frequency:</b>
        {hot_frequency_percent:.1f} %
        <br><br>

        <b>Tree Probability:</b>
        {tree_probability_percent:.1f} %
        <br>

        <b>Built Probability:</b>
        {built_probability_percent:.1f} %
        <br><br>

        <b>Suggested Greening:</b>
        {row['Suggested_Greening_Percent']:.2f} %
        <br>

        <b>Estimated Trees:</b>
        {trees:,}
        <br>

        <b>Trees per Hectare:</b>
        {row['Trees_Per_Hectare']:.2f}
        <br>

        <b>Non-tree Cooling Area:</b>
        {non_tree_area:,.0f} m²
        <br><br>

        <b>Recommended Intervention:</b>
        <br>
        {row['Recommended_Intervention']}
        <br><br>

        <b>Data Source:</b>
        {row['Data_Source']}
        <br>

        <b>Confidence:</b>
        {row['Confidence_Level']}
        <br>

        <b>Planning Reliability:</b>
        {reliability}

    </div>
    """

    tooltip_text = (
        f"{row['Grid_ID']} | "
        f"{priority} | "
        f"{row['Final_Median_LST']:.1f} °C | "
        f"{trees:,} trees"
    )

    rectangle = folium.Rectangle(

        bounds=[
            [
                row["South_Latitude"],
                row["West_Longitude"]
            ],
            [
                row["North_Latitude"],
                row["East_Longitude"]
            ]
        ],

        color="#333333",

        weight=border_style[
            "weight"
        ],

        opacity=border_style[
            "opacity"
        ],

        fill=True,

        fill_color=color,

        fill_opacity=0.62,

        tooltip=folium.Tooltip(
            tooltip_text,
            sticky=True
        ),

        popup=folium.Popup(
            popup_html,
            max_width=420
        )
    )

    rectangle.add_to(
        priority_groups[
            priority
        ]
    )


# ------------------------------------------------------------
# 10. Add groups to map
# ------------------------------------------------------------

low_group.add_to(m)
moderate_group.add_to(m)
high_group.add_to(m)
very_high_group.add_to(m)


# ------------------------------------------------------------
# 11. Legend
# ------------------------------------------------------------

legend_html = """
<div style="
    position: fixed;
    bottom: 35px;
    left: 35px;
    width: 230px;
    background-color: white;
    border: 2px solid #777;
    z-index: 9999;
    font-size: 13px;
    padding: 12px;
    border-radius: 5px;
">

<b>Cooling Priority</b>

<br><br>

<span style="
    display:inline-block;
    width:16px;
    height:16px;
    background:#2ECC71;
    margin-right:7px;
"></span>
Low

<br>

<span style="
    display:inline-block;
    width:16px;
    height:16px;
    background:#F1C40F;
    margin-right:7px;
"></span>
Moderate

<br>

<span style="
    display:inline-block;
    width:16px;
    height:16px;
    background:#E67E22;
    margin-right:7px;
"></span>
High

<br>

<span style="
    display:inline-block;
    width:16px;
    height:16px;
    background:#E74C3C;
    margin-right:7px;
"></span>
Very High

<br><br>

<b>Grid:</b> 1 km × 1 km

<br>

<b>Total cells:</b> 1,320

<br><br>

Click any cell for detailed
cooling recommendations.

</div>
"""

m.get_root().html.add_child(
    folium.Element(
        legend_html
    )
)


# ------------------------------------------------------------
# 12. Title
# ------------------------------------------------------------

title_html = """
<div style="
    position: fixed;
    top: 10px;
    left: 50%;
    transform: translateX(-50%);
    background-color: rgba(255,255,255,0.94);
    border: 1px solid #777;
    padding: 10px 18px;
    z-index: 9999;
    border-radius: 6px;
    font-family: Arial, sans-serif;
    text-align: center;
">

<div style="
    font-size:18px;
    font-weight:bold;
">
Bengaluru Urban Heat Mitigation Plan
</div>

<div style="
    font-size:12px;
    margin-top:3px;
">
Hybrid Satellite Observation + V5 Machine Learning
</div>

</div>
"""

m.get_root().html.add_child(
    folium.Element(
        title_html
    )
)


# ------------------------------------------------------------
# 13. Layer control
# ------------------------------------------------------------

folium.LayerControl(
    collapsed=False
).add_to(m)


# ------------------------------------------------------------
# 14. Fit map exactly to grid
# ------------------------------------------------------------

south = df[
    "South_Latitude"
].min()

north = df[
    "North_Latitude"
].max()

west = df[
    "West_Longitude"
].min()

east = df[
    "East_Longitude"
].max()

m.fit_bounds(
    [
        [
            south,
            west
        ],
        [
            north,
            east
        ]
    ]
)


# ------------------------------------------------------------
# 15. Save map
# ------------------------------------------------------------

m.save(
    output_file
)


# ------------------------------------------------------------
# 16. Final output
# ------------------------------------------------------------

print(
    "\n======================================"
)

print(
    "STEP 42 COMPLETE"
)

print(
    "======================================"
)

print(
    "\nGrid cells mapped:"
)

print(
    len(df)
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
    "\nFinal interactive map saved at:"
)

print(
    output_file
)
