from prometheus_client import Counter, Gauge

# metrics
MESSAGES_RECEIVED = Counter('messages_received_total', 'Total HTTP Requests (count)')
PAGES_SENT = Counter('pages_sent_total', 'Total Pages Sent (count)')
PREDICTION_LATENCY = Gauge('prediction_latency', 'Prediction latency')
OVERALL_LATENCY = Gauge('overall_latency', 'Overall latency')
PREDICTION_RATE = Gauge('prediction_rate', 'Prediction rate')
MEAN_INPUT = Gauge('mean_input', 'Mean input', ['column'])
MESSAGES_PARSED = Counter('messages_parsed_total', 'Total Parsed hl7 messages (count)')
MESSAGES_PARSED_FAILED = Counter('messages_parsed_failed_total', 'Total Parsed failed hl7 messages (count)')
PAGES_FAILED = Counter('pages_sent_failed_total', 'Total failed pages (count)')
BLOOD_TEST_RECEIVED = Counter('blood_test_messages_received_total', 'Total received blood test messages (count)')
