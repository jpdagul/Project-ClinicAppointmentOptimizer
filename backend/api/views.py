"""
API views for the Clinic Appointment Optimizer backend.
"""
import json
import logging
import traceback
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.response import Response
from rest_framework import status
import pandas as pd

logger = logging.getLogger(__name__)

from .services.prediction_service import get_prediction_service
from .services.csv_service import CSVService
from .services.simulation_service import SimulationService


@api_view(['POST'])
@parser_classes([MultiPartParser])
@csrf_exempt
def upload_csv(request):
    """
    Upload and process CSV file.
    
    Expected: FormData with CSV file
    Response: { success, message, processedRecords }
    """
    if 'file' not in request.FILES:
        return Response(
            {'success': False, 'message': 'No file provided'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    file = request.FILES['file']
    
    # Validate CSV
    file.seek(0)  # Reset file pointer
    is_valid, error_message = CSVService.validate_csv(file)
    
    if not is_valid:
        return Response(
            {'success': False, 'message': error_message},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Process CSV (limit to 100 records to avoid lag)
    file.seek(0)  # Reset file pointer
    try:
        df = CSVService.process_csv(file, limit=100)
        processed_records = len(df)
        
        # Store in session for later use
        # Convert to dict format that can be serialized
        request.session['patient_data'] = df.to_dict('records')
        request.session.modified = True  # Ensure session is saved
        
        return Response({
            'success': True,
            'message': f'File uploaded successfully! Processed {processed_records} records.',
            'processedRecords': processed_records
        })
    except Exception as e:
        return Response(
            {'success': False, 'message': f'Error processing file: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@parser_classes([JSONParser])
@csrf_exempt
def get_predictions(request):
    """
    Get predictions for patient data.
    
    Expected: JSON array of patient objects or use session data
    Response: Array of patient objects with noShowProbability, riskLevel, previousNoShows
    """
    try:
        # Check if data is in request body
        if request.data and isinstance(request.data, list) and len(request.data) > 0:
            patient_data = pd.DataFrame(request.data)
        # Check if data is in session
        elif 'patient_data' in request.session and len(request.session['patient_data']) > 0:
            patient_data = pd.DataFrame(request.session['patient_data'])
        else:
            return Response(
                {'error': 'No patient data provided. Please upload a CSV file first.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate that we have data
        if patient_data.empty:
            return Response(
                {'error': 'Patient data is empty. Please upload a valid CSV file.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get predictions
        try:
            prediction_service = get_prediction_service()
        except (FileNotFoundError, RuntimeError) as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        try:
            logger.info(f"Generating predictions for {len(patient_data)} patients")
            results = prediction_service.predict(patient_data)
            logger.info("Predictions generated successfully")
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"Error generating predictions: {error_trace}")
            return Response(
                {'error': f'Error generating predictions: {str(e)}. Please check the server logs for details.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Convert to list of dicts
        patients = results.to_dict('records')
        
        # Format response to match frontend expectations
        formatted_patients = []
        for patient in patients:
            formatted_patient = {
                'id': patient.get('PatientId', 0),
                'appointmentId': patient.get('AppointmentID', 0),
                'name': f"Patient #{patient.get('PatientId', 0)}",
                'gender': 'Female' if patient.get('Gender', 'F') == 'F' else 'Male',
                'scheduledDay': str(patient.get('ScheduledDay', '')),
                'appointmentDate': str(patient.get('AppointmentDay', '')),
                'age': patient.get('Age', 0),
                'neighbourhood': patient.get('Neighbourhood', ''),
                'scholarship': patient.get('Scholarship', 0),
                'hipertension': patient.get('Hipertension', 0),
                'diabetes': patient.get('Diabetes', 0),
                'alcoholism': patient.get('Alcoholism', 0),
                'handcap': patient.get('Handcap', 0),
                'smsReceived': patient.get('SMS_received', 0),
                'previousNoShows': int(patient.get('previousNoShows', 0)),
                'noShowProbability': float(patient.get('noShowProbability', 0)),
                'riskLevel': patient.get('riskLevel', 'Low')
            }
            formatted_patients.append(formatted_patient)
        
        return Response(formatted_patients)
        
    except Exception as e:
        return Response(
            {'error': f'Error generating predictions: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@csrf_exempt
def get_dashboard_metrics(request):
    """
    Get dashboard metrics.
    
    Response: { totalPatients, highRiskPatients, averageWaitTime, 
               doctorUtilization, patientSatisfaction, noShowRate, optimalOverbooking }
    """
    try:
        # Get patient data from session
        if 'patient_data' in request.session:
            patient_data = pd.DataFrame(request.session['patient_data'])
            metrics = SimulationService.calculate_metrics(patient_data)
        else:
            # Return zero metrics if no data
            metrics = {
                'totalPatients': 0,
                'highRiskPatients': 0,
                'averageWaitTime': 0,
                'doctorUtilization': 0,
                'patientSatisfaction': 0,
                'noShowRate': 0,
                'optimalOverbooking': 0
            }
        
        return Response(metrics)
        
    except Exception as e:
        return Response(
            {'error': f'Error calculating metrics: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@csrf_exempt
def get_weekly_performance(request):
    """
    Get weekly performance data.
    
    Response: Array of { day, appointments, noShows, waitTime }
    """
    try:
        # Get patient data from session
        if 'patient_data' in request.session:
            patient_data = pd.DataFrame(request.session['patient_data'])
            
            # Convert AppointmentDay to datetime
            patient_data['AppointmentDay'] = pd.to_datetime(patient_data['AppointmentDay'], errors='coerce')
            patient_data['DayOfWeek'] = patient_data['AppointmentDay'].dt.day_name()
            
            # Group by day of week
            day_mapping = {
                'Monday': 'Mon', 'Tuesday': 'Tue', 'Wednesday': 'Wed',
                'Thursday': 'Thu', 'Friday': 'Fri', 'Saturday': 'Sat', 'Sunday': 'Sun'
            }
            
            weekly_data = []
            for day_name, day_abbr in day_mapping.items():
                day_data = patient_data[patient_data['DayOfWeek'] == day_name]
                appointments = len(day_data)
                no_shows = len(day_data[day_data.get('No-show', pd.Series(['No'] * len(day_data))) == 'Yes']) if 'No-show' in day_data.columns else 0
                wait_time = 25  # Default estimate
                
                weekly_data.append({
                    'day': day_abbr,
                    'appointments': appointments,
                    'noShows': no_shows,
                    'waitTime': wait_time
                })
        else:
            # Return zero weekly data if no data
            weekly_data = [
                {'day': 'Mon', 'appointments': 0, 'noShows': 0, 'waitTime': 0},
                {'day': 'Tue', 'appointments': 0, 'noShows': 0, 'waitTime': 0},
                {'day': 'Wed', 'appointments': 0, 'noShows': 0, 'waitTime': 0},
                {'day': 'Thu', 'appointments': 0, 'noShows': 0, 'waitTime': 0},
                {'day': 'Fri', 'appointments': 0, 'noShows': 0, 'waitTime': 0},
                {'day': 'Sat', 'appointments': 0, 'noShows': 0, 'waitTime': 0},
                {'day': 'Sun', 'appointments': 0, 'noShows': 0, 'waitTime': 0},
            ]
        
        return Response(weekly_data)
        
    except Exception as e:
        return Response(
            {'error': f'Error calculating weekly performance: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@csrf_exempt
def get_overbooking_strategies(request):
    """
    Get overbooking strategy comparison.
    
    Response: Array of { strategy, waitTime, utilization, satisfaction }
    """
    # Only return strategies if patient data exists
    if 'patient_data' in request.session and len(request.session['patient_data']) > 0:
        strategies = [
            {
                'strategy': 'Conservative (5%)',
                'waitTime': 22,
                'utilization': 68,
                'satisfaction': 94
            },
            {
                'strategy': 'Current (10%)',
                'waitTime': 28,
                'utilization': 82,
                'satisfaction': 91
            },
            {
                'strategy': 'Aggressive (15%)',
                'waitTime': 35,
                'utilization': 89,
                'satisfaction': 87
            },
            {
                'strategy': 'Optimal (12%)',
                'waitTime': 26,
                'utilization': 85,
                'satisfaction': 92
            }
        ]
    else:
        # Return empty array if no data
        strategies = []
    
    return Response(strategies)


@api_view(['GET'])
@csrf_exempt
def get_dashboard_insights(request):
    """
    Get quick insights for dashboard.
    
    Response: { peakDay: { day, appointments }, lowestNoShows: { day, rate }, 
               highestNoShows: { day, count } } or null if no data
    """
    try:
        # Get patient data from session
        if 'patient_data' not in request.session or len(request.session['patient_data']) == 0:
            return Response(None)
        
        patient_data = pd.DataFrame(request.session['patient_data'])
        
        # Convert AppointmentDay to datetime
        patient_data['AppointmentDay'] = pd.to_datetime(patient_data['AppointmentDay'], errors='coerce')
        patient_data['DayOfWeek'] = patient_data['AppointmentDay'].dt.day_name()
        
        # Group by day of week
        day_mapping = {
            'Monday': 'Mon', 'Tuesday': 'Tue', 'Wednesday': 'Wed',
            'Thursday': 'Thu', 'Friday': 'Fri', 'Saturday': 'Sat', 'Sunday': 'Sun'
        }
        
        weekly_data = []
        for day_name, day_abbr in day_mapping.items():
            day_data = patient_data[patient_data['DayOfWeek'] == day_name]
            appointments = len(day_data)
            no_shows = len(day_data[day_data.get('No-show', pd.Series(['No'] * len(day_data))) == 'Yes']) if 'No-show' in day_data.columns else 0
            
            weekly_data.append({
                'day': day_abbr,
                'appointments': appointments,
                'noShows': no_shows
            })
        
        # Calculate insights
        # Find peak day (most appointments)
        peak_day = max(weekly_data, key=lambda x: x['appointments'])
        
        # Find lowest no-shows day (by rate)
        lowest_no_shows = min(
            [d for d in weekly_data if d['appointments'] > 0],
            key=lambda x: (x['noShows'] / x['appointments']) if x['appointments'] > 0 else 100,
            default=None
        )
        
        # Find highest no-shows day (by count)
        highest_no_shows = max(
            [d for d in weekly_data if d['appointments'] > 0],
            key=lambda x: x['noShows'],
            default=None
        )
        
        # Build response
        insights = {}
        
        if peak_day and peak_day['appointments'] > 0:
            insights['peakDay'] = {
                'day': peak_day['day'],
                'appointments': peak_day['appointments']
            }
        
        if lowest_no_shows and lowest_no_shows['appointments'] > 0:
            no_show_rate = (lowest_no_shows['noShows'] / lowest_no_shows['appointments']) * 100
            insights['lowestNoShows'] = {
                'day': lowest_no_shows['day'],
                'rate': round(no_show_rate, 1)
            }
        
        if highest_no_shows and highest_no_shows['appointments'] > 0:
            insights['highestNoShows'] = {
                'day': highest_no_shows['day'],
                'count': highest_no_shows['noShows']
            }
        
        return Response(insights if insights else None)
        
    except Exception as e:
        return Response(
            {'error': f'Error calculating insights: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@parser_classes([JSONParser])
@csrf_exempt
def run_simulation(request):
    """
    Run clinic simulation.

    Expected JSON body:
    {
      "date": "YYYY-MM-DD",
      "doctors": int,
      "slotsPerDay": int,
      "overbookingPercentage": float,
      "averageAppointmentTime": float,
      "clinicHours": float
    }
    """
    try:
        parameters = request.data

        required_params = ['date', 'doctors', 'slotsPerDay', 'overbookingPercentage',
                           'averageAppointmentTime', 'clinicHours']
        missing_params = [p for p in required_params if p not in parameters]

        if missing_params:
            return Response(
                {'error': f'Missing required parameters: {", ".join(missing_params)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        results = SimulationService.run_simulation(parameters)
        return Response(results)

    except Exception as e:
        return Response({'error': f'Error running simulation: {str(e)}'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@csrf_exempt
def clear_data(request):
    """
    Clear all patient data from session.
    
    Response: { success, message }
    """
    try:
        if 'patient_data' in request.session:
            del request.session['patient_data']
            request.session.modified = True
        
        return Response({
            'success': True,
            'message': 'All patient data has been cleared successfully.'
        })
    except Exception as e:
        return Response(
            {'success': False, 'message': f'Error clearing data: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
