import random
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import simpy

from .prediction_service import get_prediction_service

DATA_DIR = Path(__file__).resolve().parent
APPOINTMENTS_CSV = DATA_DIR / "appointment.csv"
PATIENTS_CSV = DATA_DIR / "patient.csv"

_APPOINTMENTS_CACHE = None
_PATIENT_POOL_CACHE = None


def _load_appointments():
    global _APPOINTMENTS_CACHE
    if _APPOINTMENTS_CACHE is None:
        df = pd.read_csv(APPOINTMENTS_CSV, parse_dates=["Appointment_Date"])
        df = df.rename(
            columns={
                "Appointment_Date": "date",
                "Attended": "attended",
                "DNA": "unattended",
            }
        )
        df["date"] = df["date"].dt.normalize()
        _APPOINTMENTS_CACHE = df
    return _APPOINTMENTS_CACHE


def _load_patient_pool():
    global _PATIENT_POOL_CACHE
    if _PATIENT_POOL_CACHE is None:
        df = pd.read_csv(PATIENTS_CSV)
        df = df.drop(columns=["No-show", "Attended", "DNA"], errors="ignore")
        _PATIENT_POOL_CACHE = df
    return _PATIENT_POOL_CACHE


def _simulate_clinic(
    doctors: int,
    attending: int,
    avg_time: float,
    clinic_minutes: float,
):
    env = simpy.Environment()
    doctor_res = simpy.Resource(env, capacity=doctors)

    wait_times: List[float] = []
    busy_time = {"total": 0.0}

    def patient():
        arrival = env.now
        with doctor_res.request() as req:
            yield req
            wait_times.append(env.now - arrival)
            service_time = random.uniform(avg_time * 0.8, avg_time * 1.2)
            busy_time["total"] += service_time
            yield env.timeout(service_time)

    if attending > 0:
        interval = clinic_minutes / attending
        for _ in range(attending):
            env.process(patient())
            env.timeout(interval)

    env.run(until=clinic_minutes)

    avg_wait = sum(wait_times) / len(wait_times) if wait_times else 0.0

    total_doctor_time = doctors * clinic_minutes
    utilization = (
        min(100.0, (busy_time["total"] / total_doctor_time) * 100.0)
        if total_doctor_time > 0
        else 0.0
    )

    capacity_patients = int(doctors * (clinic_minutes / avg_time))
    overflow = max(0, attending - capacity_patients)

    return avg_wait, utilization, overflow


def _patient_satisfaction(avg_wait: float, overflow: int, scheduled: int) -> float:
    wait_penalty = min(40.0, (avg_wait / 30.0) * 40.0)
    overflow_penalty = (overflow / scheduled) * 60.0 if scheduled > 0 else 0.0
    return 100.0 - wait_penalty - overflow_penalty


def _recommend_overbooking(
    utilization: float,
    overflow_rate: float,
    current: float,
    avg_appt_time: float,
) -> int:
    if utilization > 90 and avg_appt_time >= 45:
        return 0

    if overflow_rate > 0:
        return max(0, int(current - 5))

    if utilization < 70:
        return min(30, int(current + 5))

    if utilization > 90:
        return max(0, int(current - 5))

    return int(current)


