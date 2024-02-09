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

def parse_url(url):
    if url.startswith('http://'):
        url = url[7:]
    if url.startswith('https://'):
        url = url[8:]
    return url

def main():
    # parameter parsing
    warnings.filterwarnings("ignore", category=FutureWarning)
    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('--mllp', type=str, help='Port for MLLP connection')
    parser.add_argument('--pager', type=str, help='Port for pager connection')
    args = parser.parse_args()

    # url parsing, put into a util function later
    mllp = args.mllp
    mllp = parse_url(mllp)

    pager = args.pager
    pager = parse_url(pager)

    # preprocess all historical data
    historical_data = load_and_process_history('/model/history.csv')
    # load pre-trained model
    model = load_model('/model/aki_model.json')
    # expected outcomes
    aki_expected_outcomes = pd.read_csv('/model/aki.csv')

    # local paths for local testing
    # historical_data = load_and_process_history('history.csv')
    # model = load_model('aki_model.json')
    # aki_expected_outcomes = pd.read_csv('aki.csv')

    # Initialize a list to record predictions
    recorded_predictions = []

    # start listener for mllp messages
    start_listener(mllp)

    try:
        while True:
            message = receive_message()
            if message is None:
                print("No message received or connection closed, exiting loop.")
                break  # Exit the loop if no message is received or connection is closed

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
                    send_pager_message(mrn, pager)
                    recorded_predictions.append({'mrn': mrn, 'prediction_date': prediction_date})

            ack_message()

    finally:
        # metrics calculation for local
        # recorded_predictions_df = pd.DataFrame(recorded_predictions)
        # recorded_predictions_df.to_csv('recorded_predictions.csv', index=False)
        # accuracy_report = check_aki_detection_accuracy(recorded_predictions_df, aki_expected_outcomes)
        # print("AKI Detection Accuracy Report:", accuracy_report)

        print("Cleaning up resources...")
        close_connection()

if __name__ == "__main__":
    main()
