import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from src.data_preprocessing import load_and_clean_data


def evaluate_saved_model(model_path):
    X_train, X_test, y_train, y_test = load_and_clean_data("data/noshowappointments.csv")
    model = joblib.load(model_path)

    y_pred = model.predict(X_test)

    metrics = {
        "Accuracy": accuracy_score(y_test, y_pred),
        "Precision": precision_score(y_test, y_pred),
        "Recall": recall_score(y_test, y_pred),
        "F1 Score": f1_score(y_test, y_pred)
    }

    results = pd.DataFrame([metrics])
    print("\nFinal Evaluation Metrics:\n", results)
    return results