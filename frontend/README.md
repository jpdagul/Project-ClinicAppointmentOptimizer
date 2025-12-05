# Clinic Appointment Optimizer - Frontend

React-based web application for predicting patient no-shows and optimizing clinic scheduling.

## Features

### Dashboard

- Real-time clinic metrics (patients, wait times, utilization)
- Weekly performance tracking
- Patient satisfaction and no-show rate visualization
- Quick insights (optimal overbooking, peak days, no-show patterns)
- Overbooking strategy comparison

### Upload

- Drag & drop CSV file upload
- CSV format validation and documentation
- Download sample template
- Link to Kaggle dataset

### Predictions

- Patient no-show risk predictions with probability scores
- Risk level filtering (High/Medium/Low)
- Full patient data display (13 CSV columns + predictions)
- Sortable by probability, patient ID, or date

### Simulation

- Adjustable clinic parameters (doctors, slots, overbooking %, hours)
- Real-time simulation results
- Performance metrics (wait time, utilization, satisfaction)
- AI-powered recommendations

## Tech Stack

- React 19
- Vite
- Tailwind CSS
- JavaScript (ES6+)

## Getting Started

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

Application runs on `http://localhost:5173`

### Production Build

```bash
npm run build
npm run preview
```

## CSV Format Requirements

Your CSV must contain these 13 columns:

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
frontend/
├── src/
│   ├── pages/
│   │   ├── Dashboard.jsx
│   │   ├── Upload.jsx
│   │   ├── Predictions.jsx
│   │   └── Simulation.jsx
│   ├── App.jsx
│   ├── main.jsx
│   ├── config.js
│   └── index.css
├── package.json
└── vite.config.js
```

---

Built with React + Vite + Tailwind CSS
