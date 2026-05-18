# GCP Cloud Run + GCS Deployment

Deploys the Agentic Swarm Co. app using the **Ultra-Lean Stack**:
- **Cloud Run** — Single container with Pocketbase + Litestream + nginx
- **GCS Bucket** — Database replication and backup (scale-to-zero)

## Architecture

```
Client → Cloud Run (nginx + Pocketbase) → GCS (Litestream backup)
         └── 1 container, max 1 instance, $0/month idle
```

## Quick Start

### Prerequisites

```bash
# Install Google Cloud SDK
brew install google-cloud-sdk

# Authenticate
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID
```

### 1. Setup GCS Bucket

```bash
make setup-gcs
```

### 2. Deploy

```bash
# Full deployment (build + push + deploy)
make deploy-all

# Or step by step:
make docker-build
make push
make deploy
```

### 3. View Logs

```bash
make logs
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `LITESTREAM_BUCKET` | GCS bucket path (e.g. `gs://project-id-pocketbase/data.db`) |

## Local Development

```bash
make dev
```

This runs the same stack locally via Docker Compose.

## Configuration

Edit `Makefile` to adjust:
- `GCP_REGION` — deployment region (default: `us-central1`)
- `SERVICE_NAME` — Cloud Run service name
- `MIN_INSTANCES` / `MAX_INSTANCES` — scaling bounds
- `CONCURRENCY` — requests per instance

## Features

- **Scale to Zero**: `--min-instances 0` means no idle cost
- **Database Replication**: Litestream streams SQLite WAL to GCS in real-time
- **Static + API**: nginx serves frontend, proxies `/api/*` to Pocketbase