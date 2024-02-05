import xgboost as xgb
import pandas as pd
import numpy as np
from pandas import to_datetime
# from data_processor import load_and_process_history, get_patient_history, update_patient_data
# from hl7_processor import parse_hl7_message, extract_mrn
# from sklearn.metrics import confusion_matrix, fbeta_score, classification_report
# tammy
def load_model(model_path):
    '''
    Description:
        Load the pre-trained XGBoost model
    input:
        model_path: STRING
    output:
        model: XGBoost model
    '''
    # Load the pre-trained model
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
        This function processes the input data by reversing the order of creatinine results and 
        dates until the first occurrence of NaN, excluding the first two columns (assumed to be 'age' and 'sex'). 
        It prepares the data for the model by setting appropriate column names, converting data types, 
        and calculating time differences between creatinine test dates
    input:
        model: XGBoost model
        combined_data: pd DataFrame
    output:
        prediction: np array
    '''
    # Assuming combined_data is your DataFrame
    first_nan_index = combined_data.iloc[0, 2:].isna().argmax() + 2  # Adjust for the first two columns

    # Adjust for if no NaN is found, argmax will return 0, so the index should be the number of elements
    if first_nan_index == 2:
        first_nan_index = combined_data.shape[1]

    # Extract 'age' and 'sex' data
    age_sex_data = combined_data.iloc[:, :2]

    # Extract data to be reversed, up to the first NaN
    data_to_reverse = combined_data.iloc[0, 2:first_nan_index].dropna()

    # Reverse the data
    reversed_data = data_to_reverse.iloc[::-1]

    # Ensure the reversed data has up to 10 elements, filling with NaNs if necessary
    if len(reversed_data) < 10:
        # Create a series of NaNs to fill the difference
        nan_fill = pd.Series([np.nan] * (10 - len(reversed_data)))
        # Concatenate the reversed data with the NaN fill series
        reversed_data = pd.concat([reversed_data, nan_fill], ignore_index=True)
    else:
        # If the reversed series is longer than 10 elements, truncate it
        reversed_data = reversed_data.iloc[:10]

    # Reset index if necessary to align with a specific desired output format
    reversed_data = reversed_data.reset_index(drop=True)

    # Apply the new column names to the DataFrame
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

    # Reverse the data and fill with NaNs if necessary
    if len(reversed_data) < 10:
        reversed_data = list(reversed_data) + [np.nan] * (10 - len(reversed_data))  # Fill to ensure 10 elements
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
    
    # # Print the processed DataFrame
    # print("top rows of processed dataframe:")
    # print(test_data.head(10))
    
    
    # Make the prediction using the model
    prediction = model.predict(test_data)
        
    return prediction



# if __name__ == "__main__":
#     adt01_message = b'\x0bMSH|^~\\&|SIMULATION|SOUTH RIVERSIDE|||20240102135300||ADT^A01|||2.5\rPID|1||497030||ROSCOE DOHERTY||19870515|M\r\x1c\r'
#     adt03_message = b'\x0bMSH|^~\&|SIMULATION|SOUTH RIVERSIDE|||20240607141100||ADT^A03|||2.5\rPID|1||411749\r\x1c\r'
#     #oru_message =   b'\x0bMSH|^~\&|SIMULATION|SOUTH RIVERSIDE|||20240617120600||ORU^R01|||2.5\rPID|1||837440\rOBR|1||||||20240617120600\rOBX|1|SN|CREATININE||100.46338429249316\r\x1c\r'
#     oru_message =   b'\x0bMSH|^~\&|SIMULATION|SOUTH RIVERSIDE|||20240617120600||ORU^R01|||2.5\rPID|1||822825\rOBR|1||||||20240617120600\rOBX|1|SN|CREATININE||100.46338429249316\r\x1c\r'
#     test_2 = b'\x0bMSH|^~\\&|SIMULATION|SOUTH RIVERSIDE|||20240331003200||ORU^R01|||2.5\rPID|1||125412\rOBR|1||||||20240331003200\rOBX|1|SN|CREATININE||127.5695463720204\r\x1c\r'
#     test_1 =  b'\x0bMSH|^~\\&|SIMULATION|SOUTH RIVERSIDE|||20240310132300||ADT^A01|||2.5\rPID|1||125412||JAY BRIGGS||19730906|M\r\x1c\r'

#     test_3 = b'\x0bMSH|^~\\&|SIMULATION|SOUTH RIVERSIDE|||20240319094300||ADT^A01|||2.5\rPID|1||556361||HUSNA SHARPE||20210313|F\r\x1c\r'
#     test_4 = b'\x0bMSH|^~\\&|SIMULATION|SOUTH RIVERSIDE|||20240331083600||ORU^R01|||2.5\rPID|1||556361\rOBR|1||||||20240331083600\rOBX|1|SN|CREATININE||95.68952764805587\r\x1c\r'
#     test_5 = b'\x0bMSH|^~\\&|SIMULATION|SOUTH RIVERSIDE|||20240331084300||ORU^R01|||2.5\rPID|1||556361\rOBR|1||||||20240331084300\rOBX|1|SN|CREATININE||83.78383163660536\r\x1c\r'

#     test_6 = b'\x0bMSH|^~\&|SIMULATION|SOUTH RIVERSIDE|||20240617120600||ORU^R01|||2.5\rPID|1||731098\rOBR|1||||||20240617120600\rOBX|1|SN|CREATININE||100.46338429249316\r\x1c\r'

#     model = load_model('aki_model.json')

#     parsed_data, type = parse_hl7_message(oru_message)
#     print(parsed_data)
#     mrn = extract_mrn(parsed_data)


    # # predict the number 822825
    # historical_data = load_and_process_history('history.csv')
    # patient_history = get_patient_history(historical_data, str(822825))
    # combined_data = aggregate_data(parsed_data, patient_history)
    # historical_data = update_patient_data(mrn, combined_data, historical_data, type=type)
    # print(combined_data.iloc[0][0:])
    # prediction = predict_aki(model, combined_data)
    # print(prediction)

    # # predict history.csv
    # data = load_and_process_history('history.csv')
    # X = data.drop(columns=['mrn'])
    # predictions = predict_aki(model, X)

    # predict test_1-2
    # parsed_data, type = parse_hl7_message(test_1)
    # print(parsed_data)
    # mrn = extract_mrn(parsed_data)
    # historical_data = load_and_process_history('history.csv')
    # historical_data = update_patient_data(mrn, parsed_data, historical_data, type=type)

    # parsed_data, type = parse_hl7_message(test_2)
    # print(parsed_data)
    # mrn = extract_mrn(parsed_data)
    # patient_history = get_patient_history(historical_data, mrn)

    # combined_data = aggregate_data(parsed_data, patient_history)
    # historical_data = update_patient_data(mrn, combined_data, historical_data, type=type)
    # prediction = predict_aki(model, combined_data)
    # print(prediction)

    # print(historical_data.iloc[2096][0:])
    # prediction = predict_aki(model, combined_data)
    # print(prediction)

    # predict test_3-5
    # parsed_data, type = parse_hl7_message(test_3)
    # print(parsed_data)
    # mrn = extract_mrn(parsed_data)

    # historical_data = load_and_process_history('history.csv')
    # historical_data = update_patient_data(mrn, parsed_data, historical_data, type=type)

    # parsed_data, type = parse_hl7_message(test_4)
    # print(parsed_data)
    # mrn = extract_mrn(parsed_data)
    # patient_history = get_patient_history(historical_data, mrn)
    # combined_data = aggregate_data(parsed_data, patient_history)
    # historical_data = update_patient_data(mrn, combined_data, historical_data, type=type)
    # prediction = predict_aki(model, combined_data)
    # print(prediction)

    # parsed_data, type = parse_hl7_message(test_5)
    # print(parsed_data)
    # mrn = extract_mrn(parsed_data)
    # patient_history = get_patient_history(historical_data, mrn)
    # combined_data = aggregate_data(parsed_data, patient_history)
    # historical_data = update_patient_data(mrn, combined_data, historical_data, type=type)
    # prediction = predict_aki(model, combined_data)
    # print(prediction)

    # predict test_6
    # parsed_data, type = parse_hl7_message(test_6)
    # print(parsed_data)
    # mrn = extract_mrn(parsed_data)
    # historical_data = load_and_process_history('history.csv')
    # patient_history = get_patient_history(historical_data, mrn)
    # combined_data = aggregate_data(parsed_data, patient_history)
    # print(combined_data)
    # historical_data = update_patient_data(mrn, combined_data, historical_data, type=type)
    # print(historical_data.iloc[438][0:])
    # prediction = predict_aki(model, combined_data)
    # print(prediction)


    

    




