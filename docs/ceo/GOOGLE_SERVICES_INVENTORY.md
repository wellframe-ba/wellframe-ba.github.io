# Google Cloud Services Inventory: System Blueprint & Costs
**Prepared by:** Sovereign Agent (Antigravity CEO)  
**Target:** Google Cloud Platform (GCP) Resource Audit  
**Timestamp:** May 17, 2026

---

## 📋 1. The Service Inventory: 7 Core Services

If we execute this architecture, we will be using exactly **7 Core Google Services** for our application flow, plus **3 Supporting Services** that handle deployment, security, and logging behind the scenes.

Here is the precise breakdown of the services, their roles, and how they charge.

---

## 🚀 2. The Core Stack (The Flow)

### 1. Google Cloud Run (Services & Jobs)
*   **Role:** Computes our stateless backend API, hosts the frontend dashboard, and runs our long-running autonomous agent swarms.
*   **Scale Behavior:** Serverless. Instantly scales to match traffic; scales to 0 instances when idle.
*   **Cost Profile:** **Pay-per-millisecond** of actual container execution. The first 180,000 vCPU-seconds and 360,000 GiB-seconds per month are free.

### 2. Firebase Authentication / Google Cloud Identity Platform
*   **Role:** Manages user signups, secure logins, password resets, and session tokens.
*   **Scale Behavior:** Serverless. Handles millions of concurrent user sessions without intervention.
*   **Cost Profile:** **Free** for all standard email/password logins and up to **3,000 Monthly Active Users (MAUs)**.

### 3. Google Cloud SQL (PostgreSQL)
*   **Role:** Holds our actual application databases (relational profile data, organization logs, user permissions, and compliance matrices).
*   **Scale Behavior:** Managed. You select your instance size (e.g., db-f1-micro for dev or db-custom-1-3840 for prod). It handles automated backups, replica creation, and scale-ups.
*   **Cost Profile:** **Continuous/Hourly Billed**. Unlike Cloud Run, the DB runs 24/7. A small dev database (db-f1-micro) costs roughly **$9/month**, while a highly resilient production instance costs **$40–$100/month**.

### 4. Google Cloud Tasks
*   **Role:** Buffers incoming requests and schedules long-running swarm analyses. Instead of making the frontend wait, Cloud Tasks schedules execution queues.
*   **Scale Behavior:** Serverless. Automatically queues thousands of parallel executions.
*   **Cost Profile:** **Extremely cheap**. First 1 million task executions per month are **completely free**, then $0.40 per million thereafter.

### 5. Google Cloud Storage (GCS)
*   **Role:** Stores our raw assets: uploaded P&ID engineering drawings, temporary JSON manifests, safety templates, and compiled compliance reports.
*   **Scale Behavior:** Serverless. Unlimited storage capacity.
*   **Cost Profile:** **Pay-for-volume**. The first 5 GB per month is **free**, then roughly **$0.02 per GB** per month.

### 6. Google Cloud Secret Manager
*   **Role:** Securely stores API credentials (e.g. Claude API Keys, MiniMax keys, Slack Webhook URLs). Cloud Run accesses these secrets dynamically at boot time without saving them in the codebase.
*   **Scale Behavior:** Serverless.
*   **Cost Profile:** **Practically free**. $0.06 per active secret version per month.

### 7. Google Cloud VPC & Serverless VPC Access Connector
*   **Role:** Restricts database traffic to private IP spaces. The Cloud Run container communicates with PostgreSQL securely on Google’s internal network without exposing the database to the public internet.
*   **Scale Behavior:** Serverless bridge.
*   **Cost Profile:** The Serverless VPC Connector costs a minimal flat charge of **~$15/month** (running as a tiny router between the serverless ecosystem and your private network).

---

## 🛠️ 3. Supporting Infrastructure (Behind the Scenes)

We use 3 supporting services that require no manual orchestration or coding:

*   **8. Google Artifact Registry:** Secure container repository. Our Docker images are pushed here during deployment, and Cloud Run pulls from it. *(First 500 MB free).*
*   **9. Google Cloud Logging & Monitoring:** Captures all terminal logs, print statements, and error stack traces from Cloud Run instantly. *(50 GB free ingestion per month).*
*   **10. Google Cloud IAM (Identity and Access Management):** Handles serverless permissions. It allows our Cloud Run service account to talk to PostgreSQL and Secret Manager without static passwords or API keys. *(100% Free).*

---

## 📊 4. Operational Cost Model Summary

For a startup, the bill is highly optimized because **90% of our infrastructure is Serverless (scales to zero when idle)**.

| Infrastructure State | Monthly Cost (Approx) | Notes |
| :--- | :--- | :--- |
| **Development / Zero Traffic** | **~$24 / month** | Billed only for the 24/7 Cloud SQL DB (`~$9`) + VPC Router (`~$15`). All other services scale to zero. |
| **Active Startup Stage (100 runs/day)** | **~$35 - $60 / month** | Minimal incremental charges for Cloud Run compute time, storage volume, and task orchestration. |
| **High Growth Enterprise Scale** | **~$150 - $400 / month** | Upgrade the PostgreSQL database capacity and allocate dedicated instance pools. |

*Strategic Decision:* By limiting 24/7 resources to just the database and private routing connector, we achieve institutional-grade scale at the price of a small lunch.
