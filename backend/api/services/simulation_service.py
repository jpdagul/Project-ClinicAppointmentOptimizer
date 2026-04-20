import random
from typing import Dict, Any, List
import simpy

from .prediction_service import get_prediction_service

# Monte Carlo iteration counts
MONTE_CARLO_RUNS = 50
SWEEP_MC_RUNS = 20

# Clinic behavior parameters
WALK_IN_RATE = 0.05
LATE_ARRIVAL_PROB = 0.15
LATE_ARRIVAL_MAX_MIN = 15

# Appointment type mix: follow-up, standard, new patient
APPT_TYPE_WEIGHTS = [0.4, 0.4, 0.2]
APPT_TYPE_FACTORS = [0.5, 1.0, 1.5]

# Time-of-day no-show multipliers (morning, mid-morning, afternoon, late)
TOD_MULTIPLIERS = [1.20, 0.90, 0.95, 1.15]


def _pick_duration(avg_time: float, rng: random.Random) -> float:
    r = rng.random()
    cumulative = 0.0
    factor = APPT_TYPE_FACTORS[-1]
    for w, f in zip(APPT_TYPE_WEIGHTS, APPT_TYPE_FACTORS):
        cumulative += w
        if r <= cumulative:
            factor = f
            break
    return avg_time * factor * rng.uniform(0.9, 1.1)


def _tod_multiplier(slot_index: int, total_slots: int) -> float:
    if total_slots <= 0:
        return 1.0
    fraction = slot_index / total_slots
    idx = min(int(fraction * len(TOD_MULTIPLIERS)), len(TOD_MULTIPLIERS) - 1)
    return TOD_MULTIPLIERS[idx]


def _resize_probs(probs: List[float], target: int) -> List[float]:
    if not probs:
        raise ValueError("No prediction probabilities available to run the simulation.")
    if len(probs) >= target:
        return list(probs[:target])
    return [probs[i % len(probs)] for i in range(target)]


def _simulate_clinic(
    doctors: int,
    no_show_probs: List[float],
    avg_time: float,
    clinic_minutes: float,
    rng: random.Random,
) -> Dict[str, Any]:
    env = simpy.Environment()
    doctor_res = simpy.Resource(env, capacity=doctors)

    wait_times: List[float] = []
    busy_time = {"total": 0.0}
    showed_up = {"total": 0}
    scheduled = len(no_show_probs)

    # A single patient visit: queue for a doctor, then get served
    def patient_visit(env, duration):
        showed_up["total"] += 1
        arrival = env.now
        with doctor_res.request() as req:
            yield req
            wait_times.append(env.now - arrival)
            busy_time["total"] += duration
            yield env.timeout(duration)

    # Stagger scheduled arrivals across the clinic day
    def scheduled_arrivals(env):
        if scheduled <= 0:
            return
        interval = clinic_minutes / scheduled

        for i, prob in enumerate(no_show_probs):
            adj_prob = min(0.95, prob * _tod_multiplier(i, scheduled))

            if rng.random() >= adj_prob:
                duration = _pick_duration(avg_time, rng)

                # Some patients arrive late
                if rng.random() < LATE_ARRIVAL_PROB:
                    late = rng.uniform(1, LATE_ARRIVAL_MAX_MIN)
                    yield env.timeout(late)
                    env.process(patient_visit(env, duration))
                    yield env.timeout(max(0, interval - late))
                else:
                    env.process(patient_visit(env, duration))
                    yield env.timeout(interval)
            else:
                yield env.timeout(interval)

    # Unscheduled walk-in patients throughout the day
    def walk_in_arrivals(env):
        n = max(1, int(scheduled * WALK_IN_RATE))
        times = sorted(rng.uniform(0, clinic_minutes * 0.8) for _ in range(n))
        prev = 0.0
        for t in times:
            yield env.timeout(t - prev)
            env.process(patient_visit(env, _pick_duration(avg_time, rng)))
            prev = t

    env.process(scheduled_arrivals(env))
    if scheduled > 0:
        env.process(walk_in_arrivals(env))
    env.run(until=clinic_minutes)

    avg_wait = sum(wait_times) / len(wait_times) if wait_times else 0.0
    total_doctor_time = doctors * clinic_minutes
    utilization = (
        min(100.0, (busy_time["total"] / total_doctor_time) * 100.0)
        if total_doctor_time > 0
        else 0.0
    )
    # Overflow = patients who showed up but never got served before closing
    overflow = max(0, showed_up["total"] - len(wait_times))

    return {
        "avg_wait": avg_wait,
        "wait_times": list(wait_times),
        "utilization": utilization,
        "overflow": overflow,
    }


# Score from 0-100 based on wait time, variance, extreme waits, and overflow
def _patient_satisfaction(
    wait_times: List[float],
    overflow: int,
    scheduled: int,
) -> float:
    if not wait_times and overflow == 0:
        return 100.0

    overflow_penalty = min(45.0, (overflow / max(1, scheduled)) * 60.0)

    if not wait_times:
        return max(0.0, 100.0 - overflow_penalty)

    avg_wait = sum(wait_times) / len(wait_times)
    n = len(wait_times)

    # Penalty for average wait time (scaled to a 30-min threshold)
    wait_penalty = min(30.0, (avg_wait / 30.0) * 30.0)

    # Penalty for unpredictable wait times
    if n > 1:
        variance = sum((w - avg_wait) ** 2 for w in wait_times) / n
        variance_penalty = min(10.0, (variance ** 0.5 / 15.0) * 10.0)
    else:
        variance_penalty = 0.0

    # Penalty for individual waits exceeding 45 minutes
    extreme_count = sum(1 for w in wait_times if w > 45)
    extreme_penalty = min(15.0, (extreme_count / n) * 30.0)

    return max(
        0.0,
        100.0 - wait_penalty - variance_penalty - extreme_penalty - overflow_penalty,
    )


