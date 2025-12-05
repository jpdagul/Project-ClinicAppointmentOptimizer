import pandas as pd
from sklearn.model_selection import train_test_split


def load_and_clean_data(file_path: str):
    # Load dataset
    df = pd.read_csv(file_path)
    print(f"Loaded dataset with {len(df)} rows and {len(df.columns)} columns")

    # cleanup
    df['ScheduledDay'] = pd.to_datetime(df['ScheduledDay'], errors='coerce')
    df['AppointmentDay'] = pd.to_datetime(df['AppointmentDay'], errors='coerce')
    df = df[df['Age'] >= 0]

    # feature engineering: time and scheduling
    df['Days_Wait'] = (df['AppointmentDay'] - df['ScheduledDay']).dt.days
    df['Appointment_DayOfWeek'] = df['AppointmentDay'].dt.weekday
    df['Appointment_Month'] = df['AppointmentDay'].dt.month
    df['Scheduled_Hour'] = df['ScheduledDay'].dt.hour

    # sort by patient and time for behavioral features
    df = df.sort_values(by=['PatientId', 'ScheduledDay'])

    # behavioral feature 1: past no-show rate
    df['No-show'] = df['No-show'].map({'Yes': 1, 'No': 0})
    df['Past_NoShow_Rate'] = (
        df.groupby('PatientId')['No-show']
        .transform(lambda x: x.shift().expanding().mean())
        .fillna(0)
    )

    # behavioral feature 2: total appointments per patient
    df['Total_Appointments'] = df.groupby('PatientId')['AppointmentID'].transform('count')

    # behavioral feature 3: missed before
    df['Missed_Before'] = (df['Past_NoShow_Rate'] > 0).astype(int)

    # behavioral feature 4: time since last appointment (in days)
    df['Prev_Appointment_Day'] = (
        df.groupby('PatientId')['AppointmentDay'].shift()
    )
    df['Days_Since_Last_Appt'] = (
        (df['AppointmentDay'] - df['Prev_Appointment_Day']).dt.days.fillna(0)
    )

    # behavioral feature 5: appointment frequency (per patient)
    # frequency = total appointments / (days between first and last appointment + 1)
    patient_min = df.groupby('PatientId')['AppointmentDay'].transform('min')
    patient_max = df.groupby('PatientId')['AppointmentDay'].transform('max')
    df['Patient_Active_Days'] = (patient_max - patient_min).dt.days + 1
    df['Appointment_Frequency'] = df['Total_Appointments'] / df['Patient_Active_Days'].replace(0, 1)

    # drop helper columns
    df.drop(columns=['Prev_Appointment_Day', 'Patient_Active_Days'], inplace=True, errors='ignore')

    # categorical encoding
    df = pd.get_dummies(df, columns=['Gender', 'Neighbourhood'], drop_first=True)

    # drop ID/date columns
    df.drop(columns=['PatientId', 'AppointmentID', 'ScheduledDay', 'AppointmentDay'], inplace=True, errors='ignore')

    # handle missing
    df.dropna(subset=['No-show'], inplace=True)

    # split into features and target
    X = df.drop(columns=['No-show'])
    y = df['No-show']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("Data preprocessing complete.")
    print("Train shape:", X_train.shape, "| Test shape:", X_test.shape)
    print("Sample features:\n", X_train.head(2))

    return X_train, X_test, y_train, y_test
