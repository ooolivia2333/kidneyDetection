import re

def parse_hl7_message(message):
    '''
    using re to parse message into dictionary
    input: 
        message: STRING
            exaple: b'\x0bMSH|^~\\&|SIMULATION|SOUTH RIVERSIDE|||20240102135300||ADT^A01|||2.5\rPID|1||497030||ROSCOE DOHERTY||19870515|M\r\x1c\r'
    output: 
        extracted_info: DIC
            ADT01: date_and_time, message_type, pid, name, date_of_birth, sex
            ADT03: date_and_time, message_type, pid
            ORU: date_and_time, message_type, pid, test_time, test_type, test_result
        type: STRING 
            ADT/ORU
    '''
    
    message =  message.decode('utf-8')

    # Define regular expressions for extracting information
    msh_pattern = re.compile(r'MSH\|.*?\|.*?\|.*?\|.*?\|.*?\|(\d{14})\|.*?(\bADT\^A01\b|\bADT\^A03\b|\bORU\^R01\b).*?\|(\d+\.\d+)\r*')
    pid_pattern_long = re.compile(r'PID\|(\d+)\|\|(\d+)\|\|([^|]+)\|\|(\d{8})\|([MF])')
    pid_pattern_short = re.compile(r'PID\|(\d+)\|\|(\d+)')

    # Initialization
    extracted_info = {}
    type = ''

    # Extract MSH information
    msh_match = msh_pattern.search(message)
    if msh_match:
        extracted_info['date_and_time'] = msh_match.group(1)
        message_type = msh_match.group(2)
        extracted_info['message_type'] = message_type

        # Extract PID information for ADT messages
        if message_type == 'ADT^A01':
            type = 'ADT'
            pid_match = pid_pattern_long.search(message)
            if pid_match:
                extracted_info['pid'] = pid_match.group(2)
                extracted_info['name'] = pid_match.group(3)
                extracted_info['date_of_birth'] = pid_match.group(4)
                extracted_info['sex'] = pid_match.group(5)
            else:
                pass

        elif message_type == 'ADT^A03':
            type = 'ADT'
            pid_match = pid_pattern_short.search(message)
            if pid_match:
                extracted_info['pid'] = pid_match.group(2)

        # Extract information for ORU messages
        elif message_type == 'ORU^R01':
            type = 'ORU'
            pid_match = pid_pattern_short.search(message)
            if pid_match:
                extracted_info['pid'] = pid_match.group(2)

            obr_pattern = re.compile(r'OBR\|(\d+)\|\|\|\|\|\|(\d{14})')
            obx_pattern = re.compile(r'OBX\|(\d+)\|([^|]+)\|([^|]+)\|\|([.\d]+)')

            obr_match = obr_pattern.search(message)
            obx_match = obx_pattern.search(message)

            if obr_match:
                extracted_info['test_time'] = obr_match.group(2)

            if obx_match:
                extracted_info['test_type'] = obx_match.group(3)
                extracted_info['test_result'] = obx_match.group(4)


    return extracted_info, type


def extract_mrn(message):
    '''
    extract mrn
    input: 
        message: DIC
    output: 
        mrn: STRING
    '''
    return message['pid']


