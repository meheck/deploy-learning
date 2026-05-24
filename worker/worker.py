import json
import logging
import os

import psycopg2
import redis
from textblob import TextBlob

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

POSTGRES_DSN = os.environ["POSTGRES_DSN"]
REDIS_URL = os.environ["REDIS_URL"]
QUEUE_KEY = "jobs:queue"

def get_db():
    return psycopg2.connect(POSTGRES_DSN)

def run_inference(text: str) -> dict:
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    return {"polarity": round(polarity, 4), "label": "positive" if polarity > 0.1 else "negative" if polarity < -0.1 else "neutral"}

def process_job(job_id: str, text: str):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE jobs SET status = %s WHERE id = %s",
            ("running", job_id)
        )
        conn.commit()
        result = run_inference(text)
        cur.execute(
            "UPDATE jobs SET status = %s, output = %s WHERE id = %s",
            ("complete", json.dumps(result), job_id)
        )
    conn.commit()
    conn.close()

def main():
    r = redis.from_url(REDIS_URL)
    log.info("Worker started, waiting for jobs...")
    while True:
        try:
            r = redis.from_url(REDIS_URL)
            log.info("Worker started, waiting for jobs...")
            while True:
                result = r.blpop(QUEUE_KEY, timeout=5)
                if result is None:
                    continue
                _, raw = result
                job = json.loads(raw)
                process_job(job["job_id"], job["text"])
        except Exception as e:
            log.error("Worker error: %s — reconnecting in 3s", e)
            import time; time.sleep(3)

if __name__ == "__main__":
    main()
