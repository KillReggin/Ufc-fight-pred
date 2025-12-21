import pika
import json

RABBIT_HOST = "localhost"
QUEUE_NAME = "predict_queue"


def send_predict_task(payload: dict):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBIT_HOST)
    )

    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    channel.basic_publish(
        exchange="",
        routing_key=QUEUE_NAME,
        body=json.dumps(payload),
        properties=pika.BasicProperties(
            delivery_mode=2  # persistent
        )
    )

    connection.close()