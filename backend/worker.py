import pika
import json
import redis
import hashlib
from datetime import datetime

from predict import predict_fight
from mongo import save_prediction


# ================== REDIS ==================
redis_client = redis.Redis(
    host="localhost",
    port=10004,
    db=0,
    decode_responses=True
)

CACHE_TTL = 600  # 10 минут


def make_cache_key(f1: str, f2: str) -> str:
    key = f"{f1.lower().strip()}__vs__{f2.lower().strip()}"
    return "predict:" + hashlib.md5(key.encode()).hexdigest()


# ================== CALLBACK ==================
def callback(ch, method, properties, body):
    data = json.loads(body)
    f1 = data["fighter1"]
    f2 = data["fighter2"]

    cache_key = make_cache_key(f1, f2)

    # 🔁 защита от повторной обработки
    if redis_client.exists(cache_key):
        print("🔁 CACHE EXISTS → SKIP")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    print(f"🐇 WORKER: {f1} vs {f2}")

    try:
        result = predict_fight(f1, f2)

        # 💾 Redis cache
        redis_client.setex(
            cache_key,
            CACHE_TTL,
            json.dumps(result)
        )

        # 🍃 MongoDB (история)
        save_prediction(result)

        print("🧠 RESULT SAVED")

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print("❌ ERROR:", e)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


# ================== RABBIT ==================
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host="localhost")
)

channel = connection.channel()
channel.queue_declare(queue="predict_queue", durable=True)
channel.basic_qos(prefetch_count=1)
channel.basic_consume(
    queue="predict_queue",
    on_message_callback=callback
)

print("🐇 Worker started")
channel.start_consuming()