from kafka import KafkaProducer
import json

# Set up the Kafka producer
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',  # Kafka broker address
    value_serializer=lambda v: json.dumps(v).encode('utf-8')  # Ensure the message is serialized as JSON
)

# Send some valid JSON messages
for i in range(5):
    message = {'message': f'Hello Kafka {i}1111111'}  # Valid JSON message
    producer.send('predictor-topic', message)  # Send the message

producer.flush()  # Ensure all messages are sent
print("Messages sent successfully!")
