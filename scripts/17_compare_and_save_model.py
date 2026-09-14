import pandas as pd
import numpy as np
import joblib

from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor

from sklearn.metrics import(mean_absolute_error, mean_squared_error, r2_score)

#paths

script_folder = Path(__file__).resolve().parent
project_folder = script_folder.parent

csv_file = (project_folder/"src"/"bengaluru_urban_heat_clean.csv")

model_folder = project_folder/"models"
model_folder.mkdir(exist_ok = True)

#LOAD DATA

df = pd.read_csv(csv_file)
features = ["L_NDVI", "NDBI", "NDWI", "S2_NDVI", "Air_Temp", "Wind_Speed", "Relative_Humidity"]

X = df[features]
y = df["LST"]

#train test_split
X_train,X_test, y_train, y_test = train_test_split(X, y, test_size = 0.20, random_state =42)

#linear regression
linear_model = LinearRegression()

linear_model.fit(X_train, y_train )

linear_predictions = linear_model.predict(X_test)

linear_mae = mean_absolute_error(y_test, linear_predictions)
linear_rmse = np.sqrt(mean_squared_error(y_test, linear_predictions))
linear_r2 = r2_score(y_test, linear_predictions)

#random forest
rf_model = RandomForestRegressor(n_estimators = 100, random_state = 42)

rf_model.fit(X_train, y_train)

rf_predictions = rf_model.predict(X_test)

rf_mae = mean_absolute_error(y_test, rf_predictions)

rf_rmse = np.sqrt(mean_squared_error(y_test, rf_predictions))

rf_r2 = r2_score(y_test, rf_predictions)

#compare models
results = pd.DataFrame({
    "Model":[
        "Linear Regression", "Random Forest"
    ],
    "MAE": [linear_mae, rf_mae],
    "RMSE": [linear_rmse, rf_rmse],
    "R2": [linear_r2, rf_r2]
})
print("\n Model Comparison:")
print(results)

#select best model

if rf_rmse < linear_rmse:
    best_model = rf_model
    best_model_name = "Random Forest"
else:
    best_model = linear_model
    best_model_name = "Linear Regression"
print("\n Best Model:")
print(best_model_name)

#save best model
model_file = (model_folder/"urban_heat_model.pkl")

joblib.dump(best_model, model_file)
print("\n Model saved at:")
print(model_file)
#save feature names

feature_file = (model_folder/"features.pkl")

feature_file = (model_folder/"features.pkl")

joblib.dump(features, feature_file)

print("Feature list saved.")
#random forest feature importance
importance = pd.DataFrame({"Feature": features, "Importance": rf_model.feature_importances_ })
importance = importance.sort_values("Importance", ascending=False)

print("\n Random Forest Feature Importances:")
print(importance)
importance.to_csv(model_folder/"feature_importance.csv", index=False)
