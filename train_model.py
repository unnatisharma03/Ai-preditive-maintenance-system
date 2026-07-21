import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib


# Load Dataset
data = pd.read_csv("dataset/machine_data.csv")


# Features
X = data[[
    "Temperature",
    "Vibration",
    "Pressure",
    "Runtime"
]]


# Target
y = data["Status"]


# Model Training
model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)


model.fit(X, y)


# Save Model
joblib.dump(model, "model.pkl")


print("Model trained successfully")
print("Classes:", model.classes_)