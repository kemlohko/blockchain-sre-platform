# Blockchain SRE Platform

A production-oriented Site Reliability Engineering project for operating Ethereum infrastructure and a distributed blockchain application.

The project combines:

- Ethereum execution and consensus clients
- Linux/systemd operations
- Infrastructure as Code
- Configuration management
- Secure monitoring connectivity
- Prometheus and Grafana observability
- Alerting and operational runbooks
- FastAPI
- RabbitMQ
- PostgreSQL
- Asynchronous workers
- Application metrics
- Kubernetes/GKE
- GitOps
- Centralized logging
- Distributed tracing
- SLI/SLO engineering
- Failure simulation and recovery

The goal is not simply to run an Ethereum node or deploy an API. The goal is to build and operate a small production-like platform using SRE practices.

---

# Architecture

The platform intentionally separates stateful blockchain infrastructure from stateless application workloads.

```text
                         ┌──────────────────────────────┐
                         │     Application Platform     │
                         │                              │
Client ────────────────► │ FastAPI                      │
                         │    │                         │
                         │    ▼                         │
                         │ RabbitMQ                     │
                         │    │                         │
                         │    ▼                         │
                         │ Worker                      │
                         │    │                         │
                         │    ├────────► PostgreSQL     │
                         │    │                         │
                         └────┼─────────────────────────┘
                              │
                              │ Ethereum JSON-RPC
                              ▼
                  ┌───────────────────────────────┐
                  │      Ethereum Node            │
                  │                               │
                  │ Geth Execution Client         │
                  │ Lighthouse Consensus Client   │
                  │                               │
                  │ systemd + persistent storage  │
                  └───────────────┬───────────────┘
                                  │
                                  │ metrics
                                  │ WireGuard
                                  ▼
                  ┌───────────────────────────────┐
                  │      Monitoring VM            │
                  │                               │
                  │ Prometheus                    │
                  │ Grafana                       │
                  │ Alertmanager                  │
                  └───────────────────────────────┘
```

The Ethereum execution and consensus clients run on a dedicated VM with persistent disks and systemd because they are stateful and I/O-intensive infrastructure workloads.

Stateless APIs and asynchronous workers are containerized and are intended to run on Kubernetes, where horizontal scaling and self-healing provide more value.

---

# Current Infrastructure

## Ethereum node

Network:

```text
Ethereum Sepolia
```

Execution client:

```text
Geth v1.17.4
```

Consensus client:

```text
Lighthouse v8.2.2
```

Both clients are fully synchronized.

### Storage

The node uses separate storage for the main filesystem and Geth ancient data.

```text
Root filesystem
└── /var/lib/ethereum/geth

Dedicated ancient volume
└── /mnt/ethereum-ancient
```

Geth is configured with:

```text
--datadir /var/lib/ethereum/geth
--datadir.ancient /mnt/ethereum-ancient
--history.chain=postmerge
```

The dedicated ancient volume is mounted by UUID and validated by Ansible before Geth starts.

The systemd service uses:

```text
RequiresMountsFor=/mnt/ethereum-ancient
```

to prevent Geth from starting before the persistent volume is available.

---

# Ethereum Interfaces

## Geth JSON-RPC

```text
127.0.0.1:8545
```

Enabled namespaces:

```text
eth
net
web3
```

The JSON-RPC interface is intentionally bound to localhost rather than exposed publicly.

## Engine API

```text
127.0.0.1:8551
```

Used by Lighthouse to communicate with Geth.

## Lighthouse HTTP API

```text
127.0.0.1:5052
```

## Metrics

Metrics are exposed only through the private WireGuard network.

```text
node_exporter    10.10.0.2:9100
Geth             10.10.0.2:6060
Lighthouse       10.10.0.2:5054
```

---

# Infrastructure Automation

## Terraform

Terraform provisions the monitoring infrastructure in Google Cloud.

Current monitoring resources include:

