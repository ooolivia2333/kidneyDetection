#!/usr/bin/env python3
# Iqbal (evaluation too)
import unittest
import warnings

from data_processor import get_patient_history, update_patient_data, load_and_process_history
from hl7_processor import parse_hl7_message, extract_mrn
from listener import receive_message, close_connection, ack_message, start_listener
from aki_detector import load_model, predict_aki, aggregate_data
from pager_system import send_pager_message
from datetime import datetime

"""
    To run the unit tests, simply run the following command in the CLI:
        python -m unittest "<path to test file>"
    alternatively it can also be run from the main functions in any file as follows:
        unittest.main()
        
    for a verbose testing information logs through the CLI, add the -v tag as follows:
        python -m unittest -v "<path to test file>"
    to suppress print statements through CLI, add the -b tag as follows:
        python -m unittest -b "<path to test file>"
    Suggested:
        python -m unittest -v -b "<path to file>"
"""

class ListenerConnectionTesting(unittest.TestCase):
    def setUp(self):
        self.mllp = "0.0.0.0:8440"

    # Checks opening connection, sending message and receiving an appropriate message, and closing of connection
    def test_connection_to_simulator(self):
        start_listener(self.mllp)
        message = receive_message()
        self.assertIsNotNone(message)
        print('\nNot none assertion passed for message reception')
        close_connection()
        print('Connection started and closed successfully')

    # Checks if exception is raised when receiving without connection and that the output is None
    def test_reception_without_connection(self):
        message = receive_message()
        self.assertRaises(Exception)
        self.assertIsNone(message)
        print('None and Exception assertion passed')

class Hl7MessageServiceTesting(unittest.TestCase):
    def setUp(self):
        start_listener("0.0.0.0:8440")

    # Tests that the hl7_parsing service parses the data properly and supplies all data expected
    def test_hl7_parsing(self):
        message = receive_message()
        parsed_data, type = parse_hl7_message(message)
        self.assertIn('date_and_time', parsed_data)
        self.assertIn('message_type', parsed_data)
        self.assertIn('pid', parsed_data)
        self.assertIn('name', parsed_data)
        self.assertIn('date_of_birth', parsed_data)
        self.assertIn('sex', parsed_data)

        self.assertEqual(parsed_data['pid'], '497030')
        self.assertEqual(parsed_data['message_type'], 'ADT^A01')

        self.assertEqual(type, 'ADT')

    # tests that the extract MRN function works properly
    def test_extract_mrn(self):
        message = receive_message()
        parsed_data, _ = parse_hl7_message(message)
        mrn = extract_mrn(parsed_data)
        self.assertEqual(mrn, '497030')

    # tests that the simulator does not send the same patient after acknowledgment
    def test_acknowledgement(self):
        message = receive_message()
        parsed_data, _ = parse_hl7_message(message)
        mrn1 = extract_mrn(parsed_data)
        ack_message()
        message = receive_message()
        parsed_data, _ = parse_hl7_message(message)
        mrn2 = extract_mrn(parsed_data)
        self.assertNotEqual(mrn1, mrn2)

    def tearDown(self):
        close_connection()

class PagerSystemTesting(unittest.TestCase):
    def setUp(self):
        start_listener("0.0.0.0:8440")
        self.pager = "0.0.0.0:8441"

    # Sends paging request and ensures that it works
    def test_paging(self):
        send_pager_message('47823', self.pager)

    def tearDown(self):
        close_connection()