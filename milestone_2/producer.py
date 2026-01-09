import pika  # to communicate with RabbitMQ 

# Create a connection to the RabbitMQ server running on localhost
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost')
)

# Create a channel on the RabbitMQ connection
channel = connection.channel()  # Channel is used to send messages to queues

# Declare (create) a queue named 'url_queue'
channel.queue_declare(queue='url_queue', durable=True)

# List of seed URLs to start crawling from 
seed_urls = [
    "https://www.w3schools.com/",
    "https://docs.python.org/3/",
    "https://www.geeksforgeeks.org/"
]

# Loop through each seed URL
for url in seed_urls:
    # Publish (send) the URL message to the RabbitMQ queue 
    channel.basic_publish(
        exchange='',              # Default exchange
        routing_key='url_queue',  # Queue name
        body=url                  # Message body contains the URL
    )

    # Print confirmation that URL was sent
    print(f"[PRODUCER] Sent: {url}")

# Close the connection after sending all seed URLs
connection.close()