- custom VPC
- monitoring subnet
- firewall rules
- static public IP
- Ubuntu monitoring VM
- persistent boot disk

The monitoring VM runs in:

```text
europe-west3
```

Terraform state, provider binaries, credentials, private keys, and other generated files must not be committed to Git.

`.terraform.lock.hcl` should remain tracked.

---

# Configuration Management

Ansible manages the Ethereum node and monitoring infrastructure.

Example structure:

```text
ansible/
├── ethereum-data-migration.yml
├── inventory/
│   └── hosts.ini
├── monitoring.yml
├── site.yaml
└── roles/
    ├── ethereum_node/
    └── monitoring/
```

Responsibilities include:

- Geth configuration
- Lighthouse configuration
- systemd services
- persistent storage validation
- node_exporter
- Prometheus
- Grafana
- Alertmanager
- Prometheus alert rules
- Grafana dashboard provisioning

Storage automation deliberately validates existing filesystems rather than formatting disks automatically.

Never add destructive filesystem operations such as blind `mkfs` execution to the live Ethereum data volume.

---

# Secure Monitoring Network

The Ethereum node and monitoring VM communicate over WireGuard.

```text
Monitoring VM
10.10.0.1
      │
      │ WireGuard
      │
10.10.0.2
Ethereum node
```

This allows Prometheus to scrape Ethereum infrastructure metrics without exposing monitoring endpoints publicly.

Ethereum JSON-RPC remains bound to localhost.

---

# Observability

## Prometheus

Prometheus collects metrics from:

```text
node_exporter
Geth
Lighthouse
Prometheus
```

Application monitoring is also being developed for:

```text
FastAPI
Worker
RabbitMQ
```

## Grafana

Grafana is provisioned through Ansible.

The Ethereum dashboard currently includes:

- Geth availability
- Lighthouse availability
- node exporter availability
- execution sync state
- consensus sync state
- Geth peer count
- Lighthouse peer count
- execution head block
- beacon head slot
- finalized epoch
- optimistic sync state
- CPU usage
- memory usage
- root filesystem usage
- ancient filesystem usage
- network activity

Grafana and Prometheus are not exposed publicly.

Access is performed using SSH port forwarding.

---

# Alerting

Prometheus currently contains eight Ethereum infrastructure alert rules.

```text
EthereumNodeExporterDown
GethDown
LighthouseDown
ConsensusNotSynced
RootDiskUsageHigh
AncientDiskUsageHigh
GethPeerCountLow
LighthousePeerCountLow
```

All eight rules have been successfully loaded and validated by Prometheus.

Healthy state:

```text
EthereumNodeExporterDown    inactive    ok
GethDown                    inactive    ok
LighthouseDown              inactive    ok
ConsensusNotSynced          inactive    ok
RootDiskUsageHigh           inactive    ok
AncientDiskUsageHigh        inactive    ok
GethPeerCountLow            inactive    ok
LighthousePeerCountLow      inactive    ok
```

A controlled Geth outage was used to validate the alert path.

Stopping Geth also caused Lighthouse to become unavailable because of the execution-client dependency.

Alertmanager inhibition should therefore be used to suppress redundant Lighthouse notifications when Geth is already known to be unavailable.

External Alertmanager notification delivery has intentionally been deferred.

---

# Runbooks

Operational runbooks are stored under:

```text
docs/runbooks/
```

Current runbooks include:

```text
ethereum-node-down.md
geth-service-down.md
lighthouse-service-down.md
lighthouse-not-syncing.md
high-disk-usage.md
geth-low-peer-count.md
lighthouse-low-peer-count.md
ancient-volume-not-mounted.md
```

Prometheus alerts link directly to the relevant runbooks.

---

# Storage Incident and Recovery

During Ethereum synchronization, the root filesystem reached approximately 96% utilization.

Investigation showed that Geth's ancient chain data dominated disk usage.

A supported history pruning operation was attempted:

