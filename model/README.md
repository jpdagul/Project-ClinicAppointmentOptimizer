# Healthcare No-Show Prediction Model
This repository contains the machine learning workflow developed to predict whether a patient is likely to miss a scheduled medical appointment. The model uses both demographic data and engineered behavioral features to estimate no-show probability and support clinical scheduling decisions.

The final selected model is a Gradient Boosting Classifier, chosen after comparing multiple algorithms and performing threshold tuning, class balancing, and cross-validation.

---

## Project Objectives

- Predict the likelihood of a patient not attending their appointment.
- Support clinics in improving scheduling efficiency by:
  - Reducing wasted appointment slots,
  - Aiding overbooking decisions,
  - Triggering reminder systems for high-risk patients.

---

# Machine Learning Workflow
## 1. Data Preprocessing

The raw dataset undergoes several transformations before training:

- Convert date fields into Python datetime format.
- Extract weekday information from both scheduling and appointment dates.
- One-hot encode categorical data such as gender and neighborhood.
- Remove invalid entries (for example, negative ages).
- Add engineered behavioral features including:
  - Days_Wait (time between booking and appointment),
  - Past_NoShow_Rate,
  - Missed_Before,
  - Total_Appointments,
  - Days_Since_Last_Appt.

The dataset is split into training and testing partitions after preprocessing.

---

## 2. Handling Class Imbalance (SMOTE)

The dataset is imbalanced: most patients attend their appointments.

To avoid the model predicting mostly “show,” the training set is balanced using SMOTE (Synthetic Minority Over-sampling Technique).  
SMOTE generates synthetic examples of the minority class (no-shows), allowing the model to learn meaningful patterns instead of biasing toward the majority class.

---

## 3. Model Training

The training phase compares several machine learning models:

- Decision Tree  
- Random Forest  
- Gradient Boosting  
- XGBoost  

Each model is evaluated using accuracy, precision, recall, F1-score, and five-fold cross-validation.  
Gradient Boosting provided the most stable balance of recall and precision across metrics.

---

## 4. Threshold Tuning
Most classifiers use a default threshold of 0.5 to convert probabilities into final labels.

However, in this use-case, it is more important to identify patients who are at risk of not attending.

Threshold tuning is performed to:

- Adjust the cutoff probability,
- Improve recall for the no-show class,
- Provide better operational value for clinics.

The tuned threshold selected during training is saved with the final model.

---

## 5. Evaluation Visualizations
The following plots are generated and saved in the `models/` directory:

- Confusion Matrix  
- Precision-Recall Curve  
- ROC Curve  
- Feature Importance Chart  

These visualizations provide transparency and help developers understand the model’s behavior.

---

# Feature List
The model accepts the following input features:

- Age  
- Gender_F, Gender_M (one-hot encoded)  
- Scholarship  
- Hipertension  
- Diabetes  
- Alcoholism  
- Handcap  
- SMS_received  
- Days_Wait  
- ScheduledDay_Weekday  
- AppointmentDay_Weekday  
- Neighbourhood_<name> (one-hot encoded neighborhoods)  
- Past_NoShow_Rate  
- Total_Appointments  
- Missed_Before  
- Days_Since_Last_Appt  

---

# Setup Instructions

## Prerequisites
Before running the project, ensure the following are installed:

- Python 3.10+  
- pip  

---

## Installation Steps
Clone the repository:

```bash
git clone https://github.com/edentesfai/healthcare_no_show_predictor
cd healthcare_no_show_predictor
```

Install required packages:
```bash
pip install -r requirements.txt
```

# Running the Training Pipeline
To run the full machine learning workflow:
```bash
python main.py
```

This will:
- Load and preprocess data,
- Apply SMOTE,
- Normalize inputs,
- Train multiple models and select the best,
- Tune the decision threshold,
- Generate evaluation plots,
- Save the final trained model in the models/ directory.

# Future Work
- Integrate model into the backend API.
- Build the clinic simulation using SimPy.
- Explore deep learning architectures.
- Improve dataset using richer clinic data sources.
