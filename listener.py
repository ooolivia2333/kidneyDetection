import socket

MLLP_START_BLOCK = b'\x0b'  # Start of block
MLLP_END_BLOCK = b'\x1c'    # End of block
MLLP_CARRIAGE_RETURN = b'\x0d'  # Carriage return

def main():
    # Create a TCP/IP socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect the socket to the simulator's port
    server_address = ('localhost', 8440)  # Simulator's address and port
    s.connect(server_address)

    try:
        # Receiving data
        while True:
            data = s.recv(1024)
            if data:
                # Process your data here
                print('Received:', data)

                # Send acknowledgment back
                ack_message = (
                        b'\x0b'  # MLLP start block
                        + b"MSH|^~\\&|Listener|System|Simulator|SimulatorSystem|"
                        + b"202301011230||ACK|MessageControlId|P|2.3\r"
                        + b"MSA|AA|OriginalMessageControlId\r"
                        + b'\x1c'  # MLLP end block
                        + b'\x0d'  # MLLP carriage return
                )
                s.send(ack_message)
            else:
                break
    finally:
        s.close()

if __name__ == "__main__":
    main()