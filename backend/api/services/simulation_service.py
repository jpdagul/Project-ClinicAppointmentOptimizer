"""
Service for clinic simulation and optimization.
"""
import random
import math


class SimulationService:
    """Service for running clinic simulations."""
    
    @staticmethod
    def run_simulation(parameters):
        """
        Run clinic simulation with given parameters.
        
        Args:
            parameters: dict with simulation parameters:
                - doctors: number of doctors
                - slotsPerDay: appointment slots per day
                - overbookingPercentage: overbooking percentage
                - averageAppointmentTime: average appointment time in minutes
                - clinicHours: clinic operating hours
                
        Returns:
            dict: Simulation results
        """
        doctors = parameters.get('doctors', 3)
        slots_per_day = parameters.get('slotsPerDay', 20)
        overbooking_pct = parameters.get('overbookingPercentage', 10)
        avg_appt_time = parameters.get('averageAppointmentTime', 30)
        clinic_hours = parameters.get('clinicHours', 8)
        
        # Calculate total appointments (with overbooking)
        total_appointments = int(slots_per_day * (1 + overbooking_pct / 100))
        
        # Simulate no-show rate (typically 10-30%)
        no_show_rate = random.uniform(0.10, 0.30)
        actual_shows = int(total_appointments * (1 - no_show_rate))
        
        # Calculate utilization
        total_capacity = doctors * (clinic_hours * 60) / avg_appt_time
        utilization = min(100, (actual_shows / total_capacity) * 100) if total_capacity > 0 else 0
        
        # Calculate wait time based on utilization and overbooking
        base_wait_time = 15  # Base wait time in minutes
        wait_time_multiplier = 1 + (utilization / 100) * 2 + (overbooking_pct / 100) * 1.5
        average_wait_time = base_wait_time * wait_time_multiplier
        
        # Calculate patient satisfaction (inverse relationship with wait time)
        max_wait_for_satisfaction = 30
        satisfaction = max(60, 100 - (average_wait_time / max_wait_for_satisfaction) * 40)
        
        # Calculate overflow patients
        overflow_patients = max(0, actual_shows - int(total_capacity))
        
        # Recommend optimal overbooking based on utilization
        if utilization < 75:
            recommended_overbooking = min(15, overbooking_pct + 5)
        elif utilization > 90:
            recommended_overbooking = max(5, overbooking_pct - 5)
        else:
            recommended_overbooking = overbooking_pct
        
        return {
            'averageWaitTime': round(average_wait_time, 1),
            'doctorUtilization': round(utilization, 1),
            'patientSatisfaction': round(satisfaction, 1),
            'noShowRate': round(no_show_rate * 100, 1),
            'overflowPatients': overflow_patients,
            'recommendedOverbooking': int(recommended_overbooking)
        }
    
    @staticmethod
    def calculate_metrics(patient_data):
        """
        Calculate clinic metrics from patient data.
        
        Args:
            patient_data: DataFrame with patient appointment data
            
        Returns:
            dict: Calculated metrics
        """
        if patient_data is None or len(patient_data) == 0:
            return {
                'totalPatients': 0,
                'highRiskPatients': 0,
                'averageWaitTime': 0,
                'doctorUtilization': 0,
                'patientSatisfaction': 0,
                'noShowRate': 0,
                'optimalOverbooking': 10
            }
        
        total_patients = len(patient_data)
        
        # Count high risk patients (if predictions available)
        if 'riskLevel' in patient_data.columns:
            high_risk = len(patient_data[patient_data['riskLevel'] == 'High'])
        else:
            high_risk = 0
        
        # Calculate no-show rate (if available)
        if 'No-show' in patient_data.columns:
            no_show_rate = (patient_data['No-show'] == 'Yes').sum() / total_patients * 100
        else:
            no_show_rate = 0
        
        # Estimate other metrics
        average_wait_time = 28.5  # Default estimate
        doctor_utilization = 82.3  # Default estimate
        patient_satisfaction = 91.2  # Default estimate
        optimal_overbooking = 12  # Default estimate
        
        return {
            'totalPatients': total_patients,
            'highRiskPatients': high_risk,
            'averageWaitTime': average_wait_time,
            'doctorUtilization': doctor_utilization,
            'patientSatisfaction': patient_satisfaction,
            'noShowRate': round(no_show_rate, 1),
            'optimalOverbooking': optimal_overbooking
        }

