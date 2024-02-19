#!/usr/bin/env python3
import warnings
from listener import start_listener, receive_message, ack_message, close_connection
from hl7_processor import parse_hl7_message, extract_mrn
from data_processor import load_and_process_history, get_patient_history, update_patient_data
from aki_detector import load_model, aggregate_data, predict_aki
from pager_system import send_pager_message
from f3_evaluation import check_aki_detection_accuracy
import argparse
import pandas as pd
import os
import signal
import sys
from prometheus_client import start_http_server, Counter

historical_data = None

# metrics
MESSAGES_RECEIVED = Counter('messages_received_total', 'Total HTTP Requests (count)')
PAGES_SENT = Counter('pages_sent_total', 'Total Pages Sent (count)')

def saving_csv_for_shutdown(signum, frame):
    global historical_data
    print("Received SIGTERM. saving data to csv file")
    if not os.path.exists('/state'):
        os.makedirs('/state')
    historical_data.to_csv('/state/historical_data.csv', index=False)
    close_connection()
    sys.exit(0)

def reload_csv_from_shutdown():
    global historical_data
    file_path = '/state/historical_data.csv'
    if os.path.exists(file_path):
        print('load data from saved csv file')
        historical_data = pd.read_csv(file_path)
        return True
    else:
        return False


def parse_url(url):
    if url.startswith('http://'):
        url = url[7:]
    if url.startswith('https://'):
        url = url[8:]
    return url

def main():
    global historical_data
    # parameter parsing
    warnings.filterwarnings("ignore", category=FutureWarning)
    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('--history', type=str, help='path for history')
    parser.add_argument('--local', default=False, help='Show metrics if Local')
    parser.add_argument('--mllp', type=str, default='host.docker.internal:8440', help='mllp address for local')
    parser.add_argument('--pager', type=str, default='host.docker.internal:8441', help='pager address for local')
    args = parser.parse_args()

    # get address for mllp and pager
    if args.local:
        mllp = args.mllp
        mllp = parse_url(mllp)
        pager = args.pager
        pager = parse_url(pager)
    else:
        mllp = os.getenv('MLLP_ADDRESS')
        mllp = parse_url(mllp)
        pager = os.getenv('PAGER_ADDRESS')
        pager = parse_url(pager)

    # Start up the server to expose the metrics.
    start_http_server(8000)
    print("Prometheus metrics server running on port 8000")

    # local paths for local testing
    if not reload_csv_from_shutdown():
        print("not loading from state")
        if args.local:
            historical_data = load_and_process_history('/model/history.csv')
        else:
            historical_data = load_and_process_history(args.history)

    # load pre-trained model
    model = load_model('/model/aki_model.json')
    # expected outcomes
    aki_expected_outcomes = pd.read_csv('/model/aki.csv')

    # Initialize a list to record predictions
    recorded_predictions = []

    # start listener for mllp messages
    start_listener(mllp)

    try:
        # Register the SIGTERM signal handler
        signal.signal(signal.SIGTERM, saving_csv_for_shutdown)

        while True:
            message = receive_message()
            if message is None:
                print("No message received or connection closed, exiting loop.")
                break  # Exit the loop if no message is received or connection is closed
            MESSAGES_RECEIVED.inc()

            # Process the message
            parsed_data, type = parse_hl7_message(message)
            # extract mrn for the user
            mrn = extract_mrn(parsed_data)

            # if ADT (Admission, Discharge, Transfer), need to update current data
            if type == "ADT":
                historical_data = update_patient_data(mrn, parsed_data, historical_data, type=type)
            # if ORU (Observation Result), extract all pass history, aggregate and make prediction
            else:
                patient_history = get_patient_history(historical_data, mrn)

                combined_data = aggregate_data(parsed_data, patient_history)
                historical_data = update_patient_data(mrn, combined_data, historical_data, type=type)
                prediction, prediction_date = predict_aki(model, combined_data)

                # if detect aki
                if prediction:
                    print("page for mrn: " + str(mrn))
                    send_pager_message(mrn, pager)
                    PAGES_SENT.inc()
                    recorded_predictions.append({'mrn': mrn, 'prediction_date': prediction_date})

            ack_message()

    finally:
        if args.local:
            # metrics calculation for local
            recorded_predictions_df = pd.DataFrame(recorded_predictions)
            recorded_predictions_df.to_csv('recorded_predictions.csv', index=False)
            accuracy_report = check_aki_detection_accuracy(recorded_predictions_df, aki_expected_outcomes)
            print("AKI Detection Accuracy Report:", accuracy_report)

        print("Cleaning up resources...")
        close_connection()

if __name__ == "__main__":
    main()
