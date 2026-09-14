import pandas as pd
import numpy as np

from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor

from sklearn.metrics import(mean_absolute_error, mean_squared_error, r2_score)

#file path

script_folder = Path(__file__).resolve().parent
project_folder = script_folder.parent

csv_file = (project_folder/"src"/"bengaluru_urban_heat_clean.csv")

#load dataset

df = pd.read_csv(csv_file)
print("Dataset loaded successfully")
print("\n Dataset shape:")
print(df.shape)

#input features x

features = ["L_NDVI", "NDBI", "NDWI", "S2_NDVI", "Air_Temp", "Wind_Speed", "Relative_Humidity"]

X = df[features]
#Target Y
y = df["LST"]

print("\n Input features:")
print(X.columns.tolist())
print("\n Target:")
print("LST")

#train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.2, random_state = 42)
print("\n Training samples:")
print(len(X_train))

print("\n Testing samples:")
print(len(X_test))

#model 1 linear regression

linear_model= LinearRegression()
linear_model.fit(X_train, y_train)
linear_predictions = linear_model.predict(X_test)
linear_mae = mean_absolute_error(y_test, linear_predictions)
linear_rmse = np.sqrt(mean_squared_error(y_test, linear_predictions))
linear_r2 = r2_score(y_test, linear_predictions)

print("\n -------")
print("LINEAR REGRESSION")
print("--------------")
print("MAE:", linear_mae)
print("RMSE: ", linear_rmse)
print("R2:", linear_r2)

#model 2 - random forest

rf_model = RandomForestRegressor(n_estimators = 100, random_state = 42)
rf_model.fit(X_train, y_train)
rf_predictions = rf_model.predict(X_test)
rf_mae = mean_absolute_error(y_test, rf_predictions)

rf_rmse = np.sqrt(mean_squared_error(y_test, rf_predictions))

rf_r2 = r2_score(y_test, rf_predictions)

print("\n---------------")
print("RANDOM FOREST")
print("----------------")

print("MAE:", rf_mae)
print("RMSE:", rf_rmse)
print("R2:", rf_r2)

#feature importance

importance = pd.DataFrame({"Feature":features, "Importance":rf_model.feature_importances_})

importance = importance.sort_values("Importance", ascending=False)

print("\n Random Forest Feature Importance:")

print(importance)






