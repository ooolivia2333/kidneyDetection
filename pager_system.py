# Tony
import socket
import requests

def send_pager_message(mrn, port):
    '''
    send a pager message
    input:
        mrn: String
        port: int
    '''
    try:
        # for local
        # url = 'http://0.0.0.0:'+str(port)+'/page'
        # for docker
        url = 'http://host.docker.internal:'+str(port)+'/page'

        headers = {'Content-type': 'text/plain'}
        data = str(mrn)

        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        #print(response.text)
        
    except requests.exceptions.RequestException as e:
        print(f"Error sending page: {e}")


if __name__ == '__main__':
    send_pager_message('47823', 8441)
