import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold, train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from imblearn.over_sampling import SMOTE
import joblib
import os

df = pd.read_csv("app/ml/data/profile_features.csv")

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
print("MODEL 2: Random Forest + SMOTE (PRODUCTION MODEL)")
print("=" * 60)
print(f"Original class distribution: {dict(y.value_counts())}")

smote = SMOTE(random_state=42, k_neighbors=5)
X_resampled, y_resampled = smote.fit_resample(X, y)
print(f"After SMOTE: {dict(pd.Series(y_resampled).value_counts())}")

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
rf_smote_model = RandomForestClassifier(
    n_estimators=100, max_depth=4, min_samples_leaf=3, random_state=42
)
rf_smote_cv_scores = cross_val_score(rf_smote_model, X_resampled, y_resampled, cv=cv, scoring="f1")
print(f"Cross-validation F1 scores: {np.round(rf_smote_cv_scores, 3)}")
print(f"Mean F1: {rf_smote_cv_scores.mean():.3f} (+/- {rf_smote_cv_scores.std():.3f})")

rf_smote_model.fit(X_resampled, y_resampled)

print("\nFeature Importance (production model):")
importance = pd.Series(rf_smote_model.feature_importances_, index=feature_cols).sort_values(ascending=False)
print(importance)

print("\n" + "=" * 60)
print("MODEL 3: Gradient Boosting (comparison)")
print("=" * 60)
gb_model = GradientBoostingClassifier(n_estimators=100, max_depth=3, learning_rate=0.1, random_state=42)
gb_cv_scores = cross_val_score(gb_model, X, y, cv=cv, scoring="f1")
print(f"Mean F1: {gb_cv_scores.mean():.3f} (+/- {gb_cv_scores.std():.3f})")
gb_model.fit(X, y)

print("\n" + "=" * 60)
print("SUMMARY: Impact of adding stream_spike_score")
print("=" * 60)
print(f"Previous best (4 features, RF+SMOTE): 0.990")
print(f"New (5 features, RF+SMOTE):           {rf_smote_cv_scores.mean():.3f}")

os.makedirs("app/ml/models", exist_ok=True)
joblib.dump(rf_smote_model, "app/ml/models/random_forest_model.pkl")
joblib.dump(gb_model, "app/ml/models/gradient_boosting_model.pkl")
joblib.dump(iso_forest, "app/ml/models/isolation_forest_model.pkl")
print("\nAll models saved. Production model now includes stream_spike_score.")
