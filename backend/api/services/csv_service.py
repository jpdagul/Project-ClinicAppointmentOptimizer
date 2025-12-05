"""
Service for processing CSV uploads.
"""
import pandas as pd
import random


class CSVService:
    """Service for processing CSV files."""
    
    @staticmethod
    def validate_csv(file):
        """
        Validate CSV file format.
        
        Args:
            file: Uploaded file object
            
        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            # Try to read the CSV
            df = pd.read_csv(file)
            
            # Check required columns
            required_columns = [
                'PatientId', 'AppointmentID', 'Gender', 'ScheduledDay',
                'AppointmentDay', 'Age', 'Neighbourhood', 'Scholarship',
                'Hipertension', 'Diabetes', 'Alcoholism', 'Handcap', 'SMS_received'
            ]
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return False, f"Missing required columns: {', '.join(missing_columns)}"
            
            if len(df) == 0:
                return False, "CSV file is empty"
            
            return True, None
            
        except Exception as e:
            return False, f"Error reading CSV: {str(e)}"
    
    @staticmethod
    def process_csv(file, limit=100):
        """
        Process CSV file and return DataFrame.
        
        Args:
            file: Uploaded file object
            limit: Maximum number of records to process (default: 100)
            
        Returns:
            DataFrame with patient data
        """
        df = pd.read_csv(file)
        
        # Limit to random sample if too many records
        if len(df) > limit:
            df = df.sample(n=limit, random_state=42).reset_index(drop=True)
        
        return df
    
    @staticmethod
    def get_sample_data():
        """
        Get sample data structure for reference.
        
        Returns:
            dict: Sample data structure
        """
        return {
            'columns': [
                'PatientId', 'AppointmentID', 'Gender', 'ScheduledDay',
                'AppointmentDay', 'Age', 'Neighbourhood', 'Scholarship',
                'Hipertension', 'Diabetes', 'Alcoholism', 'Handcap', 'SMS_received'
            ],
            'sample_row': {
                'PatientId': 29872499824296,
                'AppointmentID': 5642903,
                'Gender': 'F',
                'ScheduledDay': '2016-04-29T18:38:08Z',
                'AppointmentDay': '2016-04-29T00:00:00Z',
                'Age': 62,
                'Neighbourhood': 'JARDIM DA PENHA',
                'Scholarship': 0,
                'Hipertension': 1,
                'Diabetes': 0,
                'Alcoholism': 0,
                'Handcap': 0,
                'SMS_received': 0
            }
        }

