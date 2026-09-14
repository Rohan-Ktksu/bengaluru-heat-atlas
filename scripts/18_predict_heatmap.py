import pandas as pd
import joblib
import folium
import json
from pathlib import Path
from folium.plugins import HeatMap

#paths
script_folder = Path(__file__).resolve().parent
project_folder = script_folder.parent

csv_file = (project_folder/"src"/"bengaluru_urban_heat_ml_dataset.csv")

model_file = (project_folder/"models"/"urban_heat_model.pkl")

feature_file = (project_folder/"models"/"features.pkl")


#load data
df = pd.read_csv(csv_file)
print("Dataset Loaded")
print("\nColumns in CSV:")
print(df.columns.tolist())
model = joblib.load(model_file)

features = joblib.load(feature_file)
print("Model Loaded")
print("Features used:")
print(features)

#EXTRACT LATITUDE / LONGITUDE FROM .geo

def extract_longitude(geo_text):

    geo = json.loads(geo_text)

    return geo["coordinates"][0]


def extract_latitude(geo_text):

    geo = json.loads(geo_text)

    return geo["coordinates"][1]


df["longitude"] = df[".geo"].apply(
    extract_longitude
)

df["latitude"] = df[".geo"].apply(
    extract_latitude
)

print("\nCoordinates extracted successfully.")

print(
    df[
        [
            "latitude",
            "longitude"
        ]
    ].head()
)

#keep required columns

required_columns = features + ["latitude", "longitude"]

df = df[required_columns].copy()

#Remove missing rows
df = df.dropna()

print("Rows available for prediction:")
print(len(df))

#prepare X
X = df[features]
#prepare lst
df["Predicted_LST"]= model.predict(X)
print("\n First predictions:")
print(df[["latitude", "longitude", "Predicted_LST"]].head())
#create folium map
m = folium.Map(location = [12.97, 77.59], zoom_start=10)
#prepare heatmap data

heat_data = []
for _, row in df.iterrows():
    heat_data.append([row["latitude"], row["longitude"], row["Predicted_LST"]])
#add heatmap
HeatMap(heat_data, radius=10, blur =15, min_opacity=0.4).add_to(m)

#save map
output_file = (project_folder/"src"/"bengaluru_predicted_heatmap.html")

m.save(output_file)

print("\n Prediction heat map created successfully")
print("Saved at:")
print(output_file)
