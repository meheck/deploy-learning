# ML Inference Service — Learning Project

## Goal
Build a production-like ML inference system from scratch to learn Docker, networking, queues, databases, and deployment. The goal is to get good at infra so you can ship things independently.

## Architecture
```
Client
  ↓ POST /submit
FastAPI (port 8000)
  ↓ RPUSH
Redis queue (jobs:queue)
  ↓ BLPOP
Worker process
  ↓ TextBlob sentiment analysis
  ↓ UPDATE
PostgreSQL (mlqueue db)
```

## What's done

### Infrastructure
- `docker-compose.yml` — all 4 services defined (postgres, redis, api, worker)
- Named volume `postgres_data` for postgres persistence
- Bind mount `./db/init.sql` runs on first DB creation
- Bind mount `./api:/app` for hot reload during development

### Database (Postgres)
- Running on port 5432
- User: `mehak`, password: `password`, db: `mlqueue`
- `db/init.sql` creates the `jobs` table automatically on first start
- Schema: `id (UUID), status, input, output (JSONB), created_at`

### Queue (Redis)
- Running on port 6379
- Queue key: `jobs:queue`
- API does RPUSH, worker does BLPOP (FIFO)

### API (FastAPI)
- `api/main.py` — all three endpoints written and working
- `POST /submit` — creates job in postgres, pushes to redis, returns job_id
- `GET /status/{job_id}` — returns current status from postgres
- `GET /results/{job_id}` — returns full result or 202 if not done
- `GET /health` — returns ok
- Dockerfile and requirements.txt done

### Worker
- `worker/worker.py` — written, BLPOP loop + process_job function
- Updates status to 'running', runs TextBlob sentiment, updates to 'complete'
- Dockerfile and requirements.txt done
- Added to docker-compose.yml

## What's NOT done yet (pick up here)

### Phase 2 — Ship to a real server
1. Push project to GitHub
2. Get a cloud VM (DigitalOcean Droplet recommended)
3. SSH in, install Docker, clone repo, run `docker compose up`
4. Configure restart policies so containers survive reboots
5. Put nginx in front as a reverse proxy (port 80/443 instead of 8000)
6. Add SSL certificate (HTTPS)
7. Set up GitHub Actions for auto-deploy on push to main

## Key commands
```bash
docker compose up --build          # start everything, rebuild images
docker compose up --build -d       # same but detached (background)
docker compose logs -f worker      # stream worker logs
docker compose logs -f api         # stream api logs
docker compose exec postgres psql -U mehak -d mlqueue   # postgres shell
docker compose exec redis redis-cli                      # redis shell
docker compose down                # stop (data persists)
docker compose down -v             # stop + delete postgres volume
docker compose up --scale worker=3 # run 3 workers
```

## Test the full flow
```bash
# Submit a job
curl -s -X POST http://localhost:8000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "I love this!"}'

# Check status (use job_id from above)
curl -s http://localhost:8000/status/<job_id>

# Get results
curl -s http://localhost:8000/results/<job_id>

# Check DB directly
docker compose exec postgres psql -U mehak -d mlqueue -c "SELECT * FROM jobs;"
```

## Concepts covered so far
- Docker images vs containers
- Dockerfile layer caching (copy requirements before code)
- docker-compose services, ports, volumes, environment
- Named volumes vs bind mounts
- Container networking (service names as hostnames)
- BRPOP/RPUSH — how a Redis queue works
- Async job dispatch — API returns immediately, worker processes later
- psql CLI, \dt, \d tablename
- docker compose exec — running commands inside containers
- 0.0.0.0 vs 127.0.0.1 in containers
