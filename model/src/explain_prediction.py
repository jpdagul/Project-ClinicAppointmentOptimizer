from src.data_preprocessing import load_and_clean_data
from src.lime_explanations import explain_prediction
from sklearn.preprocessing import StandardScaler


def main():
    X_train, X_test, y_train, y_test = load_and_clean_data(
        "data/noshowappointments.csv"
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # ONE patient to explain
    patient_index = 0

    exp = explain_prediction(
        model_path="models/decision_tree_model.pkl",
        X_train=X_train_scaled,
        X_instance=X_test_scaled[patient_index],
        feature_names=X_train.columns.tolist()
    )

    output_path = "models/lime_explanation_patient_0.html"
    exp.save_to_file(output_path)

    print(f"LIME explanation saved to: {output_path}")


if __name__ == "__main__":
    main()
