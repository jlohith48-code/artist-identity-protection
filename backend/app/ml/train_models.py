import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold, train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import os

df = pd.read_csv("app/ml/data/profile_features.csv")

feature_cols = ["name_similarity_score", "catalog_velocity_score", "growth_velocity_score", "metadata_completeness_score"]
X = df[feature_cols]
y = df["is_verified_owner"].apply(lambda x: 0 if x else 1)

print("=" * 60)
print("MODEL 1: Isolation Forest (Anomaly Detection - Unsupervised)")
print("=" * 60)
print("This model does NOT see the labels during training.")
print("It only learns what 'normal' looks like, then flags outliers.\n")

iso_forest = IsolationForest(contamination=0.2, random_state=42)
iso_forest.fit(X)
iso_predictions = iso_forest.predict(X)
iso_predictions_binary = [1 if p == -1 else 0 for p in iso_predictions]

print(classification_report(y, iso_predictions_binary, target_names=["Legitimate", "Fraudulent"]))
print("Confusion Matrix (rows=actual, cols=predicted):")
print(confusion_matrix(y, iso_predictions_binary))

print("\n" + "=" * 60)
print("MODEL 2: Random Forest (Classification - Supervised)")
print("=" * 60)

rf_model = RandomForestClassifier(
    n_estimators=100,
    max_depth=4,
    min_samples_leaf=3,
    random_state=42,
    class_weight="balanced"
)

print("Running 5-fold cross-validation (more reliable than one train/test split)...\n")
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = cross_val_score(rf_model, X, y, cv=cv, scoring="f1")
print(f"Cross-validation F1 scores across 5 folds: {np.round(cv_scores, 3)}")
print(f"Mean F1: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})\n")

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
rf_model.fit(X_train, y_train)
rf_predictions = rf_model.predict(X_test)

print("Single test-split results (for reference only, cross-validation above is more reliable):")
print(classification_report(y_test, rf_predictions, target_names=["Legitimate", "Fraudulent"]))
print("Confusion Matrix (rows=actual, cols=predicted):")
print(confusion_matrix(y_test, rf_predictions))

print("\nFeature Importance (which signals mattered most):")
importance = pd.Series(rf_model.feature_importances_, index=feature_cols).sort_values(ascending=False)
print(importance)

os.makedirs("app/ml/models", exist_ok=True)
joblib.dump(rf_model, "app/ml/models/random_forest_model.pkl")
joblib.dump(iso_forest, "app/ml/models/isolation_forest_model.pkl")
print("\nModels saved to app/ml/models/")
