import json
import os
import uuid

import psycopg2
import psycopg2.extras
import redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

POSTGRES_DSN = os.environ["POSTGRES_DSN"]
REDIS_URL = os.environ["REDIS_URL"]
QUEUE_KEY = "jobs:queue"

def get_db():
    return psycopg2.connect(POSTGRES_DSN)

def get_redis():
    return redis.from_url(REDIS_URL)

class SubmitRequest(BaseModel):
    text: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/submit", status_code=202)
def submit_job(req: SubmitRequest):
    job_id = str(uuid.uuid4())
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO jobs (id, status, input) VALUES (%s, %s, %s)",
            (job_id, "pending", req.text)
        )
    conn.commit()
    conn.close()
    r = get_redis()
    r.rpush(QUEUE_KEY, json.dumps({"job_id": job_id, "text": req.text}))
    return {"job_id": job_id, "status": "pending"}


@app.get("/status/{job_id}")
def get_status(job_id: str):
    conn = get_db()
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "SELECT id, status, created_at, updated_at FROM jobs WHERE id = %s",
            (job_id,)
        )
        row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    return dict(row)


@app.get("/results/{job_id}")
def get_results(job_id: str):
    conn = get_db()
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM jobs WHERE id = %s", (job_id,))
        row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    if row["status"] in ("pending", "running"):
        raise HTTPException(status_code=202, detail=f"Job is {row['status']}")
    return dict(row)

@app.get("/metrics")
def get_metrics():
    conn = get_db()
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "SELECT status, COUNT(*) FROM jobs GROUP BY status"
        )
        rows = cur.fetchall()
    conn.close()
    r = get_redis()
    queue_depth = r.llen(QUEUE_KEY)
    return {
    "jobs_by_status": {row["status"]: row["count"] for row in rows},
    "queue_depth": queue_depth
    }
