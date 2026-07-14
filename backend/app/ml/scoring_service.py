import joblib
import os
from app.utils.feature_calc import compute_profile_features

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "ml", "models", "random_forest_model.pkl")
_model = None

def get_model():
    global _model
    if _model is None:
        _model = joblib.load(MODEL_PATH)
    return _model

def score_profile(artist_full_name, profile):
    features = compute_profile_features(artist_full_name, profile)
    model = get_model()

    feature_order = ["name_similarity_score", "catalog_velocity_score", "growth_velocity_score", "metadata_completeness_score"]
    feature_vector = [[features[col] for col in feature_order]]

    fraud_probability = model.predict_proba(feature_vector)[0][1]

    if fraud_probability >= 0.7:
        risk_label = "high_risk"
    elif fraud_probability >= 0.4:
        risk_label = "medium_risk"
    else:
        risk_label = "low_risk"

    return {
        "name_similarity_score": features["name_similarity_score"],
        "account_age_score": features["catalog_velocity_score"],
        "growth_velocity_score": features["growth_velocity_score"],
        "metadata_completeness_score": features["metadata_completeness_score"],
        "overall_risk_score": round(float(fraud_probability), 3),
        "risk_label": risk_label,
    }
