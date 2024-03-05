import pandas as pd
import csv
import numpy as np
from datetime import datetime

def load_and_process_history(file_path):
    '''
    Description:
        This function reads the historical data from the csv file and processes it,
        adds 'age' and 'sex' columns to the data, fills any empty values with None
    input:
        file_path: STRING
    output:
        processed_data: pd DataFrame with the following columns:
        [mrn, age, sex, creatinine_date_0, creatinine_result_0, ..., creatinine_date_49, creatinine_result_49]
    '''
    # Read csv file
    with open(file_path, mode='r') as file:
        reader = csv.reader(file)
        historical_data = []

        # Skip the header
        next(reader, None)

        for row in reader:
            # Remove empty values
            row = [item for item in row if item]

            # Adding the first columns (mrn) back, and adding the second and the third columns as None to keep the same length
            processed_row = row[:1] + [None] + [None] + row[1:] + [None] * (101 - len(row))

            historical_data.append(processed_row)

    # fixed column names for the processed DataFrame
    processed_column_names = ['mrn', 'age', 'sex']

    # add the creatinine date and result columns to the column names
    for i in range(50):
        processed_column_names.append(f'creatinine_date_{i}')
        processed_column_names.append(f'creatinine_result_{i}')

    processed_df = pd.DataFrame(historical_data, columns=processed_column_names)

    # convert None to np.nan for consistency
    processed_df = processed_df.fillna(np.nan)

    return processed_df


def update_patient_data(mrn, parsed_data, historical_data, type):
    '''
    Description:
        This function handles two types of messages: 'ADT^A01' for new patient admissions,updating age and sex; 
        and 'ORU' for test results, replacing the patient's data with new data
    input:
        mrn: STRING
        parsed_data: DIC if type is 'ADT', pd DataFrame if type is 'ORU'
        historical_data: pd DataFrame
        type: STRING
    output:
        historical_data: pd DataFrame with the following columns:
        [mrn, age, sex, creatinine_date_0, creatinine_result_0, ..., creatinine_date_49, creatinine_result_49]
    '''
    # check if the message is an ADT message
    if type == 'ADT':
        message_type = parsed_data['message_type']

        # check if the message is an ADT^A01 message
        if message_type == 'ADT^A01':

            # check if the patient is already in the historical data
            if mrn not in historical_data['mrn'].values:
                # add the new patient to the historical data, with all None values
                new_patient = [mrn] + [None] * (len(historical_data.columns) - 1)
                historical_data.loc[len(historical_data)] = new_patient

            # update the age
            dob = datetime.strptime(parsed_data['date_of_birth'], '%Y%m%d')
            age = datetime.now().year - dob.year
            if (datetime.now().month, datetime.now().day) < (dob.month, dob.day):
                age -= 1
            historical_data.loc[historical_data['mrn'] == mrn, 'age'] = age

            # update the gender
            sex = parsed_data['sex']
            historical_data.loc[historical_data['mrn'] == mrn, 'sex'] = sex

    # check if the message is an ORU message
    elif type == 'ORU':
        combined_data = parsed_data

        # Check if combined_data has more columns than historical_data
        num_extra_columns = (combined_data.shape[1] + 1) - historical_data.shape[1]
        if num_extra_columns > 0:
            # Calculate the next index for the new columns based on existing column count
            next_index = (historical_data.shape[1] - 3) // 2
            new_date_col_name = f'creatinine_date_{next_index}'
            new_result_col_name = f'creatinine_result_{next_index}'
            # Add the new pair of columns with  None values
            historical_data[new_date_col_name] = None
            historical_data[new_result_col_name] = None
        # replace the whole row with the new data
        historical_data.loc[historical_data['mrn'] == mrn, historical_data.columns[1:]] = combined_data.values

    return historical_data


def get_patient_history(historical_data, mrn):
    '''
    Description:    
        This function returns the historical data for a specific patient based on its mrn
    input:
        historical_data: pd DataFrame
        mrn: STRING
    output:
        test_results: pd DataFrame with the following columns:
        [age, sex, creatinine_date_0, creatinine_result_0, ..., creatinine_date_26, creatinine_result_26]
    '''
    # get the patient's data, add the new patient to the historical data if it does not exist
    if mrn not in historical_data['mrn'].values:
        new_patient = [mrn] + [np.nan] * (len(historical_data.columns) - 1)
        historical_data.loc[len(historical_data)] = new_patient
    patient_data = historical_data[historical_data['mrn'] == mrn]
    test_results = patient_data.iloc[:, 1:]
    return test_results

