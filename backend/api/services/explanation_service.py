"""
Service for generating LIME explanations for individual no-show predictions.
"""

import sys

import lime.lime_tabular
import pandas as pd

from .prediction_service import get_prediction_service, MODEL_DIR

sys.path.insert(0, str(MODEL_DIR))
from src.data_preprocessing import load_and_clean_data


CLASS_NAMES = ("Show", "No-Show")
DEFAULT_NUM_FEATURES = 10


class ExplanationService:
    """Per-patient LIME explainer, lazily initialized and cached."""

    def __init__(self):
        self.explainer = None
        self._explainer_loaded = False
        self.predictor = get_prediction_service()

    def _ensure_predictor_loaded(self):
        if not self.predictor._model_loaded:
            self.predictor._load_model()
            self.predictor._prepare_scaler()
            self.predictor._model_loaded = True

        if self.predictor.scaler is None or self.predictor.feature_columns is None:
            raise RuntimeError(
                "PredictionService failed to initialize the scaler or feature "
                "columns. Check that the training data exists at "
                f"{MODEL_DIR / 'data' / 'noshowappointments.csv'}."
            )

    def _build_explainer(self):
        self._ensure_predictor_loaded()

        data_path = MODEL_DIR / 'data' / 'noshowappointments.csv'
        if not data_path.exists():
            raise FileNotFoundError(
                f"Training data not found at {data_path}."
            )

        X_train, _, _, _ = load_and_clean_data(str(data_path))
        X_train = X_train[self.predictor.feature_columns]
        X_train_scaled = self.predictor.scaler.transform(X_train)

        self.explainer = lime.lime_tabular.LimeTabularExplainer(
            training_data=X_train_scaled,
            feature_names=self.predictor.feature_columns,
            class_names=list(CLASS_NAMES),
            mode="classification",
            discretize_continuous=True,
        )

    def get_explanation(self, full_patient_df, appointment_id,
                        num_features=DEFAULT_NUM_FEATURES):
        """Generate a LIME explanation for one appointment in the uploaded cohort."""
        if not isinstance(full_patient_df, pd.DataFrame):
            raise TypeError("full_patient_df must be a pandas DataFrame")
        if 'AppointmentID' not in full_patient_df.columns:
            raise ValueError("full_patient_df must contain an AppointmentID column")

        df = full_patient_df.reset_index(drop=True)
        target_positions = df.index[df['AppointmentID'] == appointment_id].tolist()
        if not target_positions:
            raise ValueError(
                f"AppointmentID {appointment_id} not found in uploaded cohort."
            )
        target_idx = target_positions[0]

        if not self._explainer_loaded:
            self._build_explainer()
            self._explainer_loaded = True

        processed = self.predictor._preprocess_patient_data(df)
        aligned = self.predictor._align_features(processed)

        if target_idx not in aligned.index:
            raise ValueError(
                f"AppointmentID {appointment_id} was filtered out during "
                "preprocessing (likely an invalid Age value)."
            )

        scaled_all = self.predictor.scaler.transform(aligned)
        target_pos_in_aligned = list(aligned.index).index(target_idx)
        target_scaled = scaled_all[target_pos_in_aligned]

        proba = float(
            self.predictor.model.predict_proba(target_scaled.reshape(1, -1))[0, 1]
        )

        explanation = self.explainer.explain_instance(
            data_row=target_scaled,
            predict_fn=self.predictor.model.predict_proba,
            num_features=num_features,
        )

        top_features = [
            {
                "feature": feature_str,
                "weight": float(weight),
                "direction": "noshow" if weight > 0 else "show",
            }
            for feature_str, weight in explanation.as_list()
        ]

        return {
            "noShowProbability": proba,
            "topFeatures": top_features,
        }


_explanation_service = None


def get_explanation_service():
    global _explanation_service
    if _explanation_service is None:
        _explanation_service = ExplanationService()
    return _explanation_service