# Run the simulation n_runs times with different seeds and average results
def _run_monte_carlo(
    doctors: int,
    no_show_probs: List[float],
    avg_time: float,
    clinic_minutes: float,
    n_runs: int = MONTE_CARLO_RUNS,
    seed: int = 42,
) -> Dict[str, float]:
    waits: List[float] = []
    utils: List[float] = []
    overflows: List[int] = []
    sats: List[float] = []
    scheduled = len(no_show_probs)

    for i in range(n_runs):
        rng = random.Random(seed + i)
        result = _simulate_clinic(
            doctors, no_show_probs, avg_time, clinic_minutes, rng,
        )
        waits.append(result["avg_wait"])
        utils.append(result["utilization"])
        overflows.append(result["overflow"])
        sats.append(
            _patient_satisfaction(
                result["wait_times"], result["overflow"], scheduled,
            )
        )

    def _mean(vals):
        return sum(vals) / len(vals) if vals else 0.0

    return {
        "averageWaitTime": round(_mean(waits), 1),
        "doctorUtilization": round(_mean(utils), 1),
        "overflowPatients": int(round(_mean(overflows))),
        "patientSatisfaction": round(_mean(sats), 1),
    }


# Sweep overbooking 0-30% and pick the level with the best weighted score
def _find_optimal_overbooking(
    doctors: int,
    base_probs: List[float],
    slots: int,
    avg_time: float,
    clinic_minutes: float,
    seed: int = 42,
) -> int:
    best_score = -float("inf")
    best_pct = 0

    for pct in range(0, 31):
        scheduled = int(slots * (1 + pct / 100.0))
        if scheduled <= 0:
            continue
        probs = _resize_probs(base_probs, scheduled)

        mc = _run_monte_carlo(
            doctors, probs, avg_time, clinic_minutes,
            n_runs=SWEEP_MC_RUNS, seed=seed,
        )

        # Weighted objective: reward utilization/satisfaction, penalize overflow/wait
        score = (
            mc["doctorUtilization"] * 0.3
            + mc["patientSatisfaction"] * 0.5
            - mc["overflowPatients"] * 10.0
            - mc["averageWaitTime"] * 0.5
        )

        if score > best_score:
            best_score = score
            best_pct = pct

    return best_pct


class SimulationService:

    @staticmethod
    def run_simulation(params: Dict[str, Any], uploaded_patients=None) -> Dict[str, Any]:

        # Validate required parameters
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

        # Get ML no-show probabilities for the sampled patients
        preds = get_prediction_service().predict(sampled)

        if len(preds) > 0:
            all_probs = preds["noShowProbability"].tolist()
            avg_p = preds["noShowProbability"].mean()
            med_p = preds["noShowProbability"].median()
            high = int((preds["noShowProbability"] >= 0.6).sum())
            med = int(
                ((preds["noShowProbability"] >= 0.3) &
                 (preds["noShowProbability"] < 0.6)).sum()
            )
            low = int((preds["noShowProbability"] < 0.3).sum())
        else:
            all_probs = []
            avg_p = med_p = 0.0
            high = med = low = 0

        # Per-patient probabilities for the simulation
        predicted_probs = _resize_probs(all_probs, scheduled)

        # Run Monte Carlo simulation
        mc = _run_monte_carlo(
            doctors, predicted_probs, avg_time, clinic_minutes,
            n_runs=MONTE_CARLO_RUNS, seed=42,
        )

        # Find optimal overbooking level
        recommended = _find_optimal_overbooking(
            doctors, all_probs, slots, avg_time, clinic_minutes, seed=42,
        )

        return {
            "date": params["date"],
            "slotsPerDay": slots,
            "scheduledAppointments": scheduled,
            "uploadedPatientCount": len(uploaded_patients),
            "patientsAnalyzed": len(sampled),
            "predicted": {
                "averageWaitTime": mc["averageWaitTime"],
                "doctorUtilization": mc["doctorUtilization"],
                "patientSatisfaction": mc["patientSatisfaction"],
                "overflowPatients": mc["overflowPatients"],
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
        # Return zeros when no data is available
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

        # Clip extreme probabilities to keep the simulation realistic
        total_patients = len(preds)
        bounded_probs = preds["noShowProbability"].clip(0.05, 0.6)
        probs = bounded_probs.tolist()

        # Run Monte Carlo simulation on the cohort
        mc = _run_monte_carlo(
            doctors, probs, avg_time, clinic_minutes,
            n_runs=MONTE_CARLO_RUNS, seed=42,
        )

        # Find the best overbooking level for this cohort
        optimal = _find_optimal_overbooking(
            doctors, probs, slots, avg_time, clinic_minutes, seed=42,
        )

        high_risk = int((bounded_probs >= 0.6).sum())
        expected_attending = round(sum(1.0 - p for p in probs))
        no_show_rate = (
            (1.0 - (expected_attending / scheduled)) * 100 if scheduled else 0
        )

        return {
            'totalPatients': total_patients,
            'highRiskPatients': high_risk,
            'averageWaitTime': mc["averageWaitTime"],
            'doctorUtilization': mc["doctorUtilization"],
            'patientSatisfaction': mc["patientSatisfaction"],
            'noShowRate': round(no_show_rate, 1),
            'optimalOverbooking': optimal,
        }
