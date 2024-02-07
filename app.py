#!/usr/bin/env python3
import warnings
from listener import start_listener, receive_message, ack_message, close_connection
from hl7_processor import parse_hl7_message, extract_mrn
from data_processor import load_and_process_history, get_patient_history, update_patient_data
from aki_detector import load_model, aggregate_data, predict_aki
from pager_system import send_pager_message
import argparse

def main():
    warnings.filterwarnings("ignore", category=FutureWarning)
    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('--mllp', type=str, help='Port for MLLP connection')
    parser.add_argument('--pager', type=str, help='Port for pager connection')
    args = parser.parse_args()

    # url parsing, put into a util function later
    mllp = args.mllp
    if mllp.startswith('http://'):
        mllp = mllp[7:]
    if mllp.startswith('https://'):
        mllp = mllp[8:]

    pager = args.pager
    if pager.startswith('http://'):
        pager = pager[7:]
    if mllp.startswith('https://'):
        pager = pager[8:]

    # preprocess all historical data
    # historical_data = load_and_process_history('history.csv')
    historical_data = load_and_process_history('/model/history.csv')
    # load pre-trained model
    # model = load_model('aki_model.json')
    model = load_model('/model/aki_model.json')

    # start listener to port 8440
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
                prediction = predict_aki(model, combined_data)

                # if detect aki
                if prediction:
                    send_pager_message(mrn, pager)

            ack_message()

    finally:
        print("Cleaning up resources...")
        close_connection()

if __name__ == "__main__":
    main()
