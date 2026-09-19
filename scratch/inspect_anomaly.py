import os
import joblib

model_path = os.path.join('backend', 'anomaly_model.pkl')

if os.path.exists(model_path):
    model = joblib.load(model_path)
    print("Loaded anomaly_model.pkl successfully.")
    print("n_features_in_:", getattr(model, 'n_features_in_', None))
    print("feature_names_in_:", getattr(model, 'feature_names_in_', None))
else:
    print("anomaly_model.pkl not found at", model_path)
