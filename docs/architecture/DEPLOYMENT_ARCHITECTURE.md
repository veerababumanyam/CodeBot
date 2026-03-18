# CodeBot Deployment Architecture

**Version:** 2.5
**Date:** 2026-03-18
**Status:** Planning

## 1. Deployment Topologies

### 1.1 Local Development (Single Machine)

```
┌─────────────────────────────────────────────────────────┐
│                    Developer Machine                      │
│                                                           │
│  ┌─────────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │  CodeBot     │  │ SQLite   │  │ LanceDB          │   │
│  │  Backend     │  │ (data)   │  │ (vectors)        │   │
│  │  (FastAPI)   │  └──────────┘  └──────────────────┘   │
│  └──────┬──────┘                                         │
│         │         ┌──────────┐  ┌──────────────────┐     │
│  ┌──────┴──────┐  │ In-memory│  │ Nsjail           │   │
│  │  Dashboard   │  │ Event Bus│  │ (sandbox)        │   │
│  │  (Vite dev)  │  └──────────┘  └──────────────────┘   │
│  └─────────────┘                                         │
│                                                           │
│  No external services required. Everything runs in-process│
└─────────────────────────────────────────────────────────┘
```

**Requirements:** Python 3.12+, Node.js 20+, Git 2.40+
**Start command:** `codebot dev`

### 1.2 Docker Compose (Team Development / CI)

```
┌─────────────────────────────────────────────────────┐
│                  Docker Compose Stack                 │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ codebot  │  │ postgres │  │ nats             │  │
│  │ (backend)│  │ :5432    │  │ :4222 (client)   │  │
│  │ :8000    │  │          │  │ :8222 (monitor)  │  │
│  └──────────┘  └──────────┘  └──────────────────┘  │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ dashboard│  │ redis    │  │ lancedb          │  │
│  │ (frontend│  │ :6379    │  │ (volume mount)   │  │
│  │ :3000    │  │          │  │                  │  │
│  └──────────┘  └──────────┘  └──────────────────┘  │
│                                                      │
│  ┌──────────┐  ┌──────────┐                         │
│  │ langfuse │  │ signoz   │                         │
│  │ :3001    │  │ :3301    │                         │
│  └──────────┘  └──────────┘                         │
└─────────────────────────────────────────────────────┘
```

### 1.3 Production (Kubernetes)

```
┌─────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                      │
│                                                           │
│  ┌─────────────────────────────────────────────────┐     │
│  │ Namespace: codebot                                │     │
│  │                                                   │     │
│  │  Deployments:                                     │     │
│  │  ├── codebot-api (3 replicas, HPA)               │     │
│  │  ├── codebot-worker (5 replicas, HPA)            │     │
│  │  ├── codebot-dashboard (2 replicas)               │     │
│  │  └── codebot-scheduler (1 replica)                │     │
│  │                                                   │     │
│  │  StatefulSets:                                    │     │
│  │  ├── postgresql (1 primary + 2 replicas)          │     │
│  │  ├── nats (3 nodes, JetStream cluster)            │     │
│  │  ├── redis (3 nodes, Sentinel)                    │     │
│  │  └── qdrant (3 nodes, distributed)                │     │
│  │                                                   │     │
│  │  External Services:                               │     │
│  │  ├── LiteLLM Proxy (Deployment, 2 replicas)       │     │
│  │  ├── Langfuse (Deployment + ClickHouse)            │     │
│  │  ├── SigNoz (Helm chart)                           │     │
│  │  └── E2B (external managed service)                │     │
│  └─────────────────────────────────────────────────┘     │
│                                                           │
│  Ingress: NGINX / Traefik with TLS termination           │
│  Secrets: Kubernetes Secrets + external-secrets-operator  │
│  Storage: PVCs with dynamic provisioning                  │
└─────────────────────────────────────────────────────────┘
```

## 2. Infrastructure as Code

| Component | Tool | Description |
|-----------|------|-------------|
| Cloud resources | Pulumi (Python) | VPC, databases, storage, IAM |
| Kubernetes manifests | Helm charts | Application deployment |
| CI/CD pipelines | Dagger (Python) | Build, test, deploy pipelines |
| Local development | Docker Compose | Full stack for local dev |

## 3. Scaling Strategy

| Component | Scaling Type | Trigger |
|-----------|-------------|---------|
| API server | Horizontal (HPA) | CPU > 70% or request latency > 500ms |
| Agent workers | Horizontal (HPA) | Queue depth > 10 per worker |
| Dashboard | Horizontal | Request count |
| PostgreSQL | Vertical + read replicas | Connection count, query latency |
| NATS | Horizontal (cluster) | Message throughput |
| Qdrant | Horizontal (sharding) | Vector count > 10M per node |
| Redis | Sentinel → Cluster | Memory usage > 80% |

## 4. High Availability

| Component | HA Strategy | RPO | RTO |
|-----------|------------|-----|-----|
| PostgreSQL | Streaming replication + pgBouncer | 0 (sync) | < 30s (auto-failover) |
| NATS | JetStream R3 replication | 0 | < 5s |
| Redis | Sentinel with 3 nodes | ~1s | < 15s |
| Qdrant | Raft-based replication | 0 | < 10s |
| API/Workers | Multiple replicas behind LB | N/A | 0 (rolling) |

## 5. Backup Strategy

| Data | Method | Frequency | Retention |
|------|--------|-----------|-----------|
| PostgreSQL | pg_dump + WAL archiving | Continuous WAL, daily full | 30 days |
| Vector indexes | LanceDB/Qdrant snapshots | Daily | 7 days |
| Configuration | Git (version controlled) | On change | Indefinite |
| Secrets | Encrypted backup to object storage | Daily | 90 days |

---

*CodeBot v2.5 deployment architecture planning document*
