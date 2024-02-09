import requests

def send_pager_message(mrn, url):
    '''
    send a pager message
    input:
        mrn: String
        port: int
    '''
    try:

        url = 'http://' + url + '/page'
        headers = {'Content-type': 'text/plain'}
        data = str(mrn)

        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        #print(response.text)
        
    except requests.exceptions.RequestException as e:
        print(f"Error sending page: {e}")
