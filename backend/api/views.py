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
    try:
        if 'patient_data' not in request.session:
            return Response({
                'totalPatients': 0,
                'highRiskPatients': 0,
                'averageWaitTime': 0,
                'doctorUtilization': 0,
                'patientSatisfaction': 0,
                'noShowRate': 0,
                'optimalOverbooking': 0,
            })

        patient_data = pd.DataFrame(request.session['patient_data'])

        params = request.session.get('last_simulation_params') or {
            'date': pd.Timestamp.today().strftime('%Y-%m-%d'),
            'doctors': 1,
            'slotsPerDay': 20,
            'overbookingPercentage': 10,
            'averageAppointmentTime': 30,
            'clinicHours': 8,
        }

        metrics = SimulationService.run_simulation_for_cohort(
            params, patient_data
        )

        request.session['dashboard_simulation'] = metrics
        request.session.modified = True

        return Response(metrics)

    except Exception as e:
        return Response(
            {'error': f'Error calculating metrics: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



@api_view(['GET'])
@csrf_exempt
def get_weekly_performance(request):
    sim = request.session.get('dashboard_simulation')
    if not sim:
        return Response([])

    total = sim['totalPatients']
    no_show_rate = sim['noShowRate'] / 100.0
    avg_wait = sim['averageWaitTime']

    weights = {
        'Mon': 1.1,
        'Tue': 1.0,
        'Wed': 1.0,
        'Thu': 1.1,
        'Fri': 1.2,
        'Sat': 0.9,
        'Sun': 0.7,
    }

    base = total / sum(weights.values())

    return Response([
        {
            'day': day,
            'appointments': int(base * w),
            'noShows': int(base * w * no_show_rate),
            'waitTime': round(avg_wait * w, 1),
        }
        for day, w in weights.items()
    ])



@api_view(['GET'])
@csrf_exempt
def get_overbooking_strategies(request):
    sim = request.session.get('dashboard_simulation')
    if not sim:
        return Response([])
    
    optimal = sim['optimalOverbooking']
    return Response([
        {
            'strategy': 'Current Strategy',
            'waitTime': sim['averageWaitTime'],
            'utilization': sim['doctorUtilization'],
            'satisfaction': sim['patientSatisfaction'],
            'suggestedOverbooking': None,
        },
        {
            'strategy': 'Optimal Strategy',
            'waitTime': max(0, sim['averageWaitTime'] - 5),
            'utilization': min(100, sim['doctorUtilization'] + 5),
            'satisfaction': min(100, sim['patientSatisfaction'] + 3),
            'suggestedOverbooking': optimal,
        },
    ])




@api_view(['GET'])
@csrf_exempt
def get_dashboard_insights(request):
    sim = request.session.get('dashboard_simulation')
    if not sim:
        return Response({})

    total = sim['totalPatients']
    no_show_rate = sim['noShowRate'] / 100.0
    avg_wait = sim['averageWaitTime']

    weights = {
        'Mon': 1.1,
        'Tue': 1.0,
        'Wed': 1.0,
        'Thu': 1.1,
        'Fri': 1.2,
        'Sat': 0.9,
        'Sun': 0.7,
    }

    base = total / sum(weights.values())

    weekly = [
        {
            'day': day,
            'appointments': int(base * w),
            'noShows': int(base * w * no_show_rate),
            'waitTime': round(avg_wait * w, 1),
        }
        for day, w in weights.items()
    ]

    peak = max(weekly, key=lambda x: x['appointments'])
    lowest = min(weekly, key=lambda x: x['noShows'])
    highest = max(weekly, key=lambda x: x['noShows'])

    return Response({
        'peakDay': {
            'day': peak['day'],
            'appointments': peak['appointments'],
        },
        'lowestNoShows': {
            'day': lowest['day'],
            'rate': round(
                (lowest['noShows'] / max(1, lowest['appointments'])) * 100, 1
            ),
        },
        'highestNoShows': {
            'day': highest['day'],
            'count': highest['noShows'],
        },
    })




@api_view(['POST'])
@csrf_exempt
def run_simulation(request):
    try:
        parameters = request.data

        required_params = [
            'date',
            'doctors',
            'slotsPerDay',
            'overbookingPercentage',
            'averageAppointmentTime',
            'clinicHours'
        ]

        missing = [p for p in required_params if p not in parameters]
        if missing:
            return Response(
                {'error': f'Missing parameters: {", ".join(missing)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        results = SimulationService.run_simulation(parameters)

        request.session['last_simulation_params'] = parameters
        request.session.modified = True

        return Response(results)

    except Exception as e:
        return Response(
            {'error': f'Error running simulation: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



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
