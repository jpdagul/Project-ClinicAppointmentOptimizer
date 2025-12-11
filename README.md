# Clinic Appointment Optimizer

A full-stack web application for predicting patient no-shows and optimizing clinic appointment scheduling through machine learning and simulation strategies.

## Overview

The Clinic Appointment Optimizer helps healthcare clinics reduce no-show rates and improve operational efficiency by:

- Predicting patient no-show probabilities using machine learning
- Simulating different overbooking strategies
- Providing real-time clinic performance analytics
- Enabling data-driven scheduling decisions

## Features

- **Dashboard** - Real-time clinic metrics, weekly performance tracking, and strategy comparison
- **Upload** - CSV file upload with format validation and sample templates
- **Predictions** - Patient no-show risk predictions with filtering and sorting
- **Simulation** - Interactive clinic parameter adjustment with optimization recommendations

## Tech Stack

- **Frontend**: React, Vite, Tailwind CSS
- **Backend**: Django, Django REST Framework
- **Machine Learning**: Python, scikit-learn, Gradient Boosting Classifier
- **Simulation**: SimPy for discrete event simulation

## Project Structure

```
Project-ClinicAppointmentOptimizer/
├── frontend/                          # React web application
├── backend/                           # Django REST API
├── model/                             # Machine learning model and training
├── patient_appointments_upload.csv    # Sample CSV for upload (110K+ records)
└── README.md                          # This file
```

## Getting Started

Each component has its own detailed README with setup instructions:

- **Frontend**: See `frontend/README.md`
- **Backend**: See `backend/README.md`
- **Model**: See `model/README.md`

## Dataset

This project uses the "Medical Appointment No Shows" dataset from Kaggle, containing patient appointment data with features like age, gender, scheduled day, appointment day, and various health conditions.

## Quick Test

To quickly test the website locally:

1. **Start the backend:**
```
cd backend
```
```
python3 -m venv venv
```
```
source venv/bin/activate
```
```
pip install -r requirements.txt
```
```
python manage.py migrate
```
```
python manage.py runserver
```

2. **Start the frontend (in a separate terminal):**
```
cd frontend
```
```
npm install
```
```
npm run dev
```

3. **Open your browser and go to http://localhost:5173 to access the web app.**

## License

This project is for educational purposes as part of CPAN 314 (Project Development I).