```bash
geth \
  --datadir /var/lib/ethereum/geth \
  --history.chain=postmerge \
  prune-history
```

This removed pre-Merge historical data but did not recover enough space because post-Merge history remained large.

A dedicated 1 TB block-storage volume was therefore attached and mounted at:

```text
/mnt/ethereum-ancient
```

Geth ancient data was migrated to the new filesystem and verified before the original copy was removed.

An important discovery during the migration was that:

```text
--datadir.ancient
```

must point to the ancient-data root containing both:

```text
chain/
state/
```

rather than only the `chain/` directory.

After migration:

- Geth successfully opened the new ancient database
- Lighthouse caught up
- both clients returned to synchronized state
- root filesystem utilization dropped substantially

The incident is useful as a practical example of capacity planning, stateful workload recovery, safe data migration, and operational validation.

Never manually delete Geth freezer `.cdat`, `.cidx`, or `.meta` files.

---

# Application Layer

The application implements asynchronous Ethereum transaction analysis.

Current services:

```text
FastAPI
RabbitMQ
Worker
PostgreSQL
Prometheus
Grafana
```

## Workflow

```text
POST /transaction/analyze
        │
        ▼
FastAPI
        │
        ├──── PostgreSQL
        │       QUEUED
        │
        ▼
RabbitMQ
        │
        ▼
Worker
        │
        ├──── PostgreSQL
        │       PROCESSING
        │
        ▼
Ethereum JSON-RPC
eth_getTransactionByHash
        │
        ▼
Worker
        │
        ├──── success ──► COMPLETED
        │
        └──── failure ──► RETRYING
                              │
                              ▼
                         Retry Queue
                              │
                              ▼
                         Main Queue
                              │
                         max retries
                              ▼
                             DLQ
                              │
                              ▼
                            FAILED
```

The job state can be queried with:

```text
GET /jobs/{job_id}
```

Current states:

```text
QUEUED
PROCESSING
RETRYING
COMPLETED
FAILED
```

---

# RabbitMQ Reliability

The worker currently implements:

- durable main queue
- persistent messages
- manual acknowledgements
- `prefetch_count=1`
- retry queue
- retry counter
- delayed retry using message TTL
- dead-letter exchange
- dead-letter queue
- maximum retry count
- failure persistence in PostgreSQL

Current retry delay:

```text
10 seconds
```

Maximum retries:

```text
3
```

---

# Application Metrics

FastAPI Prometheus instrumentation has been implemented.

Current API metrics include:

```text
blockchain_api_http_requests_total
blockchain_api_http_request_duration_seconds
blockchain_jobs_submitted_total
```

Prometheus successfully scrapes:

```text
api:8000/metrics
```

The complete path has been verified:

```text
FastAPI
   ↓
/metrics
   ↓
Prometheus
   ↓
PromQL
```

Example:

```promql
blockchain_api_http_requests_total{endpoint="/health"}
```

Worker Prometheus instrumentation has also been started.

The worker exposes metrics on:

```text
worker:8001
```

Planned/current worker metrics:

```text
blockchain_worker_jobs_total
blockchain_worker_retries_total
blockchain_worker_job_duration_seconds
blockchain_ethereum_rpc_duration_seconds
```

The worker metrics HTTP server starts successfully.

---

# Local Development

Start the stack:

```bash
docker compose up -d --build
```

Check services:

```bash
docker compose ps
```

API:

```text
http://localhost:8000
```

FastAPI documentation:

```text
http://localhost:8000/docs
```

RabbitMQ management:

```text
http://localhost:15672
```

Prometheus:

```text
http://localhost:9090
```

Grafana:

```text
http://localhost:3000
```

Do not use development credentials from Docker Compose in production.

---

# Remaining Work

The following work is intentionally unfinished.

## 1. Finish worker metrics

Add the worker scrape target to Prometheus:

