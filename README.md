# Async Job Processing Service

A production-like async job processing system built to learn Docker, networking, queues, databases, and deployment.

## What it does
Accepts text, runs sentiment analysis, returns results asynchronously.

## Architecture
```
Client
  ↓ POST /submit
FastAPI (port 80 via nginx)
  ↓ RPUSH
Redis queue (jobs:queue)
  ↓ BLPOP
Worker (TextBlob sentiment analysis)
  ↓ UPDATE
PostgreSQL (jobs table)
```

## Observability
- Prometheus scrapes `/metrics` every 15s
- Grafana dashboard shows request rate, queue depth, job counts

## What we learned
- Docker images, containers, Dockerfiles, layer caching
- Docker Compose: services, ports, volumes, networks, healthchecks
- Named volumes vs bind mounts
- Container networking (service names as hostnames)
- PostgreSQL: schema design, psql CLI, init scripts
- Redis: RPUSH/BLPOP, FIFO queue pattern
- Async job dispatch — API returns immediately, worker processes later
- Worker resilience: reconnect loop on failure
- AWS EC2: instance setup, security groups, SSH keys
- nginx as a reverse proxy
- Docker restart policies for production resilience
- GitHub Actions CI/CD — auto-deploy on push to main
- Prometheus metrics and Grafana dashboards
