import requests
import datetime
import metrics

def send_pager_message(mrn, prediction_date, url):
    '''
    send a pager message
    input:
        mrn: String
        prediction_date: String : 2024-04-29 05:41:00
        port: int
    '''
    try:

        url = 'http://' + url + '/page'
        headers = {'Content-type': 'text/plain'}
       
        datetime_obj = datetime.datetime.strptime(str(prediction_date), "%Y-%m-%d %H:%M:%S")
        date = datetime_obj.strftime("%Y%m%d%H%M%S")

        data = str(mrn) + ',' + date

        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()

    except requests.exceptions.RequestException as e:
        print(f"Error sending page: {e}")
        metrics.PAGES_FAILED.inc()
