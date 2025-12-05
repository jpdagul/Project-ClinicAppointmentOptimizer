import joblib
import numpy as np
import matplotlib.pyplot as plt
import sys
import os


def inspect_model(model_path: str):
    """Load a .pkl model and print useful information."""
    if not os.path.exists(model_path):
        print(f"File not found: {model_path}")
        return

    print(f"Loading model from: {model_path}")
    model = joblib.load(model_path)

    print("\nModel Type:")
    print(type(model))

    print("\nModel Parameters:")
    try:
        params = model.get_params()
        for key, val in params.items():
            print(f"  {key}: {val}")
    except Exception:
        print("  (No readable parameters available)")

    # Feature importance check
    if hasattr(model, "feature_importances_"):
        print("\nTop Feature Importances:")
        importances = model.feature_importances_
        if len(importances) > 0:
            indices = np.argsort(importances)[-10:]  # top 10
            top_features = indices[::-1]
            print("  (Showing top 10)")
            for i in top_features:
                print(f"    Feature {i}: Importance {importances[i]:.4f}")

            # Plot
            plt.figure(figsize=(8, 5))
            plt.barh(range(len(top_features)), importances[top_features][::-1], color='teal')
            plt.yticks(range(len(top_features)), [f"Feature {i}" for i in top_features[::-1]])
            plt.title("Top 10 Feature Importances")
            plt.xlabel("Importance Score")
            plt.tight_layout()
            plt.savefig("models/inspect_feature_importance.png")
            plt.show()
        else:
            print("  (No feature importance values found)")
    else:
        print("\nThis model does not provide feature importances.")

    print("\nModel inspection complete.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python inspect_model.py <path_to_model.pkl>")
    else:
        model_path = sys.argv[1]
        inspect_model(model_path)
