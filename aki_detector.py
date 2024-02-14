import xgboost as xgb
import pandas as pd
import numpy as np
from pandas import to_datetime

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

def aggregate_data(new_data, patient_history):
    '''
    Description:
        This function appends the new test date and result to the last non-NaN historical data
    input:
        new_data: DIC
        patient_history: pd DataFrame
    output:
        combined_data: pd DataFrame
    '''
    # get the new blood test date and result
    test_time = to_datetime(new_data['test_time'], format='%Y%m%d%H%M%S')
    test_result = float(new_data['test_result'])

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
    return combined_data

def predict_aki(model, combined_data):
    '''
    Description:    
        Predict acute kidney injury (AKI) using an XGBoost model based on the provided patient data.
    input:
        model: XGBoost model
        combined_data: pd DataFrame
    output:
        prediction: np array
    '''
    # Find the first NaN index
    first_nan_index = combined_data.iloc[0, 2:].isna().argmax() + 2 
    if first_nan_index == 2:
        first_nan_index = combined_data.shape[1]

    # Extract 'age' and 'sex' data
    age_sex_data = combined_data.iloc[:, :2]

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

    # Convert the reversed data to a list and fill with NaNs if necessary
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
        
    return prediction, prediction_date

