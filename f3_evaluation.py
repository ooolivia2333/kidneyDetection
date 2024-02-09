import pandas as pd

def check_aki_detection_accuracy(predictions, aki_data):
    """
    Calculates accuracy metrics for AKI predictions compared to expected outcomes, including precision, recall, F3 score, and overall accuracy. The function emphasizes the importance of recall in the performance evaluation by calculating the F3 score, which significantly weighs recall higher than precision.

    The accuracy metrics are calculated based on the comparison of predicted AKI cases against actual AKI cases from the provided datasets. True positives (TP) are predictions that match actual AKI cases, false positives (FP) are predictions where AKI was not actually present, and false negatives (FN) are actual AKI cases that were not predicted. Precision measures the accuracy of positive predictions, recall measures the proportion of actual positives that were correctly identified, and the F3 score is a weighted average of precision and recall, emphasizing recall.

    Parameters:
    - predictions (DataFrame): A DataFrame containing predicted AKI cases, with columns ['mrn', 'prediction_date'] where 'mrn' is the Medical Record Number and 'prediction_date' is the predicted date of AKI occurrence.
    - aki_data (DataFrame): A DataFrame containing actual AKI cases, with columns ['mrn', 'date'] where 'mrn' is the Medical Record Number and 'date' is the actual date of AKI occurrence.

    Returns:
    - accuracy_report (dict): A dictionary containing the following keys:
      - 'total_predictions': The total number of AKI predictions made.
      - 'correct_predictions': The number of predictions that correctly matched an actual AKI case (TP).
      - 'incorrect_predictions': The sum of predictions where AKI was not present (FP) and actual AKI cases that were not predicted (FN).
      - 'accuracy': The percentage of predictions that were correct (TP) out of all predictions made.
      - 'precision': The proportion of positive predictions that were correct.
      - 'recall': The proportion of actual positives that were correctly identified.
      - 'F3': The F3 score, emphasizing recall over precision in the evaluation of the model's performance.
    """
    predictions['mrn'] = predictions['mrn'].astype(str)
    aki_data['mrn'] = aki_data['mrn'].astype(str)
    aki_data['date'] = pd.to_datetime(aki_data['date'])
    predictions['prediction_date'] = pd.to_datetime(predictions['prediction_date'])

    # Merge predictions with aki_data to find matches (TP) and non-matches (FP)
    merged = pd.merge(predictions, aki_data, left_on=['mrn', 'prediction_date'], right_on=['mrn', 'date'], how='outer', indicator=True)

    # Count true positives (TP) and false positives (FP)
    TP = len(merged[merged['_merge'] == 'both'])
    FP = len(merged[(merged['_merge'] == 'left_only')])

    # Count false negatives (FN) as those present in aki_data but not in predictions
    FN = len(merged[merged['_merge'] == 'right_only'])

    # Calculate precision, recall, and F3 score
    precision = TP / (TP + FP) if (TP + FP) > 0 else 0
    recall = TP / (TP + FN) if (TP + FN) > 0 else 0
    F3 = (1 + 3**2) * (precision * recall) / ((3**2 * precision) + recall) if (precision + recall) > 0 else 0

    # Calculate accuracy
    total_predictions = TP + FP  # Total number of predictions made
    accuracy = (TP / total_predictions) * 100 if total_predictions > 0 else 0

    # Prepare the accuracy report
    accuracy_report = {
        'total_predictions': total_predictions,
        'correct_predictions': TP,
        'incorrect_predictions': FP + FN,
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'F3': F3
    }

    return accuracy_report