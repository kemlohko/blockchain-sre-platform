import json
import os
import uuid
import time

import pika
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from database import Job, SessionLocal, create_tables
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

class TransactionRequest(BaseModel):
    tx_hash: str


app = FastAPI(
    title="Blockchain SRE Platform",
    version="0.1.0"
)

@app.on_event("startup")
def startup():
    create_tables()

@app.middleware("http")
async def prometheus_middleware(request, call_next):
    start_time = time.perf_counter()

    response = await call_next(request)

    duration = time.perf_counter() - start_time

    route = request.scope.get("route")

    if route:
        endpoint = route.path
    else:
        endpoint = request.url.path

    HTTP_REQUESTS.labels(
        method=request.method,
        endpoint=endpoint,
        status=response.status_code
    ).inc()

    HTTP_REQUEST_DURATION.labels(
        method=request.method,
        endpoint=endpoint
    ).observe(duration)

    return response

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "admin")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "admin")

QUEUE_NAME = "blockchain_jobs"

HTTP_REQUESTS = Counter(
    "blockchain_api_http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status"]
)

HTTP_REQUEST_DURATION = Histogram(
    "blochain_api_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"]
)

JOBS_SUBMITTED = Counter(
    "blockchain_jobs_submitted_total",
    "Total number of blockchain analysis jobs submitted",
    ["type"]
)

def get_rabbitmq_connection():
    credentials = pika.PlainCredentials(
        RABBITMQ_USER,
        RABBITMQ_PASSWORD
    )

    return pika.BlockingConnection(
        pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            credentials=credentials
        )
    )

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }

@app.post("/jobs")
def create_jobs():
    job = {
        "job_id": str(uuid.uuid4()),
        "type": "demo",
        "message": "Hello from FastApi"
    }

    connection = get_rabbitmq_connection()
    channel = connection.channel()

    channel.queue_declare(
        queue=QUEUE_NAME,
        durable=True
    )

    channel.basic_publish(
        exchange="",
        routing_key=QUEUE_NAME,
        body=json.dumps(job),
        properties=pika.BasicProperties(
            delivery_mode=pika.DeliveryMode.Persistent
        )
    )

    connection.close()

    return {
        "status": "queued",
        "job": job
    }

@app.post("/transaction/analyze")
def analyze_transaction(request: TransactionRequest):

    job_id = str(uuid.uuid4())

    job = {
        "job_id": job_id,
        "type": "transaction_analysis",
        "network": "ethereum",
        "tx_hash": request.tx_hash
    }

    connection = get_rabbitmq_connection()
    channel = connection.channel()

    channel.queue_declare(
        queue=QUEUE_NAME,
        durable=True
    )

    db = SessionLocal()

    try:
        db_job = Job(
            id=job_id,
            type="transaction_analysis",
            tx_hash=request.tx_hash,
            status="QUEUED"
        )

        db.add(db_job)
        db.commit()

    finally:
        db.close()

    channel.basic_publish(
        exchange="",
        routing_key=QUEUE_NAME,
        body=json.dumps(job),
        properties=pika.BasicProperties(
            delivery_mode=pika.DeliveryMode.Persistent
        )
    )

    JOBS_SUBMITTED.labels(
        type="transaction_analysis"
    ).inc()

    connection.close()

    return {
        "status": "queued",
        "job": job
    }

@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    db = SessionLocal()

    try:
        job = db.get(Job, job_id)

        if job is None:
            raise HTTPException(
                status_code=404,
                detail="Job not found"
            )
        
        response = {
            "job_id": job.id,
            "type": job.type,
            "tx_hash": job.tx_hash,
            "status": job.status,
            "error": job.error
        }

        if job.result: 
            response["result"] = json.loads(job.result)

        return response
    
    finally:
        db.close()

@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )