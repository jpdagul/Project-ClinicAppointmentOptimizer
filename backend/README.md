# Clinic Appointment Optimizer - Backend

Django REST API backend for predicting patient no-shows and optimizing clinic scheduling using machine learning.

## Features

### CSV Upload & Processing

- CSV file validation (13 required columns)
- Automatic data processing and storage
- Session-based data management
- Support for up to 100 records per upload

### Predictions

- Patient no-show risk predictions with probability scores
- Risk level classification (High/Medium/Low)
- Behavioral feature engineering (previous no-shows, wait times)
- ML model integration (Gradient Boosting)

### Dashboard Analytics

- Real-time clinic metrics (patients, wait times, utilization)
- Weekly performance tracking
- Patient satisfaction and no-show rate calculations
- Overbooking strategy recommendations

### Simulation

- Discrete event simulation using SimPy
- Clinic parameter optimization (doctors, slots, overbooking %, hours)
- Real-time simulation results with event-based modeling
- Performance metrics (wait time, utilization, satisfaction)
- AI-powered recommendations based on simulation outcomes

## Tech Stack

- Django 4.2
- Django REST Framework 3.14+
- Python 3.9+
- SimPy 4.0+ (discrete event simulation)
- scikit-learn 1.3+
- pandas 2.0+
- numpy 1.24+
- django-cors-headers 4.0+

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Virtual environment (recommended)

### Installation

1. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Ensure the ML model is trained (see `../model/README.md` for training instructions).

### Development

1. Run database migrations:

```bash
python manage.py migrate
```

2. Start the development server:

```bash
python manage.py runserver
```

API runs on `http://localhost:8000`

### Model Verification

Check if the ML model can be loaded:

```bash
python check_model.py
```

## API Endpoints

### Upload

- **POST** `/api/upload`
  - Upload and process CSV file
  - Returns: `{ success, message, processedRecords }`

### Predictions

- **POST** `/api/predictions`

  - Get no-show predictions for uploaded patient data
  - Returns: Array of patient objects with `noShowProbability`, `riskLevel`, `previousNoShows`

- **POST** `/api/clear`
  - Clear all patient data from session
  - Returns: `{ success, message }`

### Dashboard

- **GET** `/api/dashboard/metrics`

  - Get real-time clinic metrics
  - Returns: `{ totalPatients, highRiskPatients, averageWaitTime, doctorUtilization, patientSatisfaction, noShowRate, optimalOverbooking }`

- **GET** `/api/dashboard/weekly-performance`

  - Get weekly performance data
  - Returns: Array of daily metrics `{ day, appointments, noShows, waitTime }`

- **GET** `/api/dashboard/overbooking-strategies`

  - Get overbooking strategy recommendations
  - Returns: Array of strategies with performance metrics

- **GET** `/api/dashboard/insights`
  - Get quick insights calculated from patient data
  - Returns: `{ peakDay: { day, appointments }, lowestNoShows: { day, rate }, highestNoShows: { day, count } }` or `null` if no data
  - Calculates peak appointment day, lowest no-show rate day, and highest no-show count day

### Simulation

- **POST** `/api/simulation/run`
  - Run discrete event simulation with custom parameters using SimPy
  - Body: `{ doctors, slotsPerDay, overbookingPercentage, averageAppointmentTime, clinicHours }`
  - Returns: Simulation results with metrics and recommendations
  - Uses event-based simulation to model patient arrivals, appointments, and no-shows

## CSV Format Requirements

The API expects CSV files with these 13 columns:

1. PatientId
2. AppointmentID
3. Gender (M/F)
4. ScheduledDay (ISO 8601)
5. AppointmentDay (ISO 8601)
6. Age
7. Neighbourhood
8. Scholarship (0/1)
9. Hipertension (0/1)
10. Diabetes (0/1)
11. Alcoholism (0/1)
12. Handcap (0-4)
13. SMS_received (0/1)

## Project Structure

```
backend/
├── api/
│   ├── services/
│   │   ├── csv_service.py
│   │   ├── prediction_service.py
│   │   └── simulation_service.py
│   ├── migrations/
│   ├── urls.py
│   ├── views.py
│   └── models.py
├── manage.py
├── settings.py
├── urls.py
├── requirements.txt
└── check_model.py
```

## Model Integration

The backend integrates with the trained ML model located at `../model/models/gradient_boosting_model.pkl`. The model must be trained before the API can make predictions.

**Model Path:** `model/models/gradient_boosting_model.pkl`

**Training Instructions:** See `../model/README.md` for detailed model training instructions.

## Simulation Implementation

The simulation service uses **SimPy** for discrete event simulation to accurately model clinic operations:

- **Event-based modeling**: Patient arrivals, appointments, and no-shows are simulated as discrete events
- **Resource management**: Doctors are modeled as SimPy resources with capacity constraints
- **Realistic scheduling**: Appointments are scheduled with proper time slots and overbooking
- **Performance metrics**: Wait times, utilization, and satisfaction are calculated from simulation events

The simulation runs multiple scenarios to provide accurate performance predictions and optimization recommendations.

## CORS Configuration

The backend is configured to accept requests from the frontend running on `http://localhost:5173`. CORS settings can be modified in `settings.py`.

---

Built with Django + Django REST Framework + SimPy + scikit-learn
