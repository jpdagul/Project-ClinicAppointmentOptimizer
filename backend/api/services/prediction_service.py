"""
Service for making predictions using the trained ML model.
"""
import os
import sys
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import StandardScaler

# Add model directory to path
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
MODEL_DIR = BASE_DIR / 'model'
sys.path.insert(0, str(MODEL_DIR))

from src.data_preprocessing import load_and_clean_data


class PredictionService:
    """Service for making no-show predictions."""
    
    def __init__(self):
        """Initialize the prediction service with the trained model."""
        self.model_path = MODEL_DIR / 'models' / 'gradient_boosting_model.pkl'
        self.model = None
        self.scaler = None
        self.feature_columns = None
        self._model_loaded = False
        # Don't load model on init - load lazily when needed
    
    def _load_model(self):
        """Load the trained model."""
        if not self.model_path.exists():
            # Try alternative model name
            alt_path = MODEL_DIR / 'models' / 'gradient_boosting.pkl'
            if alt_path.exists():
                self.model_path = alt_path
            else:
                raise FileNotFoundError(
                    f"Model not found at {self.model_path} or {alt_path}. "
                    f"Please train the model first using 'python model/main.py'"
                )
        
        try:
            self.model = joblib.load(self.model_path)
            print(f"Model loaded from {self.model_path}")
        except (AttributeError, ModuleNotFoundError, ValueError) as e:
            error_msg = str(e)
            if 'CyHalfBinomialLoss' in error_msg or '__pyx_unpickle' in error_msg:
                raise RuntimeError(
                    "Model version mismatch: The model was trained with a different version of scikit-learn. "
                    "Please retrain the model with the current scikit-learn version by running: "
                    "cd model && python main.py"
                ) from e
            else:
                raise RuntimeError(
                    f"Error loading model: {error_msg}. "
                    "The model file may be corrupted or incompatible with the current scikit-learn version. "
                    "Please retrain the model by running: cd model && python main.py"
                ) from e
    
    def _prepare_scaler(self):
        """Prepare the scaler by loading training data."""
        try:
            # Load training data to fit scaler
            data_path = MODEL_DIR / 'data' / 'noshowappointments.csv'
            if not data_path.exists():
                print("Warning: Training data not found. Using default scaling.")
                return
            
            X_train, _, _, _ = load_and_clean_data(str(data_path))
            self.scaler = StandardScaler()
            self.scaler.fit(X_train)
            self.feature_columns = X_train.columns.tolist()
            print(f"Scaler prepared with {len(self.feature_columns)} features")
        except Exception as e:
            print(f"Warning: Could not prepare scaler: {e}")
    
    def _preprocess_patient_data(self, patient_data):
        """
        Preprocess patient data to match model input format.
        This must exactly match the preprocessing in model/src/data_preprocessing.py
        
        Args:
            patient_data: DataFrame with patient appointment data
            
        Returns:
            Preprocessed DataFrame ready for prediction
        """
        df = patient_data.copy()
        
        # Convert date columns (must match model preprocessing)
        df['ScheduledDay'] = pd.to_datetime(df['ScheduledDay'], errors='coerce')
        df['AppointmentDay'] = pd.to_datetime(df['AppointmentDay'], errors='coerce')
        df = df[df['Age'] >= 0]
        
        # Feature engineering: time and scheduling (must match model preprocessing exactly)
        df['Days_Wait'] = (df['AppointmentDay'] - df['ScheduledDay']).dt.days
        df['Appointment_DayOfWeek'] = df['AppointmentDay'].dt.weekday
        df['Appointment_Month'] = df['AppointmentDay'].dt.month
        df['Scheduled_Hour'] = df['ScheduledDay'].dt.hour
        
        # Sort by patient and time for behavioral features
        df = df.sort_values(by=['PatientId', 'ScheduledDay'])
        
        # Behavioral features (must match model preprocessing)
        # Handle No-show column - convert to numeric if it exists
        if 'No-show' in df.columns:
            df['No-show'] = df['No-show'].map({'Yes': 1, 'No': 0})
        else:
            # If No-show column doesn't exist, create it with zeros (for prediction)
            df['No-show'] = 0
        
        # Past no-show rate
        df['Past_NoShow_Rate'] = (
            df.groupby('PatientId')['No-show']
            .transform(lambda x: x.shift().expanding().mean())
            .fillna(0)
        )
        
        # Total appointments per patient
        df['Total_Appointments'] = df.groupby('PatientId')['AppointmentID'].transform('count')
        
        # Missed before
        df['Missed_Before'] = (df['Past_NoShow_Rate'] > 0).astype(int)
        
        # Days since last appointment
        df['Prev_Appointment_Day'] = df.groupby('PatientId')['AppointmentDay'].shift()
        df['Days_Since_Last_Appt'] = (
            (df['AppointmentDay'] - df['Prev_Appointment_Day']).dt.days.fillna(0)
        )
        
        # Appointment frequency
        patient_min = df.groupby('PatientId')['AppointmentDay'].transform('min')
        patient_max = df.groupby('PatientId')['AppointmentDay'].transform('max')
        df['Patient_Active_Days'] = (patient_max - patient_min).dt.days + 1
        df['Appointment_Frequency'] = df['Total_Appointments'] / df['Patient_Active_Days'].replace(0, 1)
        
        # Drop helper columns
        df.drop(columns=['Prev_Appointment_Day', 'Patient_Active_Days'], inplace=True, errors='ignore')
        
        # Categorical encoding (must match model preprocessing)
        df = pd.get_dummies(df, columns=['Gender', 'Neighbourhood'], drop_first=True)
        
        # Drop ID/date columns and target
        df.drop(columns=['PatientId', 'AppointmentID', 'ScheduledDay', 'AppointmentDay', 'No-show'], 
                inplace=True, errors='ignore')
        
        return df
    
    def _align_features(self, df):
        """
        Align features with training data columns.
        
        Args:
            df: Preprocessed DataFrame
            
        Returns:
            DataFrame with aligned features
        """
        if self.feature_columns is None:
            return df
        
        # Add missing columns with zeros
        for col in self.feature_columns:
            if col not in df.columns:
                df[col] = 0
        
        # Remove extra columns
        df = df[self.feature_columns]
        
        return df
    
    def predict(self, patient_data):
        """
        Make predictions for patient data.
        
        Args:
            patient_data: DataFrame with patient appointment data
            
        Returns:
            DataFrame with predictions added
        """
        # Load model if not already loaded
        if not self._model_loaded:
            self._load_model()
            self._prepare_scaler()
            self._model_loaded = True
        
        # Preprocess data
        processed_df = self._preprocess_patient_data(patient_data)
        
        # Align features
        X = self._align_features(processed_df)
        
        # Scale features
        if self.scaler is not None:
            X_scaled = self.scaler.transform(X)
        else:
            X_scaled = X.values
        
        # Make predictions
        probabilities = self.model.predict_proba(X_scaled)[:, 1]
        
        # Add predictions to original data
        result = patient_data.copy()
        result['noShowProbability'] = probabilities
        result['riskLevel'] = result['noShowProbability'].apply(
            lambda p: 'High' if p >= 0.6 else ('Medium' if p >= 0.3 else 'Low')
        )
        
        # Calculate previous no-shows if available
        if 'No-show' in patient_data.columns:
            result['previousNoShows'] = (
                patient_data.groupby('PatientId')['No-show']
                .transform(lambda x: (x == 'Yes').sum())
            )
        else:
            result['previousNoShows'] = 0
        
        return result


# Singleton instance
_prediction_service = None

def get_prediction_service():
    """Get or create the prediction service instance."""
    global _prediction_service
    if _prediction_service is None:
        # Create service instance (model loading is lazy, so this won't fail here)
        _prediction_service = PredictionService()
    return _prediction_service

