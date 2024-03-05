import socket
from datetime import datetime

MLLP_START_BLOCK = b'\x0b'  # Start of block
MLLP_END_BLOCK = b'\x1c'    # End of block
MLLP_CARRIAGE_RETURN = b'\x0d'  # Carriage return

def start_listener(url):
    host_name, port = url.split(':')
    # Set up socket connection to listen for HL7 messages
    global s
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (host_name, int(port))
    s.connect(server_address)
    print(f'Connected to {host_name}:{port}')

def receive_message():
    global s
    try:
        data = s.recv(1024)  # Attempt to receive data from the socket
        if data == b'':  # Check if the connection was closed
            print("Connection closed by the server.")
            s.close()  # Close the socket
            return None
        return data
    except Exception as e:
        print(f"An error occurred: {e}")
        s.close()  # Ensure the socket is closed to avoid resource leakage
        return None

def ack_message():
    global s
    current_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    ack_message = (
            b'\x0b'  # MLLP start block
            + f"MSH|^~\\&|||||{current_timestamp}||ACK|||2.5\r".encode()  # MSH segment with current timestamp and version 2.5
            + "MSA|AA\r".encode()  # MSA segment with acknowledgment type AA
            + b'\x1c'  # MLLP end block
            + b'\x0d'  # MLLP carriage return
    )

    s.send(ack_message)

def close_connection():
    # to properly close the connection
    global s
    s.close()