class SimulationService:
    @staticmethod
    def run_simulation(params: Dict[str, Any]) -> Dict[str, Any]:

        required = [
            "date",
            "doctors",
            "slotsPerDay",
            "overbookingPercentage",
            "averageAppointmentTime",
            "clinicHours",
        ]
        for r in required:
            if r not in params:
                raise ValueError(f"Missing parameter: {r}")

        slots = int(params["slotsPerDay"])
        if slots <= 0:
            raise ValueError("slotsPerDay must be > 0")

        sim_date = pd.to_datetime(params["date"]).normalize()
        doctors = int(params["doctors"])
        overbooking_pct = float(params["overbookingPercentage"])
        avg_time = float(params["averageAppointmentTime"])
        clinic_minutes = float(params["clinicHours"]) * 60.0

        scheduled = int(slots * (1 + overbooking_pct / 100.0))

        daily = _load_appointments()
        row = daily[daily["date"] == sim_date]

        if row.empty:
            attended = daily["attended"].sum()
            unattended = daily["unattended"].sum()
        else:
            attended = int(row.iloc[0]["attended"])
            unattended = int(row.iloc[0]["unattended"])

        denom = attended + unattended
        show_rate = attended / denom if denom > 0 else 0.0
        no_show_rate = 1.0 - show_rate

        actual_attending = round(scheduled * show_rate)

        pool = _load_patient_pool()
        sampled = pool.sample(
            n=min(scheduled, len(pool)),
            replace=len(pool) < scheduled,
        ).reset_index(drop=True)

        preds = get_prediction_service().predict(sampled)

        if len(preds) > 0:
            expected_predicted_attending = round(
                (1.0 - preds["noShowProbability"]).sum()
            )
            avg_p = preds["noShowProbability"].mean()
            med_p = preds["noShowProbability"].median()
            high = int((preds["noShowProbability"] >= 0.6).sum())
            med = int(
                ((preds["noShowProbability"] >= 0.3) &
                 (preds["noShowProbability"] < 0.6)).sum()
            )
            low = int((preds["noShowProbability"] < 0.3).sum())
        else:
            expected_predicted_attending = 0
            avg_p = med_p = 0.0
            high = med = low = 0

        actual_sim = _simulate_clinic(
            doctors, actual_attending, avg_time, clinic_minutes
        )
        predicted_sim = _simulate_clinic(
            doctors, expected_predicted_attending, avg_time, clinic_minutes
        )

        actual_sat = _patient_satisfaction(
            actual_sim[0], actual_sim[2], scheduled
        )
        predicted_sat = _patient_satisfaction(
            predicted_sim[0], predicted_sim[2], scheduled
        )

        actual_overflow_rate = actual_sim[2] / scheduled if scheduled > 0 else 0.0
        predicted_overflow_rate = (
            predicted_sim[2] / scheduled if scheduled > 0 else 0.0
        )

        actual_reco = _recommend_overbooking(
            actual_sim[1], actual_overflow_rate, overbooking_pct, avg_time
        )
        predicted_reco = _recommend_overbooking(
            predicted_sim[1], predicted_overflow_rate, overbooking_pct, avg_time
        )

        return {
            "date": params["date"],
            "slotsPerDay": slots,
            "scheduledAppointments": scheduled,
            "daily_show_rate": round(show_rate * 100, 1),
            "daily_no_show_rate": round(no_show_rate * 100, 1),
            "actual": {
                "averageWaitTime": round(actual_sim[0], 1),
                "doctorUtilization": round(actual_sim[1], 1),
                "patientSatisfaction": round(actual_sat, 1),
                "overflowPatients": actual_sim[2],
                "recommendedOverbooking": actual_reco,
                "noShowRate": round(no_show_rate * 100, 1),
            },
            "predicted": {
                "averageWaitTime": round(predicted_sim[0], 1),
                "doctorUtilization": round(predicted_sim[1], 1),
                "patientSatisfaction": round(predicted_sat, 1),
                "overflowPatients": predicted_sim[2],
                "recommendedOverbooking": predicted_reco,
                "noShowRate": round(avg_p * 100, 1),
            },
            "predictedStats": {
                "averageNoShowProbability": round(avg_p, 3),
                "medianNoShowProbability": round(med_p, 3),
                "highRiskCount": high,
                "mediumRiskCount": med,
                "lowRiskCount": low,
            },
        }

    @staticmethod
    def run_simulation_for_cohort(params, patient_data):
        if patient_data is None or len(patient_data) == 0:
            return {
                'totalPatients': 0,
                'highRiskPatients': 0,
                'averageWaitTime': 0,
                'doctorUtilization': 0,
                'patientSatisfaction': 0,
                'noShowRate': 0,
                'optimalOverbooking': 0,
            }

        required = [
            "date",
            "doctors",
            "slotsPerDay",
            "overbookingPercentage",
            "averageAppointmentTime",
            "clinicHours",
        ]
        for r in required:
            if r not in params:
                raise ValueError(f"Missing parameter: {r}")

        slots = int(params["slotsPerDay"])
        doctors = int(params["doctors"])
        overbooking_pct = float(params["overbookingPercentage"])
        avg_time = float(params["averageAppointmentTime"])
        clinic_minutes = float(params["clinicHours"]) * 60.0

        scheduled = int(slots * (1 + overbooking_pct / 100.0))

        # Ensure predictions exist
        if "noShowProbability" not in patient_data.columns:
            preds = get_prediction_service().predict(patient_data)
        else:
            preds = patient_data.copy()

        if len(preds) > scheduled:
            preds = preds.sample(n=scheduled, random_state=42)

        total_patients = len(preds)

        bounded_probs = preds["noShowProbability"].clip(0.05, 0.6)

        expected_attending = round((1.0 - bounded_probs).sum())
        expected_attending = max(0, min(expected_attending, scheduled))

        avg_wait, utilization, overflow = _simulate_clinic(
            doctors, expected_attending, avg_time, clinic_minutes
        )

        satisfaction = _patient_satisfaction(avg_wait, overflow, scheduled)

        overflow_rate = overflow / scheduled if scheduled else 0.0
        optimal_overbooking = _recommend_overbooking(
            utilization, overflow_rate, overbooking_pct, avg_time
        )

        high_risk = int((bounded_probs >= 0.6).sum())
        no_show_rate = (
            (1.0 - (expected_attending / scheduled)) * 100 if scheduled else 0
        )

        return {
            'totalPatients': total_patients,
            'highRiskPatients': high_risk,
            'averageWaitTime': round(avg_wait, 1),
            'doctorUtilization': round(utilization, 1),
            'patientSatisfaction': round(satisfaction, 1),
            'noShowRate': round(no_show_rate, 1),
            'optimalOverbooking': int(optimal_overbooking),
        }