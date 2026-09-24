import os
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import classification_report
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
import joblib

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "profile_features.csv"
MODELS_DIR = BASE_DIR / "models"

if not DATA_PATH.exists():
    raise FileNotFoundError(f"Feature dataset not found at {DATA_PATH}. Run feature engineering first.")

df = pd.read_csv(DATA_PATH)

feature_cols = ["name_similarity_score", "catalog_velocity_score", "growth_velocity_score", "metadata_completeness_score", "stream_spike_score"]
X = df[feature_cols]
y = df["is_verified_owner"].apply(lambda x: 0 if x else 1)

print("=" * 60)
print("MODEL 1: Isolation Forest (Anomaly Detection - Unsupervised)")
print("=" * 60)

iso_forest = IsolationForest(contamination=0.2, random_state=42)
iso_forest.fit(X)
iso_predictions = iso_forest.predict(X)
iso_predictions_binary = [1 if p == -1 else 0 for p in iso_predictions]
print(classification_report(y, iso_predictions_binary, target_names=["Legitimate", "Fraudulent"]))

print("\n" + "=" * 60)
print("MODEL 2: Random Forest + SMOTE Pipeline (LEAK-FREE CROSS-VALIDATION)")
print("=" * 60)
print(f"Class distribution: {dict(y.value_counts())}")

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

# ImbPipeline ensures SMOTE is fitted ONLY on training folds during cross-validation (no data leakage)
rf_pipeline = ImbPipeline([
    ("smote", SMOTE(random_state=42, k_neighbors=5)),
    ("rf", RandomForestClassifier(n_estimators=100, max_depth=4, min_samples_leaf=3, random_state=42))
])

rf_smote_cv_scores = cross_val_score(rf_pipeline, X, y, cv=cv, scoring="f1")
print(f"Leak-Free Cross-validation F1 scores: {np.round(rf_smote_cv_scores, 3)}")
print(f"Mean F1 (Leak-Free): {rf_smote_cv_scores.mean():.3f} (+/- {rf_smote_cv_scores.std():.3f})")

# Fit final production model on full dataset
smote_full = SMOTE(random_state=42, k_neighbors=5)
X_resampled, y_resampled = smote_full.fit_resample(X, y)
rf_production_model = RandomForestClassifier(n_estimators=100, max_depth=4, min_samples_leaf=3, random_state=42)
rf_production_model.fit(X_resampled, y_resampled)

print("\nFeature Importance (production model):")
importance = pd.Series(rf_production_model.feature_importances_, index=feature_cols).sort_values(ascending=False)
print(importance)

print("\n" + "=" * 60)
print("MODEL 3: Gradient Boosting (comparison)")
print("=" * 60)
gb_model = GradientBoostingClassifier(n_estimators=100, max_depth=3, learning_rate=0.1, random_state=42)
gb_cv_scores = cross_val_score(gb_model, X, y, cv=cv, scoring="f1")
print(f"Mean F1: {gb_cv_scores.mean():.3f} (+/- {gb_cv_scores.std():.3f})")
gb_model.fit(X, y)

os.makedirs(MODELS_DIR, exist_ok=True)
joblib.dump(rf_production_model, MODELS_DIR / "random_forest_model.pkl")
joblib.dump(gb_model, MODELS_DIR / "gradient_boosting_model.pkl")
joblib.dump(iso_forest, MODELS_DIR / "isolation_forest_model.pkl")
print(f"\nAll models saved to {MODELS_DIR}. Leak-free evaluation complete.")
