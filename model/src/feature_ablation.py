import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import f1_score
from sklearn.preprocessing import StandardScaler
from src.data_preprocessing import load_and_clean_data

REFERENCE_THRESHOLD = 0.40


def run_feature_ablation():
    X_train, X_test, y_train, y_test = load_and_clean_data(
        "data/noshowappointments.csv"
    )

    feature_names = X_train.columns

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = joblib.load("models/gradient_boosting_model.pkl")

    baseline_proba = model.predict_proba(X_test_scaled)[:, 1]
    baseline_pred = (baseline_proba > REFERENCE_THRESHOLD).astype(int)
    baseline_f1 = f1_score(y_test, baseline_pred)

    print(f"Baseline F1 (reference): {baseline_f1:.4f}\n")

    results = []

    for i, feature in enumerate(feature_names):
        X_test_drop = np.delete(X_test_scaled, i, axis=1)

        y_proba = model.predict_proba(X_test_drop)[:, 1]
        y_pred = (y_proba > REFERENCE_THRESHOLD).astype(int)
        f1 = f1_score(y_test, y_pred)

        results.append({
            "feature": feature,
            "f1_drop": baseline_f1 - f1
        })

        print(f"Remove {feature:<25} → F1 drop = {baseline_f1 - f1:.4f}")

    df = pd.DataFrame(results).sort_values("f1_drop", ascending=False)
    df.to_csv("models/feature_ablation.csv", index=False)

    print("\nFeature ablation results saved to models/feature_ablation.csv")


if __name__ == "__main__":
    run_feature_ablation()
