import joblib
import lime
import lime.lime_tabular


def explain_prediction(
    model_path,
    X_train,
    X_instance,
    feature_names,
    class_names=("Show", "No-Show"),
    num_features=10
):
    model = joblib.load(model_path)

    explainer = lime.lime_tabular.LimeTabularExplainer(
        training_data=X_train,
        feature_names=feature_names,
        class_names=class_names,
        mode="classification",
        discretize_continuous=True
    )

    explanation = explainer.explain_instance(
        data_row=X_instance,
        predict_fn=model.predict_proba,
        num_features=num_features
    )

    return explanation
