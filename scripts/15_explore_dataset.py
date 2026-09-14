import pandas as pd
from pathlib import Path

#Locaiton of this Python script
script_folder = Path(__file__).resolve().parent

#isro project folder
project_folder = script_folder.parent
#csv inside src folder
csv_file = (project_folder/"src"/"bengaluru_urban_heat_ml_dataset.csv")
print("Reading dataset from:")
print(csv_file)

#load dataset
df = pd.read_csv(csv_file)

print("\nDataset loaded successfully")

#first 5 rows
print("\n First 5 rows:")
print(df.head())

#dataset shape
print("\n Dataset shape:")
print(df.columns.shape)

#dataset columns:
print("\nColumn names:")
print(df.columns.tolist())

#dataset info
print("\n Dataset Information")
df.info()

#missing values
print("\n Missing values:")
print(df.isnull().sum())

#statistical summary

print("\n Statistical summary:")

print(df.describe())

#selected ml columns

ml_columns = [
    "L_NDVI",
    "NDBI",
    "NDWI",
    "S2_NDVI",
    "Air_Temp",
    "Wind_Speed",
    "Relative_Humidity",
    "LST"
]

df_ml = df[ml_columns].copy()

#remove missing values
df_ml = df_ml.dropna()

print("\n Cleaned dataset shape:")
print(df_ml.shape)

#correlation with lst

correlation = (
    df_ml.corr(numeric_only=True)["LST"]
    .sort_values(ascending=False)
)

print("\nCorrelation with LST:")
print(correlation)

#save cleaned dataset in src
clean_file = (project_folder/"src"/"bengaluru_urban_heat_clean.csv")
df_ml.to_csv(clean_file, index =False)

print("\n Cleaned dadtaset saved successfully.")
print("Saved at: ")
print(clean_file)



