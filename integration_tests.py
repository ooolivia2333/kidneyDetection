#!/usr/bin/env python3
import unittest
import warnings

from data_processor import get_patient_history, load_and_process_history
from hl7_processor import parse_hl7_message, extract_mrn
from listener import receive_message, close_connection, ack_message, start_listener
from aki_detector import load_model, predict_aki, aggregate_data
from pager_system import send_pager_message
from datetime import datetime


"""
    Refer to unit_tests.py for a detailed description of how to run tests.
    Suggested:
        python -m unittest -v -b integration_tests.py
"""
class AKIModelIntegrationTesting(unittest.TestCase):
    def setUp(self):
        warnings.filterwarnings("ignore", category=FutureWarning)
        start_listener("0.0.0.0:8440")
        self.historical_data = load_and_process_history('history.csv')
        self.model = load_model('./aki_model.json')
        self.pager = "0.0.0.0:8441"

    # Tests the loaded model on a datum that should resolve to negative and ensures accuracy
    def test_model_loading_and_prediction_negative(self):
        patient_hist = None
        mrn = ''
        while True:
            message = receive_message()
            parsed_data, type = parse_hl7_message(message)
            if type == 'ORU':
                mrn = extract_mrn(parsed_data)
                patient_hist = get_patient_history(self.historical_data, mrn)
                if not patient_hist.empty:
                    break
            ack_message()

        combined_data = aggregate_data(parsed_data, patient_hist)
        prediction = predict_aki(self.model, combined_data)
        self.assertEqual(prediction[0], 0)

    # Tests the loaded model on a datum that is positive and ensures accuracy
    # Further sends a pager request, and checks latency < 3
    # tests the flow of data through all functions
    def test_model_loading_and_prediction_positive_and_latency(self):
        patient_hist = None
        mrn = ''
        first = None
        while True:
            first = datetime.now()
            message = receive_message()
            parsed_data, type = parse_hl7_message(message)
            if parsed_data['pid'] == '807122' and type == 'ORU':
                mrn = "807122"
                patient_hist = get_patient_history(self.historical_data, mrn)
                break
            ack_message()
        
        combined_data = aggregate_data(parsed_data, patient_hist)
        prediction = predict_aki(self.model, combined_data)
        send_pager_message('807122', self.pager)
        second = datetime.now()
        timeTaken = second - first
        
        self.assertLess(timeTaken.total_seconds(), 3.00)
        self.assertEqual(prediction[0], 1)

    def tearDown(self):
        close_connection()