```yaml
- job_name: "blockchain-worker"
  static_configs:
    - targets:
        - "worker:8001"
```

Verify:

```promql
up{job="blockchain-worker"}
```

Then process a real Sepolia transaction and verify:

```promql
blockchain_worker_jobs_total
blockchain_worker_retries_total
blockchain_ethereum_rpc_duration_seconds_count
```

Refactor job-duration measurement so it uses `try/finally` and records both successful and failed attempts.

---

## 2. RabbitMQ metrics

Prometheus should scrape RabbitMQ's Prometheus endpoint.

Monitor:

- queue depth
- consumers
- message publish rate
- message delivery rate
- unacknowledged messages
- retry queue
- dead-letter queue

---

## 3. Application Grafana Dashboard

Create a dashboard containing:

- API request rate
- API error rate
- API latency
- submitted jobs
- completed jobs
- failed jobs
- retry rate
- worker processing latency
- Ethereum RPC latency
- RabbitMQ queue depth
- DLQ depth

Provision the dashboard as code rather than creating it only through the Grafana UI.

---

## 4. Improve Application Reliability

Important reliability work remains.

### RabbitMQ reconnect handling

The API and worker should recover cleanly from temporary RabbitMQ outages.

### RPC error classification

Differentiate transient failures from permanent failures.

For example:

```text
timeout / HTTP 5xx
    → retry

temporary network failure
    → retry

invalid job
    → fail without unnecessary retries
```

### Database/message consistency

The API currently writes:

```text
QUEUED → PostgreSQL
```

before publishing the RabbitMQ message.

If publishing fails after the database commit, a job could remain permanently `QUEUED` even though no RabbitMQ message exists.

Investigate the **Transactional Outbox Pattern** as a later reliability improvement.

### Worker idempotency

Ensure duplicate RabbitMQ deliveries cannot produce incorrect state or duplicate side effects.

---

## 5. Alertmanager Notifications

Configure a real notification receiver.

Possible receivers:

- email
- Slack
- Discord/webhook

Secrets must not be stored directly in Git.

Use an appropriate secret-management mechanism such as Ansible Vault or environment-specific secret injection.

Also implement/test alert inhibition for cascading execution/consensus failures.

---

## 6. Security Review

Review and restrict:

- GCP SSH firewall sources
- WireGuard firewall sources
- netcup host firewall
- Ethereum P2P ports
- monitoring endpoints
- Docker credentials
- application secrets

Metrics should remain private.

Ethereum JSON-RPC must not be exposed directly to the public Internet.

---

## 7. Scale Workers

Run multiple workers:

```text
RabbitMQ
   │
   ├── Worker 1
   ├── Worker 2
   └── Worker 3
```

Validate competing-consumer behavior and observe workload distribution.

This prepares the application for Kubernetes.

---

## 8. Kubernetes / GKE

Deploy the stateless application layer to Kubernetes.

Target workloads:

```text
FastAPI
Workers
```

Keep the Ethereum execution and consensus clients on dedicated persistent infrastructure.

Use:

- Terraform for GKE infrastructure
- Kubernetes Deployments
- Services
- ConfigMaps
- Secrets
- health probes
- resource requests/limits
- Horizontal Pod Autoscaling where appropriate

---

## 9. Helm

Package application Kubernetes resources using Helm.

Separate:

```text
templates
configuration
environment-specific values
```

---

## 10. GitOps with Argo CD

Deploy the Kubernetes application through GitOps.

Target flow:

```text
Git
 ↓
Argo CD
 ↓
Kubernetes
```

Avoid manual production deployments with `kubectl apply`.

---

## 11. Centralized Logging

Introduce Loki.

Collect logs from:

- FastAPI
- workers
- Kubernetes workloads
- potentially Ethereum infrastructure

Correlate logs with:

```text
job_id
```

Avoid using high-cardinality identifiers such as transaction hashes as Prometheus labels; those identifiers are better suited to logs and traces.

---

