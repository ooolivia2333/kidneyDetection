import xgboost as xgb
import pandas as pd
import numpy as np
import time
from pandas import to_datetime
from datetime import datetime

def load_model(model_path):
    '''
    Description:
        Load the pre-trained XGBoost model
    input:
        model_path: STRING
    output:
        model: XGBoost model
    '''
    model = xgb.XGBClassifier()
    model.load_model(model_path)
    return model

def aggregate_data(new_data, patient_history, last_hour_test_data):
    '''
    Description:
        This function appends the new test date and result to the last non-NaN historical data
    input:
        new_data: DIC
        patient_history: pd DataFrame
        last_hour_test_data: pd DataFrame
    output:
        combined_data: pd DataFrame
        last_hour_test_data: pd DataFrame
        median_last_hour_test_data: pd DataFrame
    '''
    # get the new blood test date and result
    test_time = to_datetime(new_data['test_time'], format='%Y%m%d%H%M%S')
    test_result = float(new_data['test_result'])

    # calculate the median of the test result in last an hour
    current_time = datetime.now()
    new_test_data = [test_result] + [current_time]
    last_hour_test_data.loc[len(last_hour_test_data)] = new_test_data
    last_hour_test_data = last_hour_test_data[last_hour_test_data['prediction_time'] > (current_time - pd.Timedelta(hours=1))]
    median_last_hour_test_data = last_hour_test_data.iloc[:, :1].median().values[0]

    # Add the new test result to the last non-NaN historical data
    creatinine_pairs_count = (len(patient_history.columns) - 2) // 2

    for i in range(creatinine_pairs_count):
        result_col = f'creatinine_result_{i}'
        # Check if this result column is NaN
        if pd.isna(patient_history[result_col].values[0]):
            date_col = f'creatinine_date_{i}'
            # Update the patient_history DataFrame with the new test result and date
            patient_history.at[patient_history.index[0], date_col] = test_time
            patient_history.at[patient_history.index[0], result_col] = test_result
            break  # Only update the first NaN column and then exit the loop

    # No NaN found, so add a new pair of columns
    else:
        new_date_col_name = f'creatinine_date_{creatinine_pairs_count}'
        new_result_col_name = f'creatinine_result_{creatinine_pairs_count}'
        patient_history[new_date_col_name] = test_time
        patient_history[new_result_col_name] = test_result

    combined_data = patient_history
    return combined_data, last_hour_test_data, median_last_hour_test_data

def reverse_data(combined_data):
    '''
    Description:
        Reverse data to get the most recent 10 test results
    input:
        combined_data: pd DataFrame
    output:
        reversed_data: pd DataFrame
    '''
    # Find the first NaN index to reverse the data
    first_nan_index = combined_data.iloc[0, 2:].isna().argmax() + 2 
    if first_nan_index == 2:
        first_nan_index = combined_data.shape[1]

    # Reverse the data
    data_to_reverse = combined_data.iloc[0, 2:first_nan_index].dropna()
    reversed_data = data_to_reverse.iloc[::-1]

    # Ensure the reversed data has up to 10 elements
    if len(reversed_data) < 10:
        nan_fill = pd.Series([np.nan] * (10 - len(reversed_data)))
        reversed_data = pd.concat([reversed_data, nan_fill], ignore_index=True)
    else:
        reversed_data = reversed_data.iloc[:10]
    reversed_data = reversed_data.reset_index(drop=True)
    return reversed_data

def create_test_data(combined_data, reversed_data):
    '''
    Description:
        Create the test data for the prediction
    input:
        combined_data: pd DataFrame
        reversed_data: pd DataFrame
    output:
        test_data: pd DataFrame
    '''
    # Extract 'age' and 'sex' data
    age_sex_data = combined_data.iloc[:, :2]

    # Create a new DataFrame with the reversed data and the original
    new_column_order = [
        'age', 'sex', 
        'creatinine_result_0', 'creatinine_date_0', 
        'creatinine_result_1', 'creatinine_date_1', 
        'creatinine_result_2', 'creatinine_date_2',
        'creatinine_result_3', 'creatinine_date_3',
        'creatinine_result_4', 'creatinine_date_4',
    ]
    age = age_sex_data.iloc[0]['age']
    sex = age_sex_data.iloc[0]['sex']
    age_sex_data = [age, sex]

    # Convert the reversed data to a list
    # Use NaNs to fill the missing values, because the model expects uniform data structure(10 elements)
    if len(reversed_data) < 10:
        reversed_data = list(reversed_data) + [np.nan] * (10 - len(reversed_data)) 
    else:
        reversed_data = list(reversed_data)

    test_data = pd.DataFrame(columns = new_column_order)
    combined_data_list = age_sex_data + reversed_data
    test_data.loc[len(test_data)] = combined_data_list
    
    
    # Convert 'creatinine_result' columns to float and 'creatinine_date' columns to datetime
    for i in range(5):
        creatinine_result_col = f'creatinine_result_{i}'
        creatinine_date_col = f'creatinine_date_{i}'
        test_data[creatinine_result_col] = pd.to_numeric(test_data[creatinine_result_col], errors='coerce')
        test_data[creatinine_date_col] = pd.to_datetime(test_data[creatinine_date_col], errors='coerce')
    return test_data

def predict_aki(model, combined_data, prediction_rate_dic):
    '''
    Description:    
        Predict acute kidney injury (AKI) using an XGBoost model based on the provided patient data.
    input:
        model: XGBoost model
        combined_data: pd DataFrame
        prediction_rate_dic: DIC
    output:
        prediction: np array
        prediction_date: datetime
        prediction_latency: FLOAT
        prediction_rate_dic: DIC
    '''
    # Start the timer
    start_time = time.time()


    # Reverse the data
    reversed_data = reverse_data(combined_data)

    # Create the test data
    test_data = create_test_data(combined_data, reversed_data)

    last_test_date_column = 'creatinine_date_0'  # Adjust based on your actual data structure
    prediction_date = test_data[last_test_date_column].iloc[-1]  # Get the last (most recent) test date
    
    # Calculate the time differences and set 'creatinine_date_0' to 0
    for i in range(4, 0, -1):  # Start from the last date and go backwards
        current_col = f'creatinine_date_{i}'
        previous_col = f'creatinine_date_{i - 1}'
        test_data[current_col] = (test_data[current_col] - test_data[previous_col]).dt.total_seconds().abs()
    test_data['creatinine_date_0'] = 0

    # Map sex to 0 or 1
    sex_mapping = {'M': 0, 'F': 1}
    test_data['sex'] = test_data['sex'].map(sex_mapping)

    # Map age to numeric
    test_data['age'] = pd.to_numeric(test_data['age'], errors='coerce')

    # Make the prediction using the model
    prediction = model.predict(test_data)

    # End the timer
    end_time = time.time()
    
    # Calculate the prediction latency
    prediction_latency = end_time - start_time

    # Update the prediction rate
    if prediction[0] == 1:
        prediction_rate_dic["positive"] += 1
    else:
        prediction_rate_dic["negative"] += 1
    prediction_rate_dic["rate"] = prediction_rate_dic["positive"] / (prediction_rate_dic["positive"] + prediction_rate_dic["negative"])
        
    return prediction, prediction_date, prediction_latency, prediction_rate_dic

