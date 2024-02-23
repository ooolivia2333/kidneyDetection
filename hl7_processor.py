import re
import metrics

def parse_hl7_message(message):
    '''
    Parses an HL7 message into a dictionary based on message type.

    Parameters:
    - message_bytes: bytes, the HL7 message.
    - messages_parsed_counter: Counter, Prometheus counter for successfully parsed messages.
    - messages_parsed_failed_counter: Counter, Prometheus counter for failed parses.

    Returns:
    - Tuple (extracted_info, message_type_str): Where extracted_info is a dictionary containing parsed data, and message_type_str is a string indicating the message type ("ADT" or "ORU").
    '''

    def parse_adt_a01(message):
        pid_match = pid_pattern_long.search(message)
        if pid_match:
            return {
                'pid': pid_match.group(2),
                'name': pid_match.group(3),
                'date_of_birth': pid_match.group(4),
                'sex': pid_match.group(5)
            }
        else:
            return None

    def parse_adt_a03_or_oru(message, message_type):
        pid_match = pid_pattern_short.search(message)
        if not pid_match:
            return None

        extracted_info = {'pid': pid_match.group(2)}
        if message_type == 'ORU^R01':
            obr_match = obr_pattern.search(message)
            obx_match = obx_pattern.search(message)
            if obr_match and obx_match:
                extracted_info.update({
                    'test_time': obr_match.group(2),
                    'test_type': obx_match.group(3),
                    'test_result': obx_match.group(4)
                })
        return extracted_info

    message = message.decode('utf-8')

    # Define regular expressions for extracting information
    msh_pattern = re.compile(r'MSH\|.*?\|.*?\|.*?\|.*?\|.*?\|(\d{14})\|.*?(\bADT\^A01\b|\bADT\^A03\b|\bORU\^R01\b).*?\|(\d+\.\d+)\r*')
    pid_pattern_long = re.compile(r'PID\|(\d+)\|\|(\d+)\|\|([^|]+)\|\|(\d{8})\|([MF])')
    pid_pattern_short = re.compile(r'PID\|(\d+)\|\|(\d+)')
    obr_pattern = re.compile(r'OBR\|(\d+)\|\|\|\|\|\|(\d{14})')
    obx_pattern = re.compile(r'OBX\|(\d+)\|([^|]+)\|([^|]+)\|\|([.\d]+)')

    # Extract MSH information
    msh_match = msh_pattern.search(message)
    if not msh_match:
        metrics.MESSAGES_PARSED_FAILED.inc()
        return None, "Invalid Message Format"

    message_type = msh_match.group(2)
    extracted_info = {'date_and_time': msh_match.group(1), 'message_type': message_type}
    message_type_str = 'ADT' if 'ADT' in message_type else'ORU'

    if message_type in ['ADT^A01', 'ADT^A03']:
        extracted_info.update(
            parse_adt_a01(message) if message_type == 'ADT^A01' else parse_adt_a03_or_oru(message, message_type))
    elif message_type == 'ORU^R01':
        extracted_info.update(parse_adt_a03_or_oru(message, message_type))

    if not extracted_info:
        metrics.MESSAGES_PARSED_FAILED.inc()
        return None, message_type_str

    metrics.MESSAGES_PARSED.inc()
    return extracted_info, message_type_str


def extract_mrn(message):
    '''
    extract mrn
    input: 
        message: DIC
    output: 
        mrn: STRING
    '''
    return message['pid']


