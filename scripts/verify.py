import pandas as pd

df = pd.read_csv(
    "src/bengaluru_multidate_ml_dataset.csv"
)

print("Total rows:")
print(len(df))

print("\nUnique Landsat dates:")
print(df["date"].nunique())

print("\nSamples by year:")
print(
    df["year"]
    .value_counts()
    .sort_index()
)

print("\nSamples per date:")
print(
    df["date"]
    .value_counts()
    .sort_index()
)
print("Total rows:", len(df))

print("\nUnique Landsat dates:")
print(df["date"].nunique())

print("\nSamples by year:")
print(
    df["year"]
    .value_counts()
    .sort_index()
)

print("\nUnique dates by year:")
print(
    df.groupby("year")["date"]
    .nunique()
)