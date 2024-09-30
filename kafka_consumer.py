from kafka import KafkaConsumer
import json

# Set up the Kafka consumer
consumer = KafkaConsumer(
    'predictor-topic',  # Topic to listen to
    bootstrap_servers='localhost:9092',  # Kafka broker address
    auto_offset_reset='earliest',  # Start reading at the earliest message
    enable_auto_commit=True,  # Commit the messages automatically
    group_id='my-group',  # Consumer group ID
    value_deserializer=lambda x: x.decode('utf-8')  # Decode message as a string
)

# Consume the messages
for message in consumer:
    try:
        # Attempt to parse the message as JSON
        data = json.loads(message.value)
        print("Received message: {}".format(data))
    except json.JSONDecodeError as e:
        # Handle non-JSON or malformed messages
        print(f"Error decoding JSON: {e}. Raw message: {message.value}")
