import random
from typing import Dict, Any, List
import simpy

from .prediction_service import get_prediction_service


def _simulate_clinic(
    doctors: int,
    attending: int,
    avg_time: float,
    clinic_minutes: float,
    seed: int = 42,
):
    rng = random.Random(seed)
    env = simpy.Environment()
    doctor_res = simpy.Resource(env, capacity=doctors)

    wait_times: List[float] = []
    busy_time = {"total": 0.0}

    def patient():
        arrival = env.now
        with doctor_res.request() as req:
            yield req
            wait_times.append(env.now - arrival)
            service_time = rng.uniform(avg_time * 0.8, avg_time * 1.2)
            busy_time["total"] += service_time
            yield env.timeout(service_time)

    def arrivals():
        interval = clinic_minutes / attending
        for _ in range(attending):
            env.process(patient())
            yield env.timeout(interval)

    if attending > 0:
        env.process(arrivals())

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
    def run_simulation(params: Dict[str, Any], uploaded_patients=None) -> Dict[str, Any]:
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

        if uploaded_patients is None or len(uploaded_patients) == 0:
            raise ValueError(
                "No uploaded patient data found. "
                "Please upload a CSV file on the Upload page first."
            )

        slots = int(params["slotsPerDay"])
        if slots <= 0:
            raise ValueError("slotsPerDay must be > 0")

        doctors = int(params["doctors"])
        overbooking_pct = float(params["overbookingPercentage"])
        avg_time = float(params["averageAppointmentTime"])
        clinic_minutes = float(params["clinicHours"]) * 60.0

        scheduled = int(slots * (1 + overbooking_pct / 100.0))

        if len(uploaded_patients) >= scheduled:
            sampled = uploaded_patients.sample(
                n=scheduled, random_state=42
            ).reset_index(drop=True)
        else:
            sampled = uploaded_patients.copy().reset_index(drop=True)

        preds = get_prediction_service().predict(sampled)

        if len(preds) > 0:
            expected_attending = round((1.0 - preds["noShowProbability"]).sum())
            avg_p = preds["noShowProbability"].mean()
            med_p = preds["noShowProbability"].median()
            high = int((preds["noShowProbability"] >= 0.6).sum())
            med = int(
                ((preds["noShowProbability"] >= 0.3) &
                 (preds["noShowProbability"] < 0.6)).sum()
            )
            low = int((preds["noShowProbability"] < 0.3).sum())
        else:
            expected_attending = 0
            avg_p = med_p = 0.0
            high = med = low = 0

        avg_wait, utilization, overflow = _simulate_clinic(
            doctors, expected_attending, avg_time, clinic_minutes
        )

        satisfaction = _patient_satisfaction(avg_wait, overflow, scheduled)
        overflow_rate = overflow / scheduled if scheduled > 0 else 0.0
        recommended = _recommend_overbooking(
            utilization, overflow_rate, overbooking_pct, avg_time
        )

        return {
            "date": params["date"],
            "slotsPerDay": slots,
            "scheduledAppointments": scheduled,
            "uploadedPatientCount": len(uploaded_patients),
            "patientsAnalyzed": len(sampled),
            "predicted": {
                "averageWaitTime": round(avg_wait, 1),
                "doctorUtilization": round(utilization, 1),
                "patientSatisfaction": round(satisfaction, 1),
                "overflowPatients": overflow,
                "recommendedOverbooking": recommended,
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
