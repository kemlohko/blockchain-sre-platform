import json
import os
import time

import pika
import requests
from database import Job, SessionLocal

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "admin")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "admin")

ETHEREUM_RPC_URL = os.getenv(
    "ETHEREUM_RPC_URL",
    "https://ethereum-sepolia-rpc.publicnode.com"
)

QUEUE_NAME = "blockchain_jobs"
RETRY_QUEUE = "blockchain_jobs_retry"
DLQ_NAME = "blockchain_jobs_dlq"
DLX_NAME = "blockchain_dlx"

MAX_RETRIES = 3

def get_transaction(tx_hash):
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getTransactionByHash",
        "params": [tx_hash],
        "id": 1
    }

    response = requests.post(
        ETHEREUM_RPC_URL,
        json=payload,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    if "error" in data:
        raise RuntimeError(data["error"])
    
    return data.get("result")


def process_job(ch, method, properties, body):
    job = json.loads(body)
    db = SessionLocal()

    print(f"Received job: {job}")

    try:
        db_job = db.get(Job, job["job_id"])

        if db_job:
            db_job.status = "PROCESSING"
            db.commit()
    finally:
        db.close()
    
    try:
        if job["type"] == "transaction_analysis":

            tx = get_transaction(job["tx_hash"])

            if tx is None:
                raise RuntimeError(
                    f"Transaction not found: {job['tx_hash']}"
                )
            
            else:
                result = {
                    "job_id": job["job_id"],
                    "tx_hash": tx["hash"],
                    "from": tx["from"],
                    "to": tx["to"],
                    "value_wei": int(tx["value"], 16),
                    "block_number": (
                        int(tx["blockNumber"], 16)
                        if tx.get("blockNumber")
                        else None
                    )
                }

                print("Transaction analyzed:")
                print(json.dumps(result, indent=2))

                db = SessionLocal()

                try:
                    db_job = db.get(Job, job["job_id"])

                    if db_job:
                        db_job.status = "COMPLETED"
                        db_job.result = json.dumps(result)
                        db_job.error = None
                        db.commit()
                finally:
                    db.close()

        else:
            raise ValueError(
                f"Unknown job type: {job['type']}"
            )

        ch.basic_ack(
            delivery_tag=method.delivery_tag
        )
    
    except Exception as error:
        print(f"Job failed: {error}")

        retry_count = get_retry_count(properties)

        print(
            f"Retry count: {retry_count}/{MAX_RETRIES}"
        )

        if retry_count < MAX_RETRIES:
            next_retry = retry_count + 1

            print(
                f"Scheduling retry {next_retry}/{MAX_RETRIES}"
            )

            ch.basic_publish(
                exchange="",
                routing_key=RETRY_QUEUE,
                body=body,
                properties=pika.BasicProperties(
                    delivery_mode=pika.DeliveryMode.Persistent,
                    headers={
                        "x-retry-count": next_retry
                    }
                )
            )

            db = SessionLocal()

            try:
                db_job = db.get(Job, job["job_id"])

                if db_job:
                    db_job.status = "RETRYING"
                    db_job.error = str(error)
                    db.commit()
            finally:
                db.close()

        else:
            print(
                f"Max retries reached. Sending job to DLQ"
            )

            ch.basic_publish(
                exchange=DLX_NAME,
                routing_key="failed",
                body=body,
                properties=pika.BasicProperties(
                    delivery_mode=pika.DeliveryMode.Persistent,
                    headers={
                        "x-retry-count": retry_count
                    }
                )
            )

            db = SessionLocal()

            try:
                db_job = db.get(Job, job["job_id"])

                if db_job:
                    db_job.status = "FAILED"
                    db_job.error = str(error)
                    db.commit()
            finally:
                db.close()

        ch.basic_ack(
            delivery_tag=method.delivery_tag,
        )

def get_retry_count(properties):
    headers = properties.headers or {}
    return int(headers.get("x-retry-count", 0))

credentials = pika.PlainCredentials(
    RABBITMQ_USER,
    RABBITMQ_PASSWORD
)

connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        credentials=credentials
    )
)

channel = connection.channel()

channel.exchange_declare(
    exchange=DLX_NAME,
    exchange_type="direct",
    durable=True
)

channel.queue_declare(
    queue=QUEUE_NAME,
    durable=True
)

channel.queue_declare(
    queue=RETRY_QUEUE,
    durable=True,
    arguments={
        "x-message-ttl": 10000,
        "x-dead-letter-exchange": "",
        "x-dead-letter-routing-key": QUEUE_NAME
    }
)

channel.queue_declare(
    queue=DLQ_NAME,
    durable=True
)

channel.queue_bind(
    exchange=DLX_NAME,
    queue=DLQ_NAME,
    routing_key="failed"
)

channel.basic_qos(prefetch_count=1)

channel.basic_consume(
    queue=QUEUE_NAME,
    on_message_callback=process_job
)

print("Worker waiting for blockchain jobs...")

channel.start_consuming()