## 12. Distributed Tracing

Instrument the application using OpenTelemetry.

Use Tempo as the tracing backend.

Target trace:

```text
FastAPI
   ↓
RabbitMQ
   ↓
Worker
   ↓
Ethereum JSON-RPC
   ↓
PostgreSQL
```

Propagate trace context through RabbitMQ message headers.

This should allow a single transaction-analysis request to be followed across the entire asynchronous workflow.

---

## 13. SLI / SLO Engineering

Define application SLIs such as:

### Job success rate

```text
completed jobs / terminal jobs
```

### Job processing latency

Measure:

```text
QUEUED → COMPLETED
```

rather than only HTTP request latency.

### API availability

Measure successful API requests relative to valid requests.

Then define explicit SLOs and alerting based on user-visible reliability.

---

## 14. High Availability

Introduce a second Ethereum node.

Design application-side RPC failover:

```text
Application
    │
    ├──── Ethereum Node A
    │
    └──── Ethereum Node B
```

Test failure scenarios rather than assuming failover works.

---

## 15. Incident Simulation

Perform controlled incidents such as:

- stop Geth
- stop Lighthouse
- stop worker
- stop RabbitMQ
- terminate an API pod
- make Ethereum RPC unavailable
- simulate PostgreSQL connectivity loss

For each incident record:

```text
Detection
Impact
Alert
Diagnosis
Runbook
Recovery
MTTR
Preventive action
```

Avoid destructive disk-full simulations on the live Ethereum node.

---

## 16. Postmortems

Document important incidents, particularly the Ethereum storage exhaustion and ancient-data migration.

A postmortem should cover:

```text
Summary
Impact
Timeline
Root cause
Detection
Response
Recovery
What went well
What went poorly
Corrective actions
```

---

# Long-Term Architecture

The intended final platform is:

```text
                     ┌─────────────────────┐
                     │       Users         │
                     └──────────┬──────────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │      FastAPI        │
                     │        GKE          │
                     └──────────┬──────────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │      RabbitMQ       │
                     └──────────┬──────────┘
                                │
                     ┌──────────┴──────────┐
                     ▼                     ▼
                  Worker                Worker
                     │                     │
                     └──────────┬──────────┘
                                │
                   ┌────────────┴────────────┐
                   ▼                         ▼
              PostgreSQL              Ethereum RPC
                                           │
                                  ┌────────┴────────┐
                                  ▼                 ▼
                              Node A             Node B

Observability
────────────────────────────────────────────

Prometheus ──► Grafana
Alertmanager ──► Notifications
Loki ────────► Logs
OpenTelemetry ──► Tempo ──► Traces
```

---

# Resume Point

When development resumes, **do not rebuild the application or monitoring stack**.

Start here:

1. Start Docker Compose.
2. Confirm API and worker are healthy.
3. Add `worker:8001` to Prometheus.
4. Verify `up{job="blockchain-worker"} == 1`.
5. Submit a real Sepolia transaction-analysis job.
6. Verify the job reaches `COMPLETED`.
7. Verify worker and Ethereum RPC metrics.
8. Add RabbitMQ metrics.
9. Build the application Grafana dashboard.
10. Continue with reliability improvements before Kubernetes.

The immediate next technical milestone is:

```text
Complete application observability
        ↓
Application Grafana dashboard
        ↓
Reliability improvements
        ↓
Kubernetes / GKE
```

---

# Engineering Principles

This project follows several operating principles:

- automate repeatable infrastructure changes
- treat stateful workloads differently from stateless workloads
- validate storage before modifying it
- never expose unnecessary management interfaces publicly
- observe systems before attempting to scale them
- use metrics for aggregation, logs for context, and traces for request flow
- create alerts that lead to actionable runbooks
- test failure and recovery paths
- avoid committing credentials or generated infrastructure artifacts
- prefer reproducible configuration over manual server changes
- treat monitoring and instrumentation code as production code