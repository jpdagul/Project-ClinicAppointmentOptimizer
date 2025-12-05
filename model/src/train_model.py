import joblib
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import (
    classification_report,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    precision_recall_curve,
    roc_curve,
    auc,
    confusion_matrix
)
from sklearn.model_selection import cross_val_score
from imblearn.over_sampling import SMOTE
from xgboost import XGBClassifier
from src.data_preprocessing import load_and_clean_data


def train_and_select_model():
    # load and normalize data
    X_train, X_test, y_train, y_test = load_and_clean_data("data/noshowappointments.csv")

    print("\nNormalizing data...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # handle class imbalance with SMOTE (show 88k vs no-show 22k)
    print("\nApplying SMOTE to balance classes...")
    smote = SMOTE(random_state=42)
    X_train_bal, y_train_bal = smote.fit_resample(X_train_scaled, y_train)
    print(f"After SMOTE: {y_train_bal.value_counts().to_dict()}")

    # define models (add class weights)
    models = {
        "Decision Tree": DecisionTreeClassifier(class_weight='balanced', random_state=42),
        "Random Forest": RandomForestClassifier(class_weight='balanced', n_estimators=100, random_state=42),
        "Gradient Boosting": GradientBoostingClassifier(random_state=42, subsample=0.9),
        "XGBoost": XGBClassifier(
            random_state=42,
            n_estimators=200,
            learning_rate=0.1,
            eval_metric='logloss',
            scale_pos_weight=len(y_train_bal[y_train_bal == 0]) / len(y_train_bal[y_train_bal == 1])
        )
    }

    best_model, best_score, best_name = None, 0.0, ""

    # train, cross-validate, and evaluate models
    for name, model in models.items():
        print(f"\nTraining {name}...")
        model.fit(X_train_bal, y_train_bal)
        y_pred = model.predict(X_test_scaled)

        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred)
        rec = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        cv_scores = cross_val_score(model, X_train_bal, y_train_bal, cv=5, scoring='f1')

        print(f"{name} | Accuracy: {acc:.4f} | Precision: {prec:.4f} | Recall: {rec:.4f} | "
              f"F1: {f1:.4f} | CV F1 avg: {cv_scores.mean():.4f}")
        print(classification_report(y_test, y_pred))

        if f1 > best_score:
            best_score, best_model, best_name = f1, model, name

    # tune threshold based on F1 optimization
    # --> improves recall (catching more no-shows) at the cost of some false positives
    print("\nTuning decision threshold for best model...")
    y_proba = best_model.predict_proba(X_test_scaled)[:, 1]
    precisions, recalls, thresholds = precision_recall_curve(y_test, y_proba)
    f1_scores = 2 * (precisions * recalls) / (precisions + recalls + 1e-9)
    best_threshold = thresholds[np.argmax(f1_scores)]
    y_pred_thresh = (y_proba > best_threshold).astype(int)

    print(f"Selected threshold: {best_threshold:.2f}")
    print(f"Precision: {precision_score(y_test, y_pred_thresh):.4f} | "
          f"Recall: {recall_score(y_test, y_pred_thresh):.4f} | "
          f"F1: {f1_score(y_test, y_pred_thresh):.4f}")

    # plot precision–recall curve
    plt.figure(figsize=(8, 6))
    plt.plot(recalls, precisions, color='royalblue', linewidth=2, label="PR Curve")
    plt.scatter(recall_score(y_test, y_pred_thresh), precision_score(y_test, y_pred_thresh),
                color='red', label=f"Threshold={best_threshold:.2f}")
    plt.title(f"Precision–Recall Curve ({best_name})")
    plt.xlabel("Recall (Catch No-Shows)")
    plt.ylabel("Precision (Correct Predictions)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("models/precision_recall_curve.png")
    plt.close()
    print("Precision–Recall curve saved.")

    # plot ROC Curve
    fpr, tpr, _ = roc_curve(y_test, y_proba)
    roc_auc = auc(fpr, tpr)
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, label=f"ROC Curve (AUC = {roc_auc:.2f})", color='green')
    plt.plot([0, 1], [0, 1], "k--", linewidth=1)
    plt.title(f"ROC Curve ({best_name})")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("models/roc_curve.png")
    plt.close()
    print("ROC curve saved.")

    # confusion matrix visualization
    cm = confusion_matrix(y_test, y_pred_thresh)
    fig, ax = plt.subplots(figsize=(6, 5))
    cax = ax.matshow(cm, cmap='Blues')
    plt.title(f"Confusion Matrix ({best_name})", pad=20)
    plt.xlabel("Predicted Labels")
    plt.ylabel("Actual Labels")
    plt.colorbar(cax)
    for (i, j), val in np.ndenumerate(cm):
        ax.text(j, i, f'{val}', ha='center', va='center', color='black')
    plt.tight_layout()
    plt.savefig("models/confusion_matrix.png")
    plt.close()
    print("Confusion matrix saved.")

    # Step 9: Feature Importance Visualization
    if hasattr(best_model, "feature_importances_"):
        importances = best_model.feature_importances_
        indices = np.argsort(importances)[-10:]
        top_features = np.array(X_train.columns)[indices]
        top_importances = importances[indices]

        plt.figure(figsize=(8, 5))
        plt.barh(top_features, top_importances, color='teal')
        plt.title(f"Top 10 Important Features ({best_name})")
        plt.xlabel("Feature Importance")
        plt.ylabel("Feature Name")
        plt.tight_layout()
        plt.savefig("models/feature_importance.png")
        plt.close()
        print("Feature importance chart saved.")
    else:
        print("Feature importance not available for this model.")

    # save best model
    model_path = f"models/{best_name.lower().replace(' ', '_')}_model.pkl"
    joblib.dump(best_model, model_path)
    print(f"\nBest model: {best_name} | Saved to: {model_path}")

    return model_path
