import socket

MLLP_START_BLOCK = b'\x0b'  # Start of block
MLLP_END_BLOCK = b'\x1c'    # End of block
MLLP_CARRIAGE_RETURN = b'\x0d'  # Carriage return

def start_listener(port):
    # Set up socket connection to listen for HL7 messages
    global s  # Declare the socket as global to use it outside this function
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('localhost', port)
    s.bind(server_address)
    s.listen(1)  # Listen for incoming connections

def receive_message():
    # Logic to listen and receive messages
    global s
    connection, client_address = s.accept()  # Accept a connection
    try:
        data = connection.recv(1024)
        if data:
            # Strip the MLLP start and end block characters
            message = data.strip(MLLP_START_BLOCK + MLLP_END_BLOCK + MLLP_CARRIAGE_RETURN)
            return message  # Return the stripped message
    finally:
        connection.close()

def parse_hl7_message(message):
    # TODO: implement HL7 message parsing
    # return parsed_data, type
    pass

def ack_message():
    global s
    # TODO: Implement the logic to send ACK for the given message_control_id

    # Send acknowledgment back
    ack_message = (
            MLLP_START_BLOCK
            + b"MSH|^~\\&|Listener|System|Simulator|SimulatorSystem|"
            + b"202301011230||ACK|MessageControlId|P|2.3\r"
            + b"MSA|AA|OriginalMessageControlId\r"
            + MLLP_END_BLOCK
            + MLLP_CARRIAGE_RETURN
    )
    s.send(ack_message)
