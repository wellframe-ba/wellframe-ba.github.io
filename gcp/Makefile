# GCP Deployment Configuration
# ==============================
# This file defines the Cloud Run service configuration.

# Project & Region
GCP_PROJECT_ID:=$(shell gcloud config get-value project)
GCP_REGION:=us-central1

# App Identity
SERVICE_NAME:=agentic-swarm
IMAGE:=gcr.io/$(GCP_PROJECT_ID)/$(SERVICE_NAME)

# GCS Bucket for Litestream
LITESTREAM_BUCKET:=gs://$(GCP_PROJECT_ID)-pocketbase/data.db

# Cloud Run Settings
MIN_INSTANCES:=0
MAX_INSTANCES:=1
CONCURRENCY:=100
MEMORY:=1Gi
CPU:=1

# Pocketbase Admin (set via Secret Manager or env)
# PB_ADMIN_EMAIL:=admin@agenticswarm.ai
# PB_ADMIN_PASSWORD:=your-secure-password

.PHONY: deploy build docker-build setup-gcs

# Step 1: Setup GCS bucket for Litestream replication
setup-gcs:
	@echo "Creating GCS bucket for Litestream..."
	gcloud storage buckets create $(LITESTREAM_BUCKET) \
		--location=$(GCP_REGION) \
		--uniform-bucket-level-access
	@echo "GCS bucket ready: $(LITESTREAM_BUCKET)"

# Step 2: Build the Docker image
docker-build:
	@echo "Building Docker image..."
	docker build -t $(IMAGE):latest ./gcp
	docker tag $(IMAGE):latest $(IMAGE):$(shell git rev-parse --short HEAD)

# Step 3: Push to Artifact Registry
push:
	@echo "Pushing to Artifact Registry..."
	docker push $(IMAGE):latest
	docker push $(IMAGE):$(shell git rev-parse --short HEAD)

# Step 4: Deploy to Cloud Run
deploy:
	@echo "Deploying to Cloud Run..."
	gcloud run deploy $(SERVICE_NAME) \
		--image=$(IMAGE):latest \
		--region=$(GCP_REGION) \
		--min-instances=$(MIN_INSTANCES) \
		--max-instances=$(MAX_INSTANCES) \
		--concurrency=$(CONCURRENCY) \
		--memory=$(MEMORY) \
		--cpu=$(CPU) \
		--set-env-vars="LITESTREAM_BUCKET=$(LITESTREAM_BUCKET)" \
		--allow-unauthenticated

# Full deployment: build, push, deploy
deploy-all: docker-build push deploy

# Local development with Docker Compose
dev:
	docker compose -f gcp/docker-compose.yml up --build

# View logs
logs:
	gcloud run logs read $(SERVICE_NAME) --region=$(GCP_REGION) --tail=50