# CodeBot API Specification

> **Version:** 2.5.0
> **Base URL:** `https://<host>/api/v1`
> **Protocol:** HTTPS (TLS 1.3)
> **Content-Type:** `application/json`
> **Date:** 2026-03-18

---

## Table of Contents

1. [API Overview](#1-api-overview)
2. [Authentication & Authorization API](#2-authentication--authorization-api)
3. [Project Management API](#3-project-management-api)
4. [Pipeline Management API](#4-pipeline-management-api)
5. [Agent Management API](#5-agent-management-api)
6. [Brainstorming API](#6-brainstorming-api)
7. [Template & Tech Stack API](#7-template--tech-stack-api)
8. [Code & Artifacts API](#8-code--artifacts-api)
9. [Review & Security API](#9-review--security-api)
10. [Testing API](#10-testing-api)
11. [Deployment API](#11-deployment-api)
12. [GitHub Integration API](#12-github-integration-api)
13. [LLM Configuration API](#13-llm-configuration-api)
14. [WebSocket Events API](#14-websocket-events-api)
15. [Project Manager API](#15-project-manager-api)
16. [Observability API](#16-observability-api)
17. [Audit Log API](#17-audit-log-api)
18. [Data Retention API](#18-data-retention-api)
19. [Dead Letter Queue API](#19-dead-letter-queue-api)
20. [Internal Agent Communication Protocol](#20-internal-agent-communication-protocol)
21. [CLI Commands Reference](#21-cli-commands-reference)
22. [Python SDK Reference](#22-python-sdk-reference)
23. [Error Codes Reference](#23-error-codes-reference)

---

## 1. API Overview

### Base URL

All API endpoints are served under a versioned base path:

```
https://<host>/api/v1
```

Development default: `http://localhost:8000/api/v1`

### Versioning Strategy

The API uses URI-based versioning. The current version is `v1`. When breaking changes are introduced, a new version (`v2`) will be published while `v1` remains available during a deprecation window.

### Authentication

Two authentication methods are supported:

| Method | Header | Use Case |
|--------|--------|----------|
| JWT Bearer Token | `Authorization: Bearer <token>` | Interactive sessions, browser clients |
| API Key | `X-API-Key: <key>` | CI/CD, CLI, server-to-server |

### Common Request Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | Yes | Bearer token or API key |
| `Content-Type` | Yes (for POST/PUT) | `application/json` |
| `Accept` | No | `application/json` (default) |
| `X-Request-ID` | No | Client-provided idempotency key |
| `X-API-Key` | Conditional | Alternative to Bearer token |

### Standard Response Envelope

All responses use a consistent envelope:

```json
{
  "status": "success",
  "data": {},
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2026-03-18T12:00:00Z"
  }
}
```

### Pagination

List endpoints accept `page` and `per_page` query parameters:

```
GET /api/v1/projects?page=1&per_page=20
```

Paginated responses include:

```json
{
  "data": [],
  "meta": {
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 85,
      "total_pages": 5
    }
  }
}
```

### Rate Limiting

| Tier | Requests/min | Burst |
|------|-------------|-------|
| Free | 60 | 10 |
| Pro | 300 | 50 |
| Enterprise | 1000 | 200 |

Rate limit headers returned in every response:

```
X-RateLimit-Limit: 300
X-RateLimit-Remaining: 299
X-RateLimit-Reset: 1710763200
```

When exceeded, the API returns `429 Too Many Requests`.

### Error Response Format

```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable description",
    "details": [
      {
        "field": "name",
        "issue": "Field is required"
      }
    ]
  },
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2026-03-18T12:00:00Z"
  }
}
```

### Common HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 204 | No Content (successful delete) |
| 400 | Bad Request / Validation Error |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 422 | Unprocessable Entity |
| 429 | Rate Limit Exceeded |
| 500 | Internal Server Error |

---

## 2. Authentication & Authorization API

### RBAC Roles

| Role | Description |
|------|-------------|
| `admin` | Full access to all resources and settings |
| `user` | Create/manage own projects, run pipelines |
| `viewer` | Read-only access to assigned projects |

---

### POST /api/v1/auth/register

Register a new user account.

**Authentication:** None

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "secureP@ssw0rd",
  "name": "Jane Doe",
  "organization": "Acme Corp"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | Yes | Valid email address |
| `password` | string | Yes | Min 8 chars, 1 uppercase, 1 number, 1 special |
| `name` | string | Yes | Full name |
| `organization` | string | No | Organization name |

**Response (201 Created):**

```json
{
  "status": "success",
  "data": {
    "id": "usr_a1b2c3",
    "email": "user@example.com",
    "name": "Jane Doe",
    "role": "user",
    "organization": "Acme Corp",
    "created_at": "2026-03-18T12:00:00Z"
  },
  "meta": {
    "request_id": "req_001",
    "timestamp": "2026-03-18T12:00:00Z"
  }
}
```

**Status Codes:**

| Code | Description |
|------|-------------|
| 201 | Account created |
| 400 | Validation error |
| 409 | Email already registered |

---

### POST /api/v1/auth/login

Authenticate and obtain JWT tokens.

**Authentication:** None

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "secureP@ssw0rd"
}
```

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "access_token": "eyJhbGciOiJSUzI1NiIs...",
    "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2g...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "user": {
      "id": "usr_a1b2c3",
      "email": "user@example.com",
      "name": "Jane Doe",
      "role": "user"
    }
  },
  "meta": {
    "request_id": "req_002",
    "timestamp": "2026-03-18T12:00:01Z"
  }
}
```

**Status Codes:**

| Code | Description |
|------|-------------|
| 200 | Login successful |
| 400 | Missing fields |
| 401 | Invalid credentials |
| 429 | Too many failed attempts |

---

### POST /api/v1/auth/refresh

Refresh an expired access token using a valid refresh token.

**Authentication:** None (refresh token in body)

**Request Body:**

```json
{
  "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2g..."
}
```

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "access_token": "eyJhbGciOiJSUzI1NiIs...",
    "expires_in": 3600
  },
  "meta": {
    "request_id": "req_003",
    "timestamp": "2026-03-18T12:00:02Z"
  }
}
```

**Status Codes:**

| Code | Description |
|------|-------------|
| 200 | Token refreshed |
| 401 | Invalid or expired refresh token |

---

### POST /api/v1/auth/logout

Invalidate the current session tokens.

**Authentication:** Bearer token

**Request Body:**

```json
{
  "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2g..."
}
```

**Response (204):** No content.

**Status Codes:**

| Code | Description |
|------|-------------|
| 204 | Logged out |
| 401 | Unauthorized |

---

### GET /api/v1/auth/me

Get the currently authenticated user profile.

**Authentication:** Bearer token

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "id": "usr_a1b2c3",
    "email": "user@example.com",
    "name": "Jane Doe",
    "role": "user",
    "organization": "Acme Corp",
    "api_keys": [
      {
        "id": "key_x1y2",
        "name": "CLI Key",
        "prefix": "cb_live_abc...",
        "created_at": "2026-03-01T10:00:00Z",
        "last_used_at": "2026-03-18T11:00:00Z"
      }
    ],
    "created_at": "2026-03-01T10:00:00Z",
    "updated_at": "2026-03-18T12:00:00Z"
  },
  "meta": {
    "request_id": "req_004",
    "timestamp": "2026-03-18T12:00:03Z"
  }
}
```

**Status Codes:**

| Code | Description |
|------|-------------|
| 200 | Success |
| 401 | Unauthorized |

---

### PUT /api/v1/auth/settings

Update user settings and preferences.

**Authentication:** Bearer token

**Request Body:**

```json
{
  "name": "Jane M. Doe",
  "default_llm_provider": "openai",
  "notifications": {
    "email_on_pipeline_complete": true,
    "email_on_review_requested": true
  },
  "theme": "dark"
}
```

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "id": "usr_a1b2c3",
    "name": "Jane M. Doe",
    "default_llm_provider": "openai",
    "notifications": {
      "email_on_pipeline_complete": true,
      "email_on_review_requested": true
    },
    "theme": "dark",
    "updated_at": "2026-03-18T12:01:00Z"
  },
  "meta": {
    "request_id": "req_005",
    "timestamp": "2026-03-18T12:01:00Z"
  }
}
```

**Status Codes:**

| Code | Description |
|------|-------------|
| 200 | Settings updated |
| 400 | Validation error |
| 401 | Unauthorized |

---

## 3. Project Management API

### POST /api/v1/projects

Create a new project from a PRD (text, file upload, or URL).

**Authentication:** Bearer token (role: `user`, `admin`)

**Request Body:**

```json
{
  "name": "E-Commerce Platform",
  "description": "Full-stack e-commerce application with payments",
  "prd_source": "text",
  "prd_content": "Build an e-commerce platform with user auth, product catalog, shopping cart, Stripe payments, and admin dashboard...",
  "tech_stack_id": "ts_react_fastapi",
  "template_id": "tpl_ecommerce",
  "settings": {
    "target_language": "python",
    "frontend_framework": "react",
    "database": "postgresql",
    "enable_tests": true,
    "enable_security_scan": true
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Project name |
| `description` | string | No | Short description |
| `prd_source` | string | Yes | One of: `text`, `file`, `url` |
| `prd_content` | string | Conditional | PRD text when `prd_source` is `text` |
| `prd_url` | string | Conditional | URL when `prd_source` is `url` |
| `prd_file` | string | Conditional | Base64-encoded file when `prd_source` is `file` |
| `tech_stack_id` | string | No | Pre-selected tech stack |
| `template_id` | string | No | UI/scaffold template |
| `settings` | object | No | Project settings overrides |

**Response (201 Created):**

```json
{
  "status": "success",
  "data": {
    "id": "prj_d4e5f6",
    "name": "E-Commerce Platform",
    "description": "Full-stack e-commerce application with payments",
    "status": "created",
    "prd_source": "text",
    "tech_stack": {
      "id": "ts_react_fastapi",
      "name": "React + FastAPI"
    },
    "settings": {
      "target_language": "python",
      "frontend_framework": "react",
      "database": "postgresql",
      "enable_tests": true,
      "enable_security_scan": true
    },
    "owner_id": "usr_a1b2c3",
    "created_at": "2026-03-18T12:05:00Z",
    "updated_at": "2026-03-18T12:05:00Z"
  },
  "meta": {
    "request_id": "req_010",
    "timestamp": "2026-03-18T12:05:00Z"
  }
}
```

**Status Codes:**

| Code | Description |
|------|-------------|
| 201 | Project created |
| 400 | Validation error |
| 401 | Unauthorized |
| 422 | PRD parsing failed |

---

### GET /api/v1/projects

List all projects for the authenticated user.

**Authentication:** Bearer token

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number |
| `per_page` | integer | 20 | Items per page (max 100) |
| `status` | string | - | Filter: `created`, `building`, `completed`, `failed` |
| `search` | string | - | Search by name or description |
| `sort_by` | string | `created_at` | Sort field |
| `sort_order` | string | `desc` | `asc` or `desc` |

**Response (200):**

```json
{
  "status": "success",
  "data": [
    {
      "id": "prj_d4e5f6",
      "name": "E-Commerce Platform",
      "status": "building",
      "progress_percent": 45,
      "pipeline_count": 1,
      "created_at": "2026-03-18T12:05:00Z",
      "updated_at": "2026-03-18T12:30:00Z"
    }
  ],
  "meta": {
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 3,
      "total_pages": 1
    },
    "request_id": "req_011",
    "timestamp": "2026-03-18T12:30:00Z"
  }
}
```

---

### GET /api/v1/projects/{id}

Get full project details including tech stack, stats, and active pipeline.

**Authentication:** Bearer token

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Project ID |

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "id": "prj_d4e5f6",
    "name": "E-Commerce Platform",
    "description": "Full-stack e-commerce application with payments",
    "status": "building",
    "progress_percent": 45,
    "prd_source": "text",
    "prd_content": "Build an e-commerce platform...",
    "tech_stack": {
      "id": "ts_react_fastapi",
      "name": "React + FastAPI",
      "components": ["react", "vite", "tailwindcss", "fastapi", "postgresql"]
    },
    "settings": {
      "target_language": "python",
      "frontend_framework": "react",
      "database": "postgresql",
      "enable_tests": true,
      "enable_security_scan": true
    },
    "stats": {
      "files_generated": 42,
      "lines_of_code": 8500,
      "test_coverage_percent": 78,
      "security_findings": 2
    },
    "active_pipeline_id": "pip_g7h8i9",
    "owner_id": "usr_a1b2c3",
    "created_at": "2026-03-18T12:05:00Z",
    "updated_at": "2026-03-18T12:30:00Z"
  },
  "meta": {
    "request_id": "req_012",
    "timestamp": "2026-03-18T12:30:01Z"
  }
}
```

**Status Codes:**

| Code | Description |
|------|-------------|
| 200 | Success |
| 401 | Unauthorized |
| 404 | Project not found |

---

### PUT /api/v1/projects/{id}

Update project metadata or settings.

**Authentication:** Bearer token (owner or admin)

**Request Body:**

```json
{
  "name": "E-Commerce Pro",
  "description": "Updated description",
  "settings": {
    "enable_security_scan": false
  }
}
```

**Response (200):** Returns updated project object (same schema as GET).

**Status Codes:**

| Code | Description |
|------|-------------|
| 200 | Updated |
| 400 | Validation error |
| 401 | Unauthorized |
| 403 | Forbidden (not owner) |
| 404 | Not found |

---

### DELETE /api/v1/projects/{id}

Delete a project and all associated data.

**Authentication:** Bearer token (owner or admin)

**Response (204):** No content.

**Status Codes:**

| Code | Description |
|------|-------------|
| 204 | Deleted |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not found |
| 409 | Active pipeline running |

---

### POST /api/v1/projects/{id}/clone

Clone an existing project with optional inclusion of generated artifacts.

**Authentication:** Bearer token

**Request Body:**

```json
{
  "name": "E-Commerce Platform v2",
  "include_generated_code": false,
  "include_pipeline_history": false
}
```

**Response (201):** Returns the new cloned project object.

**Status Codes:**

| Code | Description |
|------|-------------|
| 201 | Cloned |
| 401 | Unauthorized |
| 404 | Source project not found |

---

### GET /api/v1/projects/{id}/stats

Get detailed project statistics.

**Authentication:** Bearer token

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "files_generated": 42,
    "total_lines_of_code": 8500,
    "languages": {
      "python": 4200,
      "typescript": 3100,
      "css": 800,
      "html": 400
    },
    "test_coverage_percent": 78,
    "tests_total": 65,
    "tests_passing": 62,
    "tests_failing": 3,
    "security_findings": {
      "critical": 0,
      "high": 1,
      "medium": 1,
      "low": 3
    },
    "agents_used": 18,
    "total_llm_tokens": 245000,
    "pipeline_duration_seconds": 1847
  },
  "meta": {
    "request_id": "req_015",
    "timestamp": "2026-03-18T12:31:00Z"
  }
}
```

---

### POST /api/v1/projects/{id}/import

Import an existing codebase (brownfield/inflight project).

**Authentication:** Bearer token

**Request Body:**

```json
{
  "source": "github",
  "repository_url": "https://github.com/org/repo",
  "branch": "main",
  "analysis_depth": "full",
  "import_options": {
    "detect_tech_stack": true,
    "generate_prd": true,
    "map_architecture": true
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source` | string | Yes | `github`, `gitlab`, `zip_upload`, `local_path` |
| `repository_url` | string | Conditional | Git repo URL |
| `branch` | string | No | Branch to import (default: `main`) |
| `analysis_depth` | string | No | `quick` or `full` (default: `full`) |
| `import_options` | object | No | Import behavior configuration |

**Response (202 Accepted):**

```json
{
  "status": "success",
  "data": {
    "import_id": "imp_j1k2l3",
    "project_id": "prj_d4e5f6",
    "status": "analyzing",
    "estimated_duration_seconds": 120
  },
  "meta": {
    "request_id": "req_016",
    "timestamp": "2026-03-18T12:32:00Z"
  }
}
```

**Status Codes:**

| Code | Description |
|------|-------------|
| 202 | Import started |
| 400 | Invalid source |
| 401 | Unauthorized |
| 422 | Repository inaccessible |

---

## 4. Pipeline Management API

Pipelines orchestrate the multi-agent execution graph that builds the project.

### POST /api/v1/projects/{id}/pipelines

Create a new execution pipeline for a project.

**Authentication:** Bearer token (role: `user`, `admin`)

**Request Body:**

```json
{
  "name": "Initial Build",
  "mode": "full",
  "phases": ["brainstorm", "plan", "architect", "design", "develop", "test", "review", "deploy"],
  "config": {
    "auto_approve_gates": false,
    "max_retries": 3,
    "parallel_agents": 5,
    "checkpoint_interval": "phase"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | No | Pipeline label |
| `mode` | string | No | `full`, `incremental`, or `phase_only` (default: `full`) |
| `phases` | array | No | Ordered list of phases to execute |
| `config` | object | No | Execution configuration |

**Response (201 Created):**

```json
{
  "status": "success",
  "data": {
    "id": "pip_g7h8i9",
    "project_id": "prj_d4e5f6",
    "name": "Initial Build",
    "status": "created",
    "mode": "full",
    "phases": ["brainstorm", "plan", "architect", "design", "develop", "test", "review", "deploy"],
    "config": {
      "auto_approve_gates": false,
      "max_retries": 3,
      "parallel_agents": 5,
      "checkpoint_interval": "phase"
    },
    "created_at": "2026-03-18T12:35:00Z"
  },
  "meta": {
    "request_id": "req_020",
    "timestamp": "2026-03-18T12:35:00Z"
  }
}
```

---

### GET /api/v1/projects/{id}/pipelines

List all pipelines for a project.

**Authentication:** Bearer token

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number |
| `per_page` | integer | 20 | Items per page |
| `status` | string | - | Filter by status |

**Response (200):** Paginated array of pipeline summary objects.

---

### GET /api/v1/pipelines/{id}

Get detailed pipeline status and progress.

**Authentication:** Bearer token

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "id": "pip_g7h8i9",
    "project_id": "prj_d4e5f6",
    "name": "Initial Build",
    "status": "running",
    "current_phase": "develop",
    "progress_percent": 62,
    "phases": [
      {
        "name": "brainstorm",
        "status": "completed",
        "started_at": "2026-03-18T12:36:00Z",
        "completed_at": "2026-03-18T12:38:00Z",
        "duration_seconds": 120
      },
      {
        "name": "plan",
        "status": "completed",
        "started_at": "2026-03-18T12:38:00Z",
        "completed_at": "2026-03-18T12:42:00Z",
        "duration_seconds": 240
      },
      {
        "name": "develop",
        "status": "running",
        "started_at": "2026-03-18T12:50:00Z",
        "agents_active": 4,
        "tasks_completed": 12,
        "tasks_remaining": 8
      }
    ],
    "agents_summary": {
      "total_spawned": 14,
      "currently_active": 4,
      "completed": 10,
      "failed": 0
    },
    "started_at": "2026-03-18T12:36:00Z",
    "estimated_completion": "2026-03-18T13:15:00Z"
  },
  "meta": {
    "request_id": "req_021",
    "timestamp": "2026-03-18T12:55:00Z"
  }
}
```

---

### POST /api/v1/pipelines/{id}/start

Start pipeline execution.

**Authentication:** Bearer token (role: `user`, `admin`)

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "id": "pip_g7h8i9",
    "status": "running",
    "started_at": "2026-03-18T12:36:00Z"
  },
  "meta": {
    "request_id": "req_022",
    "timestamp": "2026-03-18T12:36:00Z"
  }
}
```

**Status Codes:**

| Code | Description |
|------|-------------|
| 200 | Pipeline started |
| 400 | Pipeline already running |
| 401 | Unauthorized |
| 404 | Pipeline not found |

---

### POST /api/v1/pipelines/{id}/pause

Pause a running pipeline. Active agents complete their current task before stopping.

**Authentication:** Bearer token

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "id": "pip_g7h8i9",
    "status": "paused",
    "paused_at": "2026-03-18T12:50:00Z",
    "active_agents_draining": 2
  }
}
```

---

### POST /api/v1/pipelines/{id}/resume

Resume a paused pipeline.

**Authentication:** Bearer token

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "id": "pip_g7h8i9",
    "status": "running",
    "resumed_at": "2026-03-18T13:00:00Z"
  }
}
```

---

### POST /api/v1/pipelines/{id}/cancel

Cancel a running or paused pipeline. All active agents are terminated.

**Authentication:** Bearer token

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "id": "pip_g7h8i9",
    "status": "cancelled",
    "cancelled_at": "2026-03-18T13:01:00Z"
  }
}
```

---

### GET /api/v1/pipelines/{id}/graph

Get the execution graph (DAG) showing agent dependencies and data flow.

**Authentication:** Bearer token

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "pipeline_id": "pip_g7h8i9",
    "nodes": [
      {
        "id": "node_001",
        "agent_type": "planner",
        "agent_id": "agt_m1n2o3",
        "status": "completed",
        "phase": "plan"
      },
      {
        "id": "node_002",
        "agent_type": "architect",
        "agent_id": "agt_p4q5r6",
        "status": "completed",
        "phase": "architect"
      },
      {
        "id": "node_003",
        "agent_type": "frontend_developer",
        "agent_id": "agt_s7t8u9",
        "status": "running",
        "phase": "develop"
      }
    ],
    "edges": [
      { "from": "node_001", "to": "node_002", "type": "data_dependency" },
      { "from": "node_002", "to": "node_003", "type": "data_dependency" }
    ]
  }
}
```

---

### GET /api/v1/pipelines/{id}/checkpoints

List available checkpoints for rollback.

**Authentication:** Bearer token

**Response (200):**

```json
{
  "status": "success",
  "data": [
    {
      "id": "chk_v1w2x3",
      "pipeline_id": "pip_g7h8i9",
      "phase": "architect",
      "label": "Post-architecture checkpoint",
      "files_snapshot_count": 15,
      "created_at": "2026-03-18T12:48:00Z"
    },
    {
      "id": "chk_y4z5a6",
      "pipeline_id": "pip_g7h8i9",
      "phase": "develop",
      "label": "Mid-development checkpoint",
      "files_snapshot_count": 35,
      "created_at": "2026-03-18T13:05:00Z"
    }
  ]
}
```

---

### POST /api/v1/pipelines/{id}/restore/{checkpoint_id}

Restore a pipeline to a previous checkpoint state.

**Authentication:** Bearer token (role: `user`, `admin`)

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "pipeline_id": "pip_g7h8i9",
    "restored_checkpoint": "chk_v1w2x3",
    "restored_phase": "architect",
    "files_restored": 15,
    "status": "paused"
  }
}
```

**Status Codes:**

| Code | Description |
|------|-------------|
| 200 | Restored |
| 401 | Unauthorized |
| 404 | Pipeline or checkpoint not found |
| 409 | Pipeline is running (must pause first) |

---

### GET /api/v1/pipelines/{id}/phases

List all phases in a pipeline with status.

**Authentication:** Bearer token

**Response (200):**

```json
{
  "status": "success",
  "data": [
    {
      "id": "pha_b7c8d9",
      "name": "brainstorm",
      "status": "completed",
      "gate_status": "approved",
      "agents_used": 1,
      "duration_seconds": 120
    },
    {
      "id": "pha_e1f2g3",
      "name": "develop",
      "status": "running",
      "gate_status": "pending",
      "agents_used": 4,
      "tasks_completed": 12,
      "tasks_total": 20
    }
  ]
}
```

---

### GET /api/v1/pipelines/{id}/phases/{phase_id}

Get detailed information about a specific phase.

**Authentication:** Bearer token

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "id": "pha_e1f2g3",
    "name": "develop",
    "status": "running",
    "gate_status": "pending",
    "agents": [
      {
        "id": "agt_s7t8u9",
        "type": "frontend_developer",
        "status": "running",
        "current_task": "Implementing product listing page"
      },
      {
        "id": "agt_h1i2j3",
        "type": "backend_developer",
        "status": "running",
        "current_task": "Building REST API for products"
      }
    ],
    "artifacts_produced": 28,
    "started_at": "2026-03-18T12:50:00Z"
  }
}
```

---

### POST /api/v1/pipelines/{id}/phases/{phase_id}/approve

Approve a phase gate to allow the pipeline to proceed to the next phase.

**Authentication:** Bearer token (role: `user`, `admin`)

**Request Body:**

```json
{
  "approved": true,
  "comment": "Architecture looks good, proceed to development."
}
```

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "phase_id": "pha_e1f2g3",
    "gate_status": "approved",
    "approved_by": "usr_a1b2c3",
    "next_phase": "test",
    "approved_at": "2026-03-18T13:10:00Z"
  }
}
```

**Status Codes:**

| Code | Description |
|------|-------------|
| 200 | Gate approved/rejected |
| 400 | Phase not awaiting approval |
| 401 | Unauthorized |
| 403 | Insufficient role |

---

## 5. Agent Management API

### GET /api/v1/agents

List all active and recent agent instances across all projects.

**Authentication:** Bearer token

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number |
| `per_page` | integer | 20 | Items per page |
| `status` | string | - | `running`, `completed`, `failed`, `stopped` |
| `type` | string | - | Agent type filter |
| `project_id` | string | - | Filter by project |
| `pipeline_id` | string | - | Filter by pipeline |

**Response (200):**

```json
{
  "status": "success",
  "data": [
    {
      "id": "agt_s7t8u9",
      "type": "frontend_developer",
      "status": "running",
      "project_id": "prj_d4e5f6",
      "pipeline_id": "pip_g7h8i9",
      "phase": "develop",
      "current_task": "Implementing product listing page",
      "progress_percent": 60,
      "started_at": "2026-03-18T12:50:00Z"
    }
  ],
  "meta": {
    "pagination": { "page": 1, "per_page": 20, "total": 4, "total_pages": 1 }
  }
}
```

---

### GET /api/v1/agents/{id}

Get detailed agent information including configuration and state.

**Authentication:** Bearer token

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "id": "agt_s7t8u9",
    "type": "frontend_developer",
    "status": "running",
    "project_id": "prj_d4e5f6",
    "pipeline_id": "pip_g7h8i9",
    "phase": "develop",
    "current_task": "Implementing product listing page",
    "progress_percent": 60,
    "config": {
      "llm_provider": "openai",
      "llm_model": "gpt-4o",
      "temperature": 0.2,
      "max_retries": 3
    },
    "metrics": {
      "tasks_completed": 5,
      "tasks_failed": 0,
      "tokens_used": 32000,
      "llm_calls": 12,
      "files_created": 8,
      "files_modified": 3
    },
    "dependencies": ["agt_p4q5r6"],
    "started_at": "2026-03-18T12:50:00Z",
    "last_activity_at": "2026-03-18T13:02:00Z"
  }
}
```

---

### GET /api/v1/agents/{id}/logs

Get agent execution logs with streaming support.

**Authentication:** Bearer token

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `level` | string | `info` | Min log level: `debug`, `info`, `warn`, `error` |
| `since` | string | - | ISO-8601 timestamp filter |
| `limit` | integer | 100 | Max log entries |
| `offset` | integer | 0 | Pagination offset |

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "agent_id": "agt_s7t8u9",
    "logs": [
      {
        "timestamp": "2026-03-18T12:50:01Z",
        "level": "info",
        "message": "Agent initialized with frontend_developer role",
        "metadata": {}
      },
      {
        "timestamp": "2026-03-18T12:50:05Z",
        "level": "info",
        "message": "Received task: Implement product listing page",
        "metadata": { "task_id": "tsk_001" }
      },
      {
        "timestamp": "2026-03-18T12:51:30Z",
        "level": "info",
        "message": "Created file: src/components/ProductList.tsx",
        "metadata": { "file_path": "src/components/ProductList.tsx", "lines": 145 }
      }
    ],
    "has_more": true
  }
}
```

---

### POST /api/v1/agents/{id}/stop

Stop a running agent gracefully.

**Authentication:** Bearer token (role: `user`, `admin`)

**Request Body:**

```json
{
  "reason": "Manual stop for review",
  "force": false
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `reason` | string | No | Reason for stopping |
| `force` | boolean | No | Force-kill without graceful shutdown (default: false) |

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "id": "agt_s7t8u9",
    "status": "stopped",
    "stopped_at": "2026-03-18T13:05:00Z",
    "reason": "Manual stop for review"
  }
}
```

---

### POST /api/v1/agents/{id}/restart

Restart a stopped or failed agent.

**Authentication:** Bearer token

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "id": "agt_s7t8u9",
    "status": "running",
    "restarted_at": "2026-03-18T13:06:00Z",
    "resume_from_task": "tsk_006"
  }
}
```

---

### GET /api/v1/agents/types

List all available agent types and their capabilities.

**Authentication:** Bearer token

**Response (200):**

```json
{
  "status": "success",
  "data": [
    {
      "type": "orchestrator",
      "display_name": "Orchestrator",
      "description": "Coordinates all other agents and manages execution flow",
      "category": "control",
      "capabilities": ["task_routing", "dependency_resolution", "error_escalation"]
    },
    {
      "type": "brainstorming",
      "display_name": "Brainstorming Agent",
      "description": "Explores requirements and generates ideas interactively",
      "category": "planning",
      "capabilities": ["requirement_analysis", "idea_generation", "clarification"]
    },
    {
      "type": "planner",
      "display_name": "Planner",
      "description": "Creates detailed implementation plans from requirements",
      "category": "planning",
      "capabilities": ["task_decomposition", "estimation", "dependency_mapping"]
    },
    {
      "type": "architect",
      "display_name": "Architect",
      "description": "Designs system architecture and data models",
      "category": "design",
      "capabilities": ["system_design", "api_design", "data_modeling"]
    },
    {
      "type": "frontend_developer",
      "display_name": "Frontend Developer",
      "description": "Builds UI components and frontend logic",
      "category": "development",
      "capabilities": ["react", "vue", "html_css", "responsive_design"]
    },
    {
      "type": "backend_developer",
      "display_name": "Backend Developer",
      "description": "Implements server-side logic and APIs",
      "category": "development",
      "capabilities": ["fastapi", "django", "express", "database_queries"]
    },
    {
      "type": "security_auditor",
      "display_name": "Security Auditor",
      "description": "Scans code for vulnerabilities and security issues",
      "category": "quality",
      "capabilities": ["sast", "dependency_audit", "owasp_check"]
    },
    {
      "type": "tester",
      "display_name": "Tester",
      "description": "Generates and runs test suites",
      "category": "quality",
      "capabilities": ["unit_tests", "integration_tests", "e2e_tests"]
    }
  ]
}
```

---

### GET /api/v1/agents/{id}/context

Get the agent's current working context including shared memory state.

**Authentication:** Bearer token

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "agent_id": "agt_s7t8u9",
    "context": {
      "project_prd_summary": "E-commerce platform with...",
      "architecture_decisions": ["React SPA", "FastAPI backend", "PostgreSQL"],
      "assigned_tasks": [
        { "id": "tsk_006", "description": "Build product listing component", "status": "in_progress" }
      ],
      "shared_artifacts": [
        { "type": "api_schema", "path": "docs/openapi.yaml" },
        { "type": "data_model", "path": "docs/erd.json" }
      ],
      "conversation_history_length": 24
    }
  }
}
```

---

### POST /api/v1/agents/{id}/message

Send a human-in-the-loop message or instruction to a running agent.

**Authentication:** Bearer token

**Request Body:**

```json
{
  "message": "Please use TailwindCSS utility classes instead of CSS modules",
  "type": "instruction",
  "priority": "normal"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | Yes | Message content |
| `type` | string | No | `instruction`, `question`, `correction` (default: `instruction`) |
| `priority` | string | No | `low`, `normal`, `high` (default: `normal`) |

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "message_id": "msg_k3l4m5",
    "agent_id": "agt_s7t8u9",
    "acknowledged": true,
    "acknowledged_at": "2026-03-18T13:08:00Z"
  }
}
```

---

### GET /api/v1/agents/{id}/artifacts

Get all artifacts (files, documents, configs) produced by an agent.

**Authentication:** Bearer token

**Response (200):**

```json
{
  "status": "success",
  "data": [
    {
      "id": "art_n6o7p8",
      "type": "source_file",
      "path": "src/components/ProductList.tsx",
      "language": "typescript",
      "lines": 145,
      "created_at": "2026-03-18T12:51:30Z"
    },
    {
      "id": "art_q9r1s2",
      "type": "source_file",
      "path": "src/components/ProductCard.tsx",
      "language": "typescript",
      "lines": 78,
      "created_at": "2026-03-18T12:55:00Z"
    },
    {
      "id": "art_t3u4v5",
      "type": "test_file",
      "path": "src/__tests__/ProductList.test.tsx",
      "language": "typescript",
      "lines": 92,
      "created_at": "2026-03-18T12:58:00Z"
    }
  ]
}
```

---

## 6. Brainstorming API

Interactive AI-powered brainstorming sessions to refine project requirements before building.

### POST /api/v1/projects/{id}/brainstorm

Start a new brainstorming session for a project.

**Authentication:** Bearer token

**Request Body:**

```json
{
  "initial_prompt": "I want to build a SaaS project management tool similar to Linear",
  "mode": "exploratory",
  "focus_areas": ["features", "user_personas", "competitive_analysis"]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `initial_prompt` | string | Yes | Starting idea or requirement description |
| `mode` | string | No | `exploratory`, `focused`, `refinement` (default: `exploratory`) |
| `focus_areas` | array | No | Areas to focus brainstorming on |

**Response (201 Created):**

```json
{
  "status": "success",
  "data": {
    "session_id": "brs_w5x6y7",
    "project_id": "prj_d4e5f6",
    "status": "active",
    "mode": "exploratory",
    "messages": [
      {
        "id": "bmsg_001",
        "role": "assistant",
        "content": "Great idea! Let me help you explore this further. A project management tool like Linear has several core aspects. Let me ask some clarifying questions:\n\n1. Who is your primary target audience?\n2. What key differentiator do you envision?\n3. Do you need real-time collaboration features?",
        "suggestions": [
          "Target startups with 10-50 engineers",
          "Focus on AI-powered sprint planning",
          "Include GitHub/GitLab deep integration"
        ],
        "timestamp": "2026-03-18T13:10:00Z"
      }
    ],
    "created_at": "2026-03-18T13:10:00Z"
  }
}
```

---

### GET /api/v1/projects/{id}/brainstorm/{session_id}

Get the current state of a brainstorming session.

**Authentication:** Bearer token

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "session_id": "brs_w5x6y7",
    "project_id": "prj_d4e5f6",
    "status": "active",
    "mode": "exploratory",
    "message_count": 8,
    "messages": [
      {
        "id": "bmsg_001",
        "role": "assistant",
        "content": "Great idea! Let me help you explore this further...",
        "timestamp": "2026-03-18T13:10:00Z"
      },
      {
        "id": "bmsg_002",
        "role": "user",
        "content": "Target audience is engineering teams at mid-size companies...",
        "timestamp": "2026-03-18T13:11:00Z"
      }
    ],
    "extracted_requirements": [
      "User authentication with SSO support",
      "Kanban and list views for issues",
      "Sprint planning with velocity tracking",
      "GitHub PR integration"
    ],
    "suggested_features": [
      { "name": "AI Sprint Planning", "priority": "high", "complexity": "medium" },
      { "name": "Automated Standup Reports", "priority": "medium", "complexity": "low" }
    ],
    "created_at": "2026-03-18T13:10:00Z",
    "updated_at": "2026-03-18T13:15:00Z"
  }
}
```

---

### POST /api/v1/projects/{id}/brainstorm/{session_id}/message

Send a message in an active brainstorming session.

**Authentication:** Bearer token

**Request Body:**

```json
{
  "content": "I want to focus on the AI-powered sprint planning feature. How should we scope it?",
  "attachments": []
}
```

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "user_message": {
      "id": "bmsg_009",
      "role": "user",
      "content": "I want to focus on the AI-powered sprint planning feature. How should we scope it?",
      "timestamp": "2026-03-18T13:16:00Z"
    },
    "assistant_message": {
      "id": "bmsg_010",
      "role": "assistant",
      "content": "For the AI-powered sprint planning, I recommend scoping it in three tiers...",
      "suggestions": [
        "MVP: Auto-assign issues based on past velocity",
        "V2: Predict sprint completion likelihood",
        "V3: Suggest scope adjustments mid-sprint"
      ],
      "timestamp": "2026-03-18T13:16:05Z"
    }
  }
}
```

---

### POST /api/v1/projects/{id}/brainstorm/{session_id}/finalize

Finalize the brainstorming session and convert extracted requirements into a structured PRD.

**Authentication:** Bearer token

**Request Body:**

```json
{
  "include_all_suggestions": false,
  "selected_features": ["AI Sprint Planning", "GitHub PR Integration", "Kanban Board"],
  "additional_notes": "Focus on MVP scope only"
}
```

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "session_id": "brs_w5x6y7",
    "status": "finalized",
    "generated_prd": {
      "title": "AI-Powered Project Management Tool",
      "overview": "A modern project management tool targeting mid-size engineering teams...",
      "user_personas": [
        { "name": "Engineering Manager", "goals": ["Track team velocity", "Plan sprints"] },
        { "name": "Developer", "goals": ["View assigned issues", "Link PRs to issues"] }
      ],
      "features": [
        {
          "name": "AI Sprint Planning",
          "description": "Automatically suggest issue assignments based on historical velocity",
          "priority": "P0",
          "user_stories": 5
        }
      ],
      "non_functional_requirements": [
        "Page load time under 200ms",
        "Support 1000 concurrent users",
        "SOC2 compliance"
      ]
    },
    "project_updated": true,
    "finalized_at": "2026-03-18T13:20:00Z"
  }
}
```

**Status Codes:**

| Code | Description |
|------|-------------|
| 200 | Session finalized |
| 400 | Session already finalized |
| 401 | Unauthorized |
| 404 | Session not found |

---

## 7. Template & Tech Stack API

### GET /api/v1/templates

List all available project templates and UI kits.

**Authentication:** Bearer token

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `category` | string | - | `ui_kit`, `scaffold`, `full_app` |
| `framework` | string | - | Filter by framework (`react`, `vue`, `nextjs`) |
| `search` | string | - | Search by name |

**Response (200):**

```json
{
  "status": "success",
  "data": [
    {
      "id": "tpl_ecommerce",
      "name": "E-Commerce Starter",
      "category": "full_app",
      "description": "Complete e-commerce app with product catalog, cart, and checkout",
      "framework": "react",
      "preview_url": "https://templates.codebot.dev/ecommerce/preview.png",
      "tags": ["ecommerce", "stripe", "tailwind"],
      "downloads": 1250
    },
    {
      "id": "tpl_dashboard",
      "name": "Admin Dashboard",
      "category": "ui_kit",
      "description": "Responsive admin dashboard with charts, tables, and forms",
      "framework": "react",
      "preview_url": "https://templates.codebot.dev/dashboard/preview.png",
      "tags": ["admin", "dashboard", "charts"],
      "downloads": 3400
    }
  ],
  "meta": {
    "pagination": { "page": 1, "per_page": 20, "total": 15, "total_pages": 1 }
  }
}
```

---

### GET /api/v1/templates/{id}

Get template details with preview images and included components.

**Authentication:** Bearer token

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "id": "tpl_ecommerce",
    "name": "E-Commerce Starter",
    "category": "full_app",
    "description": "Complete e-commerce app with product catalog, cart, and checkout",
    "framework": "react",
    "tech_stack": ["react", "vite", "tailwindcss", "fastapi", "postgresql", "stripe"],
    "preview_images": [
      "https://templates.codebot.dev/ecommerce/home.png",
      "https://templates.codebot.dev/ecommerce/product.png",
      "https://templates.codebot.dev/ecommerce/cart.png"
    ],
    "pages": ["Home", "Product Listing", "Product Detail", "Cart", "Checkout", "Admin Dashboard"],
    "components": ["Navbar", "ProductCard", "CartDrawer", "SearchBar", "FilterPanel"],
    "file_count": 45,
    "estimated_loc": 6000
  }
}
```

---

### GET /api/v1/techstacks

List all recommended tech stack configurations.

**Authentication:** Bearer token

**Response (200):**

```json
{
  "status": "success",
  "data": [
    {
      "id": "ts_react_fastapi",
      "name": "React + FastAPI",
      "description": "Modern full-stack with React frontend and FastAPI backend",
      "frontend": { "framework": "react", "bundler": "vite", "css": "tailwindcss" },
      "backend": { "framework": "fastapi", "language": "python" },
      "database": "postgresql",
      "category": "full_stack",
      "popularity": "high"
    },
    {
      "id": "ts_nextjs_prisma",
      "name": "Next.js + Prisma",
      "description": "Full-stack TypeScript with Next.js and Prisma ORM",
      "frontend": { "framework": "nextjs", "bundler": "webpack", "css": "tailwindcss" },
      "backend": { "framework": "nextjs_api", "language": "typescript" },
      "database": "postgresql",
      "category": "full_stack",
      "popularity": "high"
    }
  ]
}
```

---

### POST /api/v1/techstacks/recommend

Get an AI-recommended tech stack based on project requirements.

**Authentication:** Bearer token

**Request Body:**

```json
{
  "project_description": "Real-time collaborative document editor with offline support",
  "requirements": {
    "real_time": true,
    "offline_support": true,
    "mobile_app": false,
    "expected_users": 10000,
    "team_experience": ["typescript", "react", "python"]
  }
}
```

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "recommended": {
      "id": "ts_custom_001",
      "name": "React + FastAPI + WebSocket",
      "reasoning": "Given real-time and offline requirements, a WebSocket-enabled backend with CRDTs is ideal.",
      "frontend": {
        "framework": "react",
        "bundler": "vite",
        "css": "tailwindcss",
        "additional": ["yjs", "service-worker"]
      },
      "backend": {
        "framework": "fastapi",
        "language": "python",
        "additional": ["websockets", "redis"]
      },
      "database": "postgresql",
      "cache": "redis",
      "real_time": "websocket"
    },
    "alternatives": [
      {
        "id": "ts_nextjs_supabase",
        "name": "Next.js + Supabase",
        "reasoning": "Supabase provides built-in real-time subscriptions"
      }
    ]
  }
}
```

---

### GET /api/v1/techstacks/{id}

Get detailed tech stack information including all component versions and compatibility matrix.

**Authentication:** Bearer token

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "id": "ts_react_fastapi",
    "name": "React + FastAPI",
    "components": [
      { "name": "react", "version": "18.3.x", "role": "frontend_framework" },
      { "name": "vite", "version": "5.x", "role": "bundler" },
      { "name": "tailwindcss", "version": "3.4.x", "role": "css_framework" },
      { "name": "fastapi", "version": "0.111.x", "role": "backend_framework" },
      { "name": "sqlalchemy", "version": "2.x", "role": "orm" },
      { "name": "postgresql", "version": "16.x", "role": "database" },
      { "name": "redis", "version": "7.x", "role": "cache" }
    ],
    "compatible_templates": ["tpl_ecommerce", "tpl_dashboard", "tpl_saas"]
  }
}
```

---

## 8. Code & Artifacts API

### GET /api/v1/projects/{id}/files

List all generated files in the project.

**Authentication:** Bearer token

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | string | `/` | Directory path to list |
| `recursive` | boolean | false | Include subdirectory contents |
| `type` | string | - | Filter: `source`, `test`, `config`, `docs` |

**Response (200):**

```json
{
  "status": "success",
  "data": [
    {
      "path": "src/components/ProductList.tsx",
      "type": "source",
      "language": "typescript",
      "size_bytes": 4250,
      "lines": 145,
      "created_by_agent": "agt_s7t8u9",
      "last_modified": "2026-03-18T12:51:30Z"
    },
    {
      "path": "src/api/products.py",
      "type": "source",
      "language": "python",
      "size_bytes": 3100,
      "lines": 98,
      "created_by_agent": "agt_h1i2j3",
      "last_modified": "2026-03-18T12:52:00Z"
    }
  ],
  "meta": {
    "total_files": 42,
    "total_lines": 8500
  }
}
```

---

### GET /api/v1/projects/{id}/files/{path}

Get the content of a specific generated file.

**Authentication:** Bearer token

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Project ID |
| `path` | string | URL-encoded file path (e.g., `src%2Fcomponents%2FProductList.tsx`) |

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "path": "src/components/ProductList.tsx",
    "content": "import React from 'react';\nimport { ProductCard } from './ProductCard';\n\nexport const ProductList: React.FC = () => {\n  // ...\n};",
    "language": "typescript",
    "size_bytes": 4250,
    "lines": 145,
    "encoding": "utf-8",
    "created_by_agent": "agt_s7t8u9",
    "last_modified": "2026-03-18T12:51:30Z",
    "version": 3,
    "history": [
      { "version": 1, "agent": "agt_s7t8u9", "timestamp": "2026-03-18T12:51:30Z" },
      { "version": 2, "agent": "agt_review01", "timestamp": "2026-03-18T13:00:00Z" },
      { "version": 3, "agent": "agt_s7t8u9", "timestamp": "2026-03-18T13:05:00Z" }
    ]
  }
}
```

---

### GET /api/v1/projects/{id}/diff

Get the code diff for all changes or between specific versions.

**Authentication:** Bearer token

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `from_checkpoint` | string | - | Starting checkpoint ID |
| `to_checkpoint` | string | - | Ending checkpoint ID (default: current) |
| `file_path` | string | - | Filter to specific file |
| `format` | string | `unified` | `unified`, `side_by_side`, or `json` |

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "files_changed": 5,
    "insertions": 120,
    "deletions": 15,
    "diffs": [
      {
        "path": "src/components/ProductList.tsx",
        "status": "modified",
        "insertions": 20,
        "deletions": 5,
        "hunks": [
          {
            "header": "@@ -10,5 +10,20 @@",
            "lines": [
              { "type": "context", "content": "export const ProductList: React.FC = () => {" },
              { "type": "deletion", "content": "  return <div>TODO</div>;" },
              { "type": "addition", "content": "  const [products, setProducts] = useState([]);" },
              { "type": "addition", "content": "  // ... full implementation" }
            ]
          }
        ]
      }
    ]
  }
}
```

---

### GET /api/v1/projects/{id}/tree

Get the complete file tree structure.

**Authentication:** Bearer token

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "name": "e-commerce-platform",
    "type": "directory",
    "children": [
      {
        "name": "src",
        "type": "directory",
        "children": [
          {
            "name": "components",
            "type": "directory",
            "children": [
              { "name": "ProductList.tsx", "type": "file", "language": "typescript", "lines": 145 },
              { "name": "ProductCard.tsx", "type": "file", "language": "typescript", "lines": 78 }
            ]
          },
          {
            "name": "api",
            "type": "directory",
            "children": [
              { "name": "products.py", "type": "file", "language": "python", "lines": 98 }
            ]
          }
        ]
      },
      { "name": "package.json", "type": "file", "language": "json", "lines": 35 },
      { "name": "README.md", "type": "file", "language": "markdown", "lines": 80 }
    ]
  }
}
```

---

### POST /api/v1/projects/{id}/files/{path}/edit

Apply a human edit to a generated file. The change is tracked and agents are notified.

**Authentication:** Bearer token

**Request Body:**

```json
{
  "content": "import React from 'react';\n// Updated by human\nexport const ProductList: React.FC = () => {\n  return <div>Updated content</div>;\n};",
  "comment": "Fixed component structure per design review"
}
```

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "path": "src/components/ProductList.tsx",
    "version": 4,
    "edited_by": "usr_a1b2c3",
    "comment": "Fixed component structure per design review",
    "saved_at": "2026-03-18T13:25:00Z",
    "agents_notified": ["agt_s7t8u9", "agt_review01"]
  }
}
```

**Status Codes:**

| Code | Description |
|------|-------------|
| 200 | File updated |
| 400 | Invalid content |
| 401 | Unauthorized |
| 404 | File not found |
| 409 | Concurrent edit conflict |

---

## 9. Review & Security API

### GET /api/v1/projects/{id}/reviews

List all code reviews for a project.

**Authentication:** Bearer token

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | - | `pending`, `approved`, `changes_requested` |
| `page` | integer | 1 | Page number |
| `per_page` | integer | 20 | Items per page |

**Response (200):**

```json
{
  "status": "success",
  "data": [
    {
      "id": "rev_a1b2c3",
      "project_id": "prj_d4e5f6",
      "pipeline_id": "pip_g7h8i9",
      "status": "pending",
      "reviewer_agent": "agt_review01",
      "files_reviewed": 12,
      "findings": { "critical": 0, "warning": 3, "info": 7 },
      "created_at": "2026-03-18T13:10:00Z"
    }
  ]
}
```

---

### GET /api/v1/reviews/{id}

Get detailed review results with per-file findings.

**Authentication:** Bearer token

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "id": "rev_a1b2c3",
    "project_id": "prj_d4e5f6",
    "status": "pending",
    "reviewer_agent": "agt_review01",
    "summary": "Overall code quality is good. Found 3 warnings related to error handling and 7 style suggestions.",
    "files": [
      {
        "path": "src/api/products.py",
        "status": "reviewed",
        "findings": [
          {
            "id": "find_001",
            "severity": "warning",
            "line": 45,
            "column": 12,
            "rule": "error-handling",
            "message": "Bare except clause should catch specific exceptions",
            "suggestion": "Replace `except:` with `except (ValueError, KeyError):`",
            "auto_fixable": true
          }
        ]
      }
    ],
    "metrics": {
      "code_quality_score": 8.2,
      "maintainability_index": 75,
      "cyclomatic_complexity_avg": 4.5
    },
    "created_at": "2026-03-18T13:10:00Z"
  }
}
```

---

### POST /api/v1/reviews/{id}/comments

Add a human comment to a review finding.

**Authentication:** Bearer token

**Request Body:**

```json
{
  "file_path": "src/api/products.py",
  "line": 45,
  "content": "Agreed, let's fix this. Also add logging for the caught exception.",
  "finding_id": "find_001"
}
```

**Response (201):**

```json
{
  "status": "success",
  "data": {
    "comment_id": "cmt_d4e5f6",
    "review_id": "rev_a1b2c3",
    "author_id": "usr_a1b2c3",
    "content": "Agreed, let's fix this. Also add logging for the caught exception.",
    "created_at": "2026-03-18T13:15:00Z"
  }
}
```

---

### POST /api/v1/reviews/{id}/approve

Approve or request changes for a review.

**Authentication:** Bearer token (role: `user`, `admin`)

**Request Body:**

```json
{
  "decision": "approved",
  "comment": "Code looks good after the suggested fixes."
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `decision` | string | Yes | `approved` or `changes_requested` |
| `comment` | string | No | Optional comment |

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "review_id": "rev_a1b2c3",
    "status": "approved",
    "approved_by": "usr_a1b2c3",
    "approved_at": "2026-03-18T13:20:00Z"
  }
}
```

---

### GET /api/v1/projects/{id}/security

Get the latest security scan summary for a project.

**Authentication:** Bearer token

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "project_id": "prj_d4e5f6",
    "last_scan_at": "2026-03-18T13:12:00Z",
    "status": "completed",
    "summary": {
      "critical": 0,
      "high": 1,
      "medium": 2,
      "low": 5,
      "info": 3,
      "total": 11
    },
    "scans_performed": ["sast", "dependency_audit", "secrets_detection", "owasp_top10"],
    "dependency_vulnerabilities": 2,
    "score": 82
  }
}
```

---

### GET /api/v1/projects/{id}/security/findings

List all security findings with details.

**Authentication:** Bearer token

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `severity` | string | - | `critical`, `high`, `medium`, `low`, `info` |
| `category` | string | - | `sast`, `dependency`, `secrets`, `owasp` |
| `status` | string | - | `open`, `fixed`, `ignored` |

**Response (200):**

```json
{
  "status": "success",
  "data": [
    {
      "id": "sec_g7h8i9",
      "severity": "high",
      "category": "sast",
      "title": "SQL Injection vulnerability",
      "description": "Unsanitized user input used in database query",
      "file_path": "src/api/search.py",
      "line": 23,
      "cwe": "CWE-89",
      "owasp": "A03:2021",
      "remediation": "Use parameterized queries instead of string concatenation",
      "status": "open",
      "detected_at": "2026-03-18T13:12:00Z"
    },
    {
      "id": "sec_j1k2l3",
      "severity": "medium",
      "category": "dependency",
      "title": "Vulnerable dependency: lodash@4.17.20",
      "description": "Prototype pollution vulnerability (CVE-2021-23337)",
      "remediation": "Upgrade to lodash@4.17.21 or later",
      "status": "open",
      "detected_at": "2026-03-18T13:12:00Z"
    }
  ]
}
```

---

### POST /api/v1/projects/{id}/security/rescan

Trigger a new security scan.

**Authentication:** Bearer token

**Request Body:**

```json
{
  "scan_types": ["sast", "dependency_audit", "secrets_detection"],
  "scope": "full"
}
```

**Response (202 Accepted):**

```json
{
  "status": "success",
  "data": {
    "scan_id": "scn_m3n4o5",
    "project_id": "prj_d4e5f6",
    "status": "running",
    "scan_types": ["sast", "dependency_audit", "secrets_detection"],
    "started_at": "2026-03-18T13:30:00Z"
  }
}
```

---

## 10. Testing API

### GET /api/v1/projects/{id}/tests

List all test suites generated for a project.

**Authentication:** Bearer token

**Response (200):**

```json
{
  "status": "success",
  "data": [
    {
      "id": "suite_p6q7r8",
      "name": "Unit Tests - Frontend Components",
      "type": "unit",
      "framework": "vitest",
      "test_count": 28,
      "file_count": 8,
      "last_run": {
        "status": "passed",
        "passed": 26,
        "failed": 2,
        "skipped": 0,
        "duration_seconds": 12,
        "run_at": "2026-03-18T13:15:00Z"
      }
    },
    {
      "id": "suite_s9t1u2",
      "name": "Unit Tests - Backend API",
      "type": "unit",
      "framework": "pytest",
      "test_count": 35,
      "file_count": 10,
      "last_run": {
        "status": "passed",
        "passed": 35,
        "failed": 0,
        "skipped": 0,
        "duration_seconds": 8,
        "run_at": "2026-03-18T13:15:00Z"
      }
    },
    {
      "id": "suite_v3w4x5",
      "name": "Integration Tests",
      "type": "integration",
      "framework": "pytest",
      "test_count": 12,
      "file_count": 4,
      "last_run": null
    }
  ]
}
```

---

### GET /api/v1/projects/{id}/tests/{suite_id}/results

Get detailed test results for a specific test suite.

**Authentication:** Bearer token

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "suite_id": "suite_p6q7r8",
    "run_id": "run_y5z6a7",
    "status": "completed",
    "summary": {
      "total": 28,
      "passed": 26,
      "failed": 2,
      "skipped": 0,
      "duration_seconds": 12
    },
    "tests": [
      {
        "name": "ProductList renders correctly",
        "file": "src/__tests__/ProductList.test.tsx",
        "status": "passed",
        "duration_ms": 45
      },
      {
        "name": "ProductList handles empty state",
        "file": "src/__tests__/ProductList.test.tsx",
        "status": "passed",
        "duration_ms": 32
      },
      {
        "name": "ProductCard displays price correctly",
        "file": "src/__tests__/ProductCard.test.tsx",
        "status": "failed",
        "duration_ms": 28,
        "error": {
          "message": "Expected '$19.99' but received '$19.990'",
          "stack": "at Object.<anonymous> (src/__tests__/ProductCard.test.tsx:25:5)",
          "expected": "$19.99",
          "actual": "$19.990"
        }
      }
    ],
    "run_at": "2026-03-18T13:15:00Z"
  }
}
```

---

### POST /api/v1/projects/{id}/tests/run

Trigger test execution for one or all test suites.

**Authentication:** Bearer token

**Request Body:**

```json
{
  "suite_ids": ["suite_p6q7r8", "suite_s9t1u2"],
  "coverage": true,
  "verbose": false
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `suite_ids` | array | No | Specific suites to run (default: all) |
| `coverage` | boolean | No | Generate coverage report (default: true) |
| `verbose` | boolean | No | Verbose output (default: false) |

**Response (202 Accepted):**

```json
{
  "status": "success",
  "data": {
    "run_id": "run_b8c9d1",
    "suites": ["suite_p6q7r8", "suite_s9t1u2"],
    "status": "running",
    "started_at": "2026-03-18T13:35:00Z"
  }
}
```

---

### GET /api/v1/projects/{id}/coverage

Get the code coverage report.

**Authentication:** Bearer token

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "project_id": "prj_d4e5f6",
    "overall_percent": 78.5,
    "lines": { "total": 8500, "covered": 6673, "percent": 78.5 },
    "branches": { "total": 420, "covered": 315, "percent": 75.0 },
    "functions": { "total": 180, "covered": 152, "percent": 84.4 },
    "files": [
      {
        "path": "src/components/ProductList.tsx",
        "line_percent": 92.0,
        "branch_percent": 85.0,
        "function_percent": 100.0,
        "uncovered_lines": [45, 46, 78]
      },
      {
        "path": "src/api/products.py",
        "line_percent": 88.0,
        "branch_percent": 70.0,
        "function_percent": 90.0,
        "uncovered_lines": [23, 67, 68, 69, 101]
      }
    ],
    "generated_at": "2026-03-18T13:16:00Z"
  }
}
```

**Status Codes:**

| Code | Description |
|------|-------------|
| 200 | Success |
| 401 | Unauthorized |
| 404 | No coverage data available |

---

## 11. Deployment API

### POST /api/v1/projects/{id}/deploy

Deploy a project to a target environment.

**Authentication:** Bearer token (role: `user`, `admin`)

**Request Body:**

```json
{
  "target": "vercel",
  "environment": "production",
  "config": {
    "region": "us-east-1",
    "auto_ssl": true,
    "custom_domain": "myapp.example.com",
    "env_vars": {
      "DATABASE_URL": "postgresql://...",
      "REDIS_URL": "redis://..."
    }
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `target` | string | Yes | `vercel`, `aws`, `gcp`, `azure`, `railway`, `fly`, `docker` |
| `environment` | string | No | `staging` or `production` (default: `staging`) |
| `config` | object | No | Target-specific configuration |

**Response (202 Accepted):**

```json
{
  "status": "success",
  "data": {
    "deployment_id": "dpl_e2f3g4",
    "project_id": "prj_d4e5f6",
    "target": "vercel",
    "environment": "production",
    "status": "deploying",
    "started_at": "2026-03-18T14:00:00Z"
  }
}
```

---

### GET /api/v1/projects/{id}/deployments

List all deployments for a project.

**Authentication:** Bearer token

**Response (200):**

```json
{
  "status": "success",
  "data": [
    {
      "id": "dpl_e2f3g4",
      "target": "vercel",
      "environment": "production",
      "status": "live",
      "url": "https://myapp.example.com",
      "version": "v1.0.0",
      "commit_sha": "abc123def",
      "deployed_at": "2026-03-18T14:05:00Z"
    },
    {
      "id": "dpl_h5i6j7",
      "target": "vercel",
      "environment": "staging",
      "status": "live",
      "url": "https://myapp-staging.vercel.app",
      "version": "v1.0.0-rc1",
      "deployed_at": "2026-03-18T13:50:00Z"
    }
  ]
}
```

---

### GET /api/v1/deployments/{id}

Get deployment details including logs and health status.

**Authentication:** Bearer token

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "id": "dpl_e2f3g4",
    "project_id": "prj_d4e5f6",
    "target": "vercel",
    "environment": "production",
    "status": "live",
    "url": "https://myapp.example.com",
    "version": "v1.0.0",
    "build_log_url": "https://vercel.com/builds/abc123",
    "health": {
      "status": "healthy",
      "uptime_percent": 99.9,
      "last_checked": "2026-03-18T14:10:00Z"
    },
    "resources": {
      "functions": 12,
      "static_files": 35,
      "total_size_mb": 4.2
    },
    "deployed_at": "2026-03-18T14:05:00Z",
    "deployed_by": "usr_a1b2c3"
  }
}
```

---

### POST /api/v1/deployments/{id}/rollback

Rollback to a previous deployment version.

**Authentication:** Bearer token (role: `user`, `admin`)

**Request Body:**

```json
{
  "target_deployment_id": "dpl_h5i6j7",
  "reason": "Performance regression detected"
}
```

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "rollback_id": "rb_k8l9m1",
    "from_deployment": "dpl_e2f3g4",
    "to_deployment": "dpl_h5i6j7",
    "status": "rolling_back",
    "started_at": "2026-03-18T14:20:00Z"
  }
}
```

**Status Codes:**

| Code | Description |
|------|-------------|
| 200 | Rollback initiated |
| 401 | Unauthorized |
| 404 | Deployment not found |
| 409 | Rollback already in progress |

---

### GET /api/v1/projects/{id}/deploy/targets

List all available deployment targets and their configuration requirements.

**Authentication:** Bearer token

**Response (200):**

```json
{
  "status": "success",
  "data": [
    {
      "id": "vercel",
      "name": "Vercel",
      "description": "Serverless deployment platform",
      "supported_frameworks": ["react", "nextjs", "vue", "svelte"],
      "requires_config": ["VERCEL_TOKEN"],
      "features": ["auto_ssl", "edge_functions", "preview_deploys"]
    },
    {
      "id": "aws",
      "name": "AWS",
      "description": "Amazon Web Services (ECS, Lambda, S3+CloudFront)",
      "supported_frameworks": ["any"],
      "requires_config": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION"],
      "features": ["auto_scaling", "custom_vpc", "rds_integration"]
    },
    {
      "id": "docker",
      "name": "Docker",
      "description": "Generate Dockerfile and docker-compose.yml",
      "supported_frameworks": ["any"],
      "requires_config": [],
      "features": ["multi_stage_build", "compose_file", "health_checks"]
    }
  ]
}
```

---

## 12. GitHub Integration API

### POST /api/v1/projects/{id}/github/connect

Connect a GitHub repository to the project.

**Authentication:** Bearer token

**Request Body:**

```json
{
  "repository": "org/repo-name",
  "branch": "main",
  "access_token": "ghp_xxxxxxxxxxxx",
  "auto_push": false,
  "create_repo": true,
  "visibility": "private"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `repository` | string | Yes | GitHub repo in `owner/name` format |
| `branch` | string | No | Target branch (default: `main`) |
| `access_token` | string | Yes | GitHub personal access token |
| `auto_push` | boolean | No | Auto-push on code changes (default: false) |
| `create_repo` | boolean | No | Create repo if not exists (default: false) |
| `visibility` | string | No | `public` or `private` (default: `private`) |

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "project_id": "prj_d4e5f6",
    "github_repo": "org/repo-name",
    "branch": "main",
    "connected": true,
    "repo_url": "https://github.com/org/repo-name",
    "connected_at": "2026-03-18T14:30:00Z"
  }
}
```

**Status Codes:**

| Code | Description |
|------|-------------|
| 200 | Connected |
| 400 | Invalid repository format |
| 401 | Unauthorized |
| 403 | Insufficient GitHub permissions |
| 422 | Repository does not exist and `create_repo` is false |

---

### POST /api/v1/projects/{id}/github/push

Push generated code to the connected GitHub repository.

**Authentication:** Bearer token

**Request Body:**

```json
{
  "branch": "main",
  "commit_message": "feat: initial project generation by CodeBot",
  "force": false
}
```

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "commit_sha": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
    "branch": "main",
    "files_pushed": 42,
    "repo_url": "https://github.com/org/repo-name",
    "commit_url": "https://github.com/org/repo-name/commit/a1b2c3d",
    "pushed_at": "2026-03-18T14:35:00Z"
  }
}
```

---

### POST /api/v1/projects/{id}/github/pr

Create a pull request on the connected repository.

**Authentication:** Bearer token

**Request Body:**

```json
{
  "title": "feat: Add product catalog and search functionality",
  "body": "## Changes\n- Product listing page\n- Search with filters\n- Product detail page\n\nGenerated by CodeBot pipeline pip_g7h8i9",
  "head_branch": "codebot/feature-product-catalog",
  "base_branch": "main",
  "draft": false,
  "reviewers": ["username1"],
  "labels": ["codebot-generated", "feature"]
}
```

**Response (201):**

```json
{
  "status": "success",
  "data": {
    "pr_number": 15,
    "title": "feat: Add product catalog and search functionality",
    "url": "https://github.com/org/repo-name/pull/15",
    "head_branch": "codebot/feature-product-catalog",
    "base_branch": "main",
    "status": "open",
    "created_at": "2026-03-18T14:40:00Z"
  }
}
```

---

### GET /api/v1/projects/{id}/github/actions

Get CI/CD pipeline status from GitHub Actions.

**Authentication:** Bearer token

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "repository": "org/repo-name",
    "workflows": [
      {
        "id": "wf_001",
        "name": "CI Pipeline",
        "status": "completed",
        "conclusion": "success",
        "run_number": 5,
        "branch": "main",
        "commit_sha": "a1b2c3d",
        "jobs": [
          { "name": "lint", "status": "completed", "conclusion": "success" },
          { "name": "test", "status": "completed", "conclusion": "success" },
          { "name": "build", "status": "completed", "conclusion": "success" }
        ],
        "url": "https://github.com/org/repo-name/actions/runs/123",
        "started_at": "2026-03-18T14:36:00Z",
        "completed_at": "2026-03-18T14:42:00Z"
      }
    ]
  }
}
```

---

## 13. LLM Configuration API

### GET /api/v1/llm/providers

List all configured LLM providers.

**Authentication:** Bearer token (role: `admin`)

**Response (200):**

```json
{
  "status": "success",
  "data": [
    {
      "id": "llm_openai",
      "provider": "openai",
      "display_name": "OpenAI",
      "models": ["gpt-4o", "gpt-4o-mini", "o1", "o3-mini"],
      "status": "active",
      "is_default": true,
      "usage_this_month": {
        "tokens": 1250000,
        "cost_usd": 18.50
      }
    },
    {
      "id": "llm_anthropic",
      "provider": "anthropic",
      "display_name": "Anthropic",
      "models": ["claude-sonnet-4-20250514", "claude-opus-4-20250514"],
      "status": "active",
      "is_default": false,
      "usage_this_month": {
        "tokens": 800000,
        "cost_usd": 24.00
      }
    }
  ]
}
```

---

### POST /api/v1/llm/providers

Add a new LLM provider configuration.

**Authentication:** Bearer token (role: `admin`)

**Request Body:**

```json
{
  "provider": "anthropic",
  "api_key": "sk-ant-xxxxxxxxxxxx",
  "display_name": "Anthropic Claude",
  "default_model": "claude-sonnet-4-20250514",
  "config": {
    "max_tokens": 8192,
    "temperature": 0.2,
    "base_url": "https://api.anthropic.com"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `provider` | string | Yes | `openai`, `anthropic`, `google`, `groq`, `ollama`, `custom` |
| `api_key` | string | Yes | Provider API key (stored encrypted) |
| `display_name` | string | No | Custom display name |
| `default_model` | string | No | Default model to use |
| `config` | object | No | Provider-specific configuration |

**Response (201):**

```json
{
  "status": "success",
  "data": {
    "id": "llm_anthropic",
    "provider": "anthropic",
    "display_name": "Anthropic Claude",
    "status": "active",
    "created_at": "2026-03-18T14:45:00Z"
  }
}
```

---

### PUT /api/v1/llm/providers/{id}

Update an LLM provider configuration.

**Authentication:** Bearer token (role: `admin`)

**Request Body:**

```json
{
  "default_model": "claude-opus-4-20250514",
  "config": {
    "max_tokens": 16384
  }
}
```

**Response (200):** Returns updated provider object.

---

### GET /api/v1/llm/usage

Get token usage and cost breakdown.

**Authentication:** Bearer token

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `period` | string | `month` | `day`, `week`, `month` |
| `project_id` | string | - | Filter by project |
| `provider` | string | - | Filter by provider |

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "period": "2026-03",
    "total_tokens": 2050000,
    "total_cost_usd": 42.50,
    "by_provider": [
      {
        "provider": "openai",
        "tokens": 1250000,
        "cost_usd": 18.50,
        "calls": 450
      },
      {
        "provider": "anthropic",
        "tokens": 800000,
        "cost_usd": 24.00,
        "calls": 200
      }
    ],
    "by_agent_type": [
      { "agent_type": "frontend_developer", "tokens": 520000, "cost_usd": 8.20 },
      { "agent_type": "backend_developer", "tokens": 480000, "cost_usd": 7.50 },
      { "agent_type": "planner", "tokens": 350000, "cost_usd": 6.80 }
    ],
    "daily_breakdown": [
      { "date": "2026-03-18", "tokens": 245000, "cost_usd": 5.20 },
      { "date": "2026-03-17", "tokens": 180000, "cost_usd": 3.80 }
    ]
  }
}
```

---

### POST /api/v1/llm/test

Test connectivity and configuration for an LLM provider.

**Authentication:** Bearer token (role: `admin`)

**Request Body:**

```json
{
  "provider_id": "llm_anthropic",
  "model": "claude-sonnet-4-20250514",
  "test_prompt": "Hello, respond with 'OK' if you can read this."
}
```

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "provider_id": "llm_anthropic",
    "model": "claude-sonnet-4-20250514",
    "test_result": "passed",
    "response": "OK",
    "latency_ms": 320,
    "tokens_used": 25,
    "tested_at": "2026-03-18T14:50:00Z"
  }
}
```

**Status Codes:**

| Code | Description |
|------|-------------|
| 200 | Test passed |
| 400 | Invalid provider configuration |
| 401 | Unauthorized |
| 422 | Provider connection failed |

---

## 14. WebSocket Events API

### Connection

Connect to the WebSocket endpoint for real-time events:

```
wss://<host>/ws?token=<jwt_token>&project_id=<project_id>
```

**Authentication:** JWT token passed as query parameter.

**Connection Response:**

```json
{
  "type": "connection.established",
  "data": {
    "connection_id": "ws_abc123",
    "subscriptions": ["project.prj_d4e5f6"]
  }
}
```

### Event Envelope

All WebSocket events follow this format:

```json
{
  "type": "event.name",
  "data": {},
  "meta": {
    "event_id": "evt_001",
    "timestamp": "2026-03-18T12:00:00Z",
    "project_id": "prj_d4e5f6",
    "pipeline_id": "pip_g7h8i9"
  }
}
```

### Subscription Management

**Subscribe to specific event types:**

```json
{
  "action": "subscribe",
  "channels": ["agent.*", "pipeline.*", "code.*"]
}
```

**Unsubscribe:**

```json
{
  "action": "unsubscribe",
  "channels": ["code.*"]
}
```

---

### Agent Events

**`agent.started`** -- An agent has been spawned and is beginning work.

```json
{
  "type": "agent.started",
  "data": {
    "agent_id": "agt_s7t8u9",
    "agent_type": "frontend_developer",
    "phase": "develop",
    "task": "Implement product listing page"
  }
}
```

**`agent.progress`** -- An agent reports incremental progress.

```json
{
  "type": "agent.progress",
  "data": {
    "agent_id": "agt_s7t8u9",
    "agent_type": "frontend_developer",
    "progress_percent": 60,
    "current_step": "Creating ProductCard component",
    "files_created": 3,
    "files_modified": 1
  }
}
```

**`agent.completed`** -- An agent has finished its work successfully.

```json
{
  "type": "agent.completed",
  "data": {
    "agent_id": "agt_s7t8u9",
    "agent_type": "frontend_developer",
    "duration_seconds": 180,
    "artifacts": [
      { "type": "source_file", "path": "src/components/ProductList.tsx" },
      { "type": "source_file", "path": "src/components/ProductCard.tsx" }
    ]
  }
}
```

**`agent.failed`** -- An agent has encountered an unrecoverable error.

```json
{
  "type": "agent.failed",
  "data": {
    "agent_id": "agt_s7t8u9",
    "agent_type": "frontend_developer",
    "error": {
      "code": "AGENT_LLM_ERROR",
      "message": "LLM provider returned 429 rate limit exceeded",
      "retries_exhausted": true
    },
    "will_retry": false
  }
}
```

---

### Pipeline Events

**`pipeline.phase_changed`** -- Pipeline has moved to a new phase.

```json
{
  "type": "pipeline.phase_changed",
  "data": {
    "pipeline_id": "pip_g7h8i9",
    "from_phase": "architect",
    "to_phase": "develop",
    "requires_approval": false
  }
}
```

**`pipeline.completed`** -- Pipeline has finished all phases.

```json
{
  "type": "pipeline.completed",
  "data": {
    "pipeline_id": "pip_g7h8i9",
    "total_duration_seconds": 1847,
    "phases_completed": 8,
    "files_generated": 42,
    "tests_passing": 62
  }
}
```

---

### Code Events

**`code.file_created`** -- A new file has been generated.

```json
{
  "type": "code.file_created",
  "data": {
    "path": "src/components/ProductList.tsx",
    "language": "typescript",
    "lines": 145,
    "agent_id": "agt_s7t8u9",
    "agent_type": "frontend_developer"
  }
}
```

**`code.file_updated`** -- An existing file has been modified.

```json
{
  "type": "code.file_updated",
  "data": {
    "path": "src/components/ProductList.tsx",
    "lines_added": 20,
    "lines_removed": 5,
    "version": 3,
    "agent_id": "agt_s7t8u9"
  }
}
```

---

### Test Events

**`test.started`** -- A test suite has begun execution.

```json
{
  "type": "test.started",
  "data": {
    "suite_id": "suite_p6q7r8",
    "suite_name": "Unit Tests - Frontend",
    "test_count": 28
  }
}
```

**`test.passed`** -- A test has passed.

```json
{
  "type": "test.passed",
  "data": {
    "suite_id": "suite_p6q7r8",
    "test_name": "ProductList renders correctly",
    "duration_ms": 45
  }
}
```

**`test.failed`** -- A test has failed.

```json
{
  "type": "test.failed",
  "data": {
    "suite_id": "suite_p6q7r8",
    "test_name": "ProductCard displays price correctly",
    "error": "Expected '$19.99' but received '$19.990'",
    "file": "src/__tests__/ProductCard.test.tsx",
    "line": 25
  }
}
```

---

### Review Events

**`review.comment_added`** -- A review comment has been added.

```json
{
  "type": "review.comment_added",
  "data": {
    "review_id": "rev_a1b2c3",
    "comment_id": "cmt_d4e5f6",
    "author": "usr_a1b2c3",
    "file_path": "src/api/products.py",
    "line": 45
  }
}
```

**`review.approved`** -- A review has been approved.

```json
{
  "type": "review.approved",
  "data": {
    "review_id": "rev_a1b2c3",
    "approved_by": "usr_a1b2c3"
  }
}
```

---

### Security Events

**`security.finding_detected`** -- A new security issue has been detected.

```json
{
  "type": "security.finding_detected",
  "data": {
    "finding_id": "sec_g7h8i9",
    "severity": "high",
    "title": "SQL Injection vulnerability",
    "file_path": "src/api/search.py",
    "line": 23
  }
}
```

---

### Deployment Events

**`deploy.started`** -- A deployment has been initiated.

```json
{
  "type": "deploy.started",
  "data": {
    "deployment_id": "dpl_e2f3g4",
    "target": "vercel",
    "environment": "production"
  }
}
```

**`deploy.completed`** -- A deployment has finished.

```json
{
  "type": "deploy.completed",
  "data": {
    "deployment_id": "dpl_e2f3g4",
    "target": "vercel",
    "environment": "production",
    "url": "https://myapp.example.com",
    "status": "live"
  }
}
```

---

### Brainstorming Events

**`brainstorm.message`** -- New message in a brainstorming session.

```json
{
  "type": "brainstorm.message",
  "data": {
    "session_id": "brs_w5x6y7",
    "message_id": "bmsg_010",
    "role": "assistant",
    "content": "For the AI-powered sprint planning, I recommend..."
  }
}
```

**`brainstorm.suggestion`** -- AI suggests a feature or improvement.

```json
{
  "type": "brainstorm.suggestion",
  "data": {
    "session_id": "brs_w5x6y7",
    "suggestion": "Add real-time notification system using WebSockets",
    "priority": "medium",
    "category": "feature"
  }
}
```

---

### Collaboration Events

**`collaboration.user_edit`** -- A human has edited a file.

```json
{
  "type": "collaboration.user_edit",
  "data": {
    "user_id": "usr_a1b2c3",
    "file_path": "src/components/ProductList.tsx",
    "edit_type": "content_change",
    "version": 4
  }
}
```

**`collaboration.agent_edit`** -- An agent has modified a file in response to human feedback.

```json
{
  "type": "collaboration.agent_edit",
  "data": {
    "agent_id": "agt_s7t8u9",
    "agent_type": "frontend_developer",
    "file_path": "src/components/ProductList.tsx",
    "reason": "Applied user feedback from review comment",
    "version": 5
  }
}
```

---

## 15. Project Manager API

### GET /api/v1/projects/{project_id}/reports

List project manager reports.

**Response:**

```json
{
  "status": "success",
  "data": [
    {
      "id": "rpt_abc123",
      "report_type": "STATUS_UPDATE",
      "summary": "Sprint 3 progress on track with 75% completion",
      "progress_percent": 75,
      "blockers": [
        "Waiting on third-party API credentials"
      ],
      "recommendations": [
        "Prioritize authentication module to unblock integration testing"
      ],
      "created_at": "2026-03-18T12:00:00Z"
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique report identifier |
| `report_type` | string | One of: `STATUS_UPDATE`, `BLOCKER_ALERT`, `COMPLETION_SUMMARY`, `TIMELINE_REVISION` |
| `summary` | string | Human-readable summary of the report |
| `progress_percent` | integer | Overall project progress (0-100) |
| `blockers` | array | List of current blockers |
| `recommendations` | array | AI-generated recommendations |
| `created_at` | string | ISO-8601 timestamp |

### GET /api/v1/projects/{project_id}/reports/{report_id}

Get a specific project manager report.

**Response:** Single report object (same schema as list item above).

### POST /api/v1/projects/{project_id}/reports/generate

Trigger generation of a new status report.

**Request Body:**

```json
{
  "report_type": "STATUS_UPDATE"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `report_type` | string | Yes | One of: `STATUS_UPDATE`, `BLOCKER_ALERT`, `COMPLETION_SUMMARY`, `TIMELINE_REVISION` |

**Response:** The newly generated report object.

### GET /api/v1/projects/{project_id}/timeline

Get project timeline with estimated completion.

**Response:**

```json
{
  "status": "success",
  "data": {
    "project_id": "prj_d4e5f6",
    "phases": [
      {
        "name": "Architecture & Design",
        "estimated_start": "2026-03-01T00:00:00Z",
        "estimated_end": "2026-03-05T00:00:00Z",
        "actual_start": "2026-03-01T00:00:00Z",
        "actual_end": "2026-03-04T18:00:00Z",
        "status": "completed",
        "blockers": []
      },
      {
        "name": "Implementation",
        "estimated_start": "2026-03-05T00:00:00Z",
        "estimated_end": "2026-03-15T00:00:00Z",
        "actual_start": "2026-03-05T00:00:00Z",
        "actual_end": null,
        "status": "in_progress",
        "blockers": ["Waiting on third-party API credentials"]
      }
    ]
  }
}
```

---

## 16. Observability API

### GET /api/v1/metrics

Get platform metrics in Prometheus format.

**Response:** `text/plain` (Prometheus exposition format)

Returns the following metric families:

| Metric | Type | Description |
|--------|------|-------------|
| `codebot_agent_throughput_total` | counter | Total tasks processed per agent |
| `codebot_token_usage_total` | counter | Total LLM tokens consumed |
| `codebot_cost_dollars_total` | counter | Cumulative LLM cost in USD |
| `codebot_request_latency_seconds` | histogram | API request latency |
| `codebot_error_rate` | gauge | Current error rate per endpoint |

### GET /api/v1/health

Health check endpoint.

**Response:**

```json
{
  "status": "healthy",
  "version": "2.1.0",
  "uptime_seconds": 12345,
  "agents_active": 5
}
```

### GET /api/v1/health/detailed

Detailed health check with component status.

**Response:**

```json
{
  "status": "healthy",
  "version": "2.1.0",
  "components": {
    "database": { "status": "healthy", "latency_ms": 2 },
    "redis": { "status": "healthy", "latency_ms": 1 },
    "llm_providers": {
      "anthropic": { "status": "healthy", "latency_ms": 150 },
      "openai": { "status": "healthy", "latency_ms": 200 }
    },
    "event_bus": { "status": "healthy", "latency_ms": 3 },
    "vector_store": { "status": "healthy", "latency_ms": 5 }
  }
}
```

---

## 17. Audit Log API

### GET /api/v1/audit-logs

List audit log entries with filtering.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | string | No | Filter by user ID |
| `action` | string | No | Filter by action (e.g., `project.create`, `agent.start`) |
| `resource_type` | string | No | Filter by resource type (e.g., `project`, `pipeline`, `agent`) |
| `from_date` | string | No | ISO-8601 start date |
| `to_date` | string | No | ISO-8601 end date |
| `page` | integer | No | Page number (default: 1) |
| `per_page` | integer | No | Items per page (default: 20, max: 100) |

**Response:**

```json
{
  "status": "success",
  "data": [
    {
      "id": "aud_xyz789",
      "user_id": "usr_abc123",
      "action": "project.create",
      "resource_type": "project",
      "resource_id": "prj_d4e5f6",
      "details": {
        "project_name": "My New App"
      },
      "ip_address": "192.168.1.100",
      "created_at": "2026-03-18T12:00:00Z"
    }
  ]
}
```

---

## 18. Data Retention API

### GET /api/v1/admin/retention-policies

List data retention policies.

**Response:**

```json
{
  "status": "success",
  "data": [
    {
      "id": "ret_001",
      "resource_type": "audit_logs",
      "retention_days": 90,
      "enabled": true,
      "last_cleanup_at": "2026-03-17T02:00:00Z"
    }
  ]
}
```

### PUT /api/v1/admin/retention-policies/{policy_id}

Update a retention policy.

**Request Body:**

```json
{
  "retention_days": 90,
  "enabled": true
}
```

**Response:** Updated policy object.

### POST /api/v1/admin/retention-policies/run-cleanup

Trigger manual cleanup for all enabled retention policies.

**Response:**

```json
{
  "status": "success",
  "data": {
    "policies_executed": 3,
    "records_deleted": 1520,
    "completed_at": "2026-03-18T12:05:00Z"
  }
}
```

---

## 19. Dead Letter Queue API

### GET /api/v1/admin/dlq

List dead letter queue items.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | No | Filter by status: `pending`, `replayed`, `discarded` |
| `page` | integer | No | Page number (default: 1) |
| `per_page` | integer | No | Items per page (default: 20, max: 100) |

**Response:**

```json
{
  "status": "success",
  "data": [
    {
      "id": "dlq_001",
      "original_event": "task_assignment",
      "error": "Target agent unavailable",
      "status": "pending",
      "retry_count": 3,
      "created_at": "2026-03-18T11:00:00Z"
    }
  ]
}
```

### POST /api/v1/admin/dlq/{item_id}/replay

Replay a dead letter queue item.

**Response:**

```json
{
  "status": "success",
  "data": {
    "id": "dlq_001",
    "status": "replayed",
    "replayed_at": "2026-03-18T12:10:00Z"
  }
}
```

### DELETE /api/v1/admin/dlq/{item_id}

Discard a dead letter queue item.

**Response:**

```json
{
  "status": "success",
  "data": {
    "id": "dlq_001",
    "status": "discarded",
    "discarded_at": "2026-03-18T12:10:00Z"
  }
}
```

---

## 20. Internal Agent Communication Protocol

This section documents the internal message protocol used for agent-to-agent communication via Redis Pub/Sub. These are not exposed as public API endpoints but are documented for transparency and debugging.

### Standardized Message Format

Every inter-agent message follows this standardized format:

```json
{
  "id": "msg-uuid",
  "version": "1.0",
  "type": "task_handoff | result | error | clarification | approval_request | broadcast",
  "source_agent": "string",
  "target_agent": "string | *",
  "correlation_id": "task-uuid",
  "timestamp": "ISO 8601",
  "priority": "low | normal | high | critical",
  "payload": {},
  "metadata": { "tokens_used": 0, "model": "", "duration_ms": 0 }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique message identifier (UUID) |
| `version` | string | Message format version |
| `type` | string | One of: `task_handoff`, `result`, `error`, `clarification`, `approval_request`, `broadcast` |
| `source_agent` | string | Sender agent identifier |
| `target_agent` | string | Recipient agent identifier (or `*` for broadcast) |
| `correlation_id` | string | Groups related messages for a task (UUID) |
| `timestamp` | string | ISO-8601 send time |
| `priority` | string | `low`, `normal`, `high`, `critical` |
| `payload` | object | Message-type-specific data |
| `metadata` | object | Execution metadata (tokens_used, model, duration_ms) |

### Delivery Guarantees

- **At-least-once delivery** via the event bus. Consumers must be idempotent.
- **Per source-target pair ordering guarantee.** Messages between a specific source and target agent are delivered in the order they were sent.
- **Large message handling:** Messages exceeding **100KB** are stored in blob storage; the event bus message carries a reference URI instead of the full payload.

### Message Types

#### State Flow Messages

**`task_assignment`** -- Orchestrator assigns a task to an agent.

```json
{
  "message_type": "task_assignment",
  "payload": {
    "task_id": "tsk_001",
    "description": "Implement REST API endpoints for product CRUD operations",
    "inputs": {
      "api_schema": "docs/openapi.yaml",
      "data_model": "docs/erd.json"
    },
    "constraints": {
      "framework": "fastapi",
      "style": "async",
      "max_files": 10
    },
    "deadline_seconds": 600
  }
}
```

**`task_result`** -- Agent reports task completion back to orchestrator.

```json
{
  "message_type": "task_result",
  "payload": {
    "task_id": "tsk_001",
    "status": "completed",
    "outputs": {
      "files_created": ["src/api/products.py", "src/models/product.py"],
      "files_modified": ["src/main.py"]
    },
    "metrics": {
      "tokens_used": 8500,
      "duration_seconds": 120,
      "llm_calls": 4
    }
  }
}
```

#### Message Flow Messages

**`data_request`** -- Agent requests data or artifacts from another agent.

```json
{
  "message_type": "data_request",
  "payload": {
    "request_type": "artifact",
    "artifact_type": "api_schema",
    "format": "openapi_yaml"
  }
}
```

**`data_response`** -- Agent responds with requested data.

```json
{
  "message_type": "data_response",
  "payload": {
    "request_id": "imsg_a1b2c3d4",
    "artifact_type": "api_schema",
    "content": "openapi: 3.0.0\ninfo:\n  title: Product API\n...",
    "content_type": "text/yaml"
  }
}
```

**`context_update`** -- Agent broadcasts context changes to interested agents.

```json
{
  "message_type": "context_update",
  "payload": {
    "update_type": "architecture_decision",
    "key": "auth_strategy",
    "value": "JWT with refresh tokens",
    "reason": "Selected for stateless scalability"
  }
}
```

#### Control Flow Messages

**`agent_heartbeat`** -- Periodic liveness signal.

```json
{
  "message_type": "agent_heartbeat",
  "payload": {
    "agent_id": "agt_s7t8u9",
    "status": "running",
    "current_task": "tsk_001",
    "progress_percent": 60,
    "memory_mb": 256,
    "uptime_seconds": 480
  }
}
```

**`error_escalation`** -- Agent escalates an error to the orchestrator.

```json
{
  "message_type": "error_escalation",
  "payload": {
    "error_code": "COMPILATION_ERROR",
    "severity": "high",
    "message": "TypeScript compilation failed with 3 errors",
    "context": {
      "file": "src/components/ProductList.tsx",
      "errors": [
        "TS2322: Type 'string' is not assignable to type 'number' at line 45"
      ]
    },
    "suggested_action": "request_debugger_agent",
    "retry_count": 2,
    "max_retries": 3
  }
}
```

### Agent-to-Agent Routing

Messages are routed through Redis Pub/Sub channels using this naming convention:

```
codebot:pipeline:{pipeline_id}:agent:{agent_id}     -- Direct messages
codebot:pipeline:{pipeline_id}:broadcast             -- Broadcast to all agents
codebot:pipeline:{pipeline_id}:phase:{phase_name}    -- Phase-scoped broadcast
codebot:orchestrator:{pipeline_id}                   -- Messages to orchestrator
```

### Error Escalation Protocol

When an agent encounters an error it cannot resolve:

1. **Retry** -- Agent retries the failed operation up to `max_retries` times.
2. **Self-heal** -- Agent attempts to fix the issue (e.g., debugger agent analyzes compiler errors).
3. **Escalate** -- Agent sends `error_escalation` message to orchestrator.
4. **Orchestrator decides** -- Orchestrator can:
   - Spawn a debugger agent to fix the issue.
   - Reassign the task to a different agent.
   - Pause the pipeline and request human intervention.
   - Mark the task as failed and continue with remaining work.

```
Agent Error -> Retry (up to N) -> Self-Heal -> Escalate to Orchestrator
                                                    |
                                    +---------------+---------------+
                                    |               |               |
                              Spawn Debugger   Reassign Task   Pause Pipeline
```

---

## 21. CLI Commands Reference

The CodeBot CLI (`codebot`) communicates with the API server. Below is the mapping of CLI commands to their API equivalents.

### Installation

```bash
npm install -g @codebot/cli
```

### Authentication

```bash
codebot login
# Prompts for email/password, stores JWT locally
# API: POST /api/v1/auth/login
```

```bash
codebot config set api-key <key>
# Stores API key for non-interactive use
# API: Uses X-API-Key header
```

### Project Commands

| CLI Command | API Endpoint | Description |
|-------------|-------------|-------------|
| `codebot init` | `POST /api/v1/projects` | Create a new project interactively |
| `codebot init --prd ./requirements.md` | `POST /api/v1/projects` (prd_source: file) | Create project from PRD file |
| `codebot init --url https://docs.google.com/...` | `POST /api/v1/projects` (prd_source: url) | Create project from URL |
| `codebot status` | `GET /api/v1/projects/{id}` | Show current project status |
| `codebot status --pipeline` | `GET /api/v1/pipelines/{id}` | Show pipeline status |
| `codebot list` | `GET /api/v1/projects` | List all projects |

### Pipeline Commands

| CLI Command | API Endpoint | Description |
|-------------|-------------|-------------|
| `codebot start` | `POST /api/v1/pipelines/{id}/start` | Start the pipeline |
| `codebot start --full` | `POST /api/v1/projects/{id}/pipelines` + start | Create and start full pipeline |
| `codebot pause` | `POST /api/v1/pipelines/{id}/pause` | Pause the pipeline |
| `codebot resume` | `POST /api/v1/pipelines/{id}/resume` | Resume the pipeline |
| `codebot stop` | `POST /api/v1/pipelines/{id}/cancel` | Cancel the pipeline |
| `codebot approve` | `POST /api/v1/pipelines/{id}/phases/{phase_id}/approve` | Approve a phase gate |

### Brainstorming Commands

| CLI Command | API Endpoint | Description |
|-------------|-------------|-------------|
| `codebot brainstorm` | `POST /api/v1/projects/{id}/brainstorm` | Start interactive brainstorming |
| `codebot brainstorm --finalize` | `POST .../brainstorm/{session_id}/finalize` | Finalize session into PRD |

### Review & Testing Commands

| CLI Command | API Endpoint | Description |
|-------------|-------------|-------------|
| `codebot review` | `GET /api/v1/projects/{id}/reviews` | Show latest code review |
| `codebot review --approve` | `POST /api/v1/reviews/{id}/approve` | Approve review |
| `codebot test` | `POST /api/v1/projects/{id}/tests/run` | Run all tests |
| `codebot test --coverage` | `GET /api/v1/projects/{id}/coverage` | Show coverage report |
| `codebot security` | `GET /api/v1/projects/{id}/security` | Show security scan results |

### Template & Tech Stack Commands

| CLI Command | API Endpoint | Description |
|-------------|-------------|-------------|
| `codebot template list` | `GET /api/v1/templates` | List available templates |
| `codebot template use <id>` | Used during `POST /api/v1/projects` | Apply a template |
| `codebot techstack list` | `GET /api/v1/techstacks` | List tech stacks |
| `codebot techstack recommend` | `POST /api/v1/techstacks/recommend` | Get AI recommendation |

### Deployment Commands

| CLI Command | API Endpoint | Description |
|-------------|-------------|-------------|
| `codebot deploy` | `POST /api/v1/projects/{id}/deploy` | Deploy interactively |
| `codebot deploy --target vercel` | `POST /api/v1/projects/{id}/deploy` | Deploy to Vercel |
| `codebot deploy --target docker` | `POST /api/v1/projects/{id}/deploy` | Generate Docker files |
| `codebot deploy status` | `GET /api/v1/deployments/{id}` | Get deployment status |
| `codebot deploy rollback` | `POST /api/v1/deployments/{id}/rollback` | Rollback deployment |

### Configuration Commands

| CLI Command | API Endpoint | Description |
|-------------|-------------|-------------|
| `codebot config set <key> <value>` | `PUT /api/v1/auth/settings` | Update settings |
| `codebot config get <key>` | `GET /api/v1/auth/me` | Get current config |
| `codebot config llm add` | `POST /api/v1/llm/providers` | Add LLM provider |
| `codebot config llm test` | `POST /api/v1/llm/test` | Test LLM connection |

### Example CLI Session

```bash
# Initialize a new project
$ codebot init --prd ./my-app-requirements.md --name "My App"
Project created: prj_d4e5f6

# Start brainstorming to refine requirements
$ codebot brainstorm
Starting brainstorming session...
AI: What is the primary user persona for this application?
You: Engineering managers at mid-size companies
AI: Great! Here are some feature suggestions...
...
$ codebot brainstorm --finalize

# Start the build pipeline
$ codebot start --full
Pipeline pip_g7h8i9 started. 8 phases to complete.
Phase 1/8: brainstorm ... completed (2m 00s)
Phase 2/8: plan ........ completed (4m 00s)
Phase 3/8: architect ... completed (3m 30s)
Phase 4/8: design ...... completed (5m 00s)
Phase 5/8: develop ..... running (12 of 20 tasks complete)

# Check status
$ codebot status
Project: My App (prj_d4e5f6)
Status: building (62% complete)
Files: 42 | Lines: 8,500 | Tests: 62/65 passing

# Review and deploy
$ codebot review --approve
$ codebot deploy --target vercel
Deploying to Vercel... done!
Live at: https://my-app.vercel.app
```

---

## 22. Python SDK Reference

### Installation

```bash
pip install codebot-sdk
```

### Client Initialization

```python
from codebot import CodeBotClient

# Using API key
client = CodeBotClient(api_key="cb_live_xxxxxxxxxxxx")

# Using JWT token
client = CodeBotClient(token="eyJhbGciOiJSUzI1NiIs...")

# Custom server
client = CodeBotClient(
    api_key="cb_live_xxxxxxxxxxxx",
    base_url="https://codebot.mycompany.com/api/v1"
)
```

### Project Management

```python
# Create a project from PRD text
project = client.projects.create(
    name="E-Commerce Platform",
    prd_content="Build an e-commerce platform with user auth, "
                "product catalog, shopping cart, and Stripe payments.",
    tech_stack_id="ts_react_fastapi",
    settings={
        "enable_tests": True,
        "enable_security_scan": True
    }
)
print(f"Project created: {project.id}")

# Create from a PRD file
with open("requirements.md", "r") as f:
    project = client.projects.create(
        name="My App",
        prd_source="file",
        prd_content=f.read()
    )

# List projects
projects = client.projects.list(status="building", page=1, per_page=10)
for p in projects.data:
    print(f"{p.name} - {p.status} ({p.progress_percent}%)")

# Get project details
project = client.projects.get("prj_d4e5f6")
print(f"Files: {project.stats.files_generated}")
print(f"Coverage: {project.stats.test_coverage_percent}%")

# Delete a project
client.projects.delete("prj_d4e5f6")
```

### Pipeline Execution

```python
# Create and start a pipeline
pipeline = client.pipelines.create(
    project_id="prj_d4e5f6",
    mode="full",
    config={"auto_approve_gates": False, "parallel_agents": 5}
)

# Start the pipeline
client.pipelines.start(pipeline.id)

# Monitor progress
import time

while True:
    status = client.pipelines.get(pipeline.id)
    print(f"Phase: {status.current_phase} | "
          f"Progress: {status.progress_percent}%")
    if status.status in ("completed", "failed", "cancelled"):
        break
    time.sleep(10)

# Approve a phase gate
phases = client.pipelines.list_phases(pipeline.id)
for phase in phases:
    if phase.gate_status == "pending":
        client.pipelines.approve_phase(
            pipeline.id,
            phase.id,
            comment="Looks good, proceed."
        )

# Restore a checkpoint
checkpoints = client.pipelines.list_checkpoints(pipeline.id)
client.pipelines.restore_checkpoint(pipeline.id, checkpoints[0].id)
```

### Real-Time Events (Async)

```python
import asyncio
from codebot import CodeBotAsyncClient

async def main():
    client = CodeBotAsyncClient(api_key="cb_live_xxxxxxxxxxxx")

    async with client.ws.connect(project_id="prj_d4e5f6") as ws:
        await ws.subscribe(["agent.*", "pipeline.*", "code.*"])

        async for event in ws.events():
            if event.type == "agent.progress":
                print(f"Agent {event.data.agent_type}: "
                      f"{event.data.progress_percent}%")
            elif event.type == "code.file_created":
                print(f"New file: {event.data.path}")
            elif event.type == "pipeline.completed":
                print("Pipeline finished!")
                break

asyncio.run(main())
```

### Code & Artifacts

```python
# Get file tree
tree = client.projects.get_tree("prj_d4e5f6")
for item in tree.children:
    print(f"{'[dir]' if item.type == 'directory' else '     '} {item.name}")

# Read a file
file = client.projects.get_file("prj_d4e5f6", "src/components/ProductList.tsx")
print(file.content)

# Get diff
diff = client.projects.get_diff("prj_d4e5f6")
print(f"Files changed: {diff.files_changed}")
print(f"+{diff.insertions} -{diff.deletions}")

# Human edit a file
client.projects.edit_file(
    "prj_d4e5f6",
    "src/components/ProductList.tsx",
    content="// Updated content\n...",
    comment="Manual fix for layout issue"
)
```

### Testing & Security

```python
# Run tests
run = client.tests.run("prj_d4e5f6", coverage=True)
print(f"Test run started: {run.run_id}")

# Get coverage
coverage = client.projects.get_coverage("prj_d4e5f6")
print(f"Overall coverage: {coverage.overall_percent}%")

# Security scan
security = client.security.get_summary("prj_d4e5f6")
print(f"Findings: {security.summary.total} "
      f"({security.summary.critical} critical)")

# List findings
findings = client.security.list_findings(
    "prj_d4e5f6",
    severity="high"
)
for f in findings:
    print(f"[{f.severity}] {f.title} - {f.file_path}:{f.line}")
```

### Deployment

```python
# Deploy to Vercel
deployment = client.deploy.create(
    project_id="prj_d4e5f6",
    target="vercel",
    environment="production",
    config={"custom_domain": "myapp.example.com"}
)

# Wait for deployment
import time
while True:
    status = client.deploy.get(deployment.deployment_id)
    if status.status == "live":
        print(f"Live at: {status.url}")
        break
    elif status.status == "failed":
        print("Deployment failed!")
        break
    time.sleep(5)

# Rollback
client.deploy.rollback(
    deployment.deployment_id,
    reason="Performance regression"
)
```

### LLM Configuration

```python
# List providers
providers = client.llm.list_providers()
for p in providers:
    print(f"{p.display_name}: {p.usage_this_month.cost_usd} USD")

# Get usage
usage = client.llm.get_usage(period="month")
print(f"Total tokens: {usage.total_tokens:,}")
print(f"Total cost: ${usage.total_cost_usd:.2f}")
```

---

## 23. Error Codes Reference

All error codes follow the pattern `CATEGORY_SPECIFIC_ERROR`. The `error.code` field in error responses always contains one of these values.

### Authentication Errors (AUTH_*)

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `AUTH_INVALID_CREDENTIALS` | 401 | Email or password is incorrect |
| `AUTH_TOKEN_EXPIRED` | 401 | JWT access token has expired |
| `AUTH_TOKEN_INVALID` | 401 | JWT token is malformed or signature invalid |
| `AUTH_REFRESH_TOKEN_EXPIRED` | 401 | Refresh token has expired |
| `AUTH_REFRESH_TOKEN_INVALID` | 401 | Refresh token is invalid |
| `AUTH_API_KEY_INVALID` | 401 | API key is invalid or revoked |
| `AUTH_INSUFFICIENT_ROLE` | 403 | User role lacks permission for this action |
| `AUTH_ACCOUNT_LOCKED` | 403 | Account locked due to too many failed attempts |
| `AUTH_EMAIL_EXISTS` | 409 | Email address already registered |

### Validation Errors (VALIDATION_*)

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Generic field validation failure |
| `VALIDATION_REQUIRED_FIELD` | 400 | A required field is missing |
| `VALIDATION_INVALID_FORMAT` | 400 | Field value format is invalid |
| `VALIDATION_VALUE_TOO_LONG` | 400 | Field value exceeds max length |
| `VALIDATION_VALUE_TOO_SHORT` | 400 | Field value below min length |
| `VALIDATION_INVALID_ENUM` | 400 | Value not in allowed enum set |

### Project Errors (PROJECT_*)

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `PROJECT_NOT_FOUND` | 404 | Project does not exist or not accessible |
| `PROJECT_ALREADY_EXISTS` | 409 | Project with this name already exists |
| `PROJECT_DELETE_ACTIVE_PIPELINE` | 409 | Cannot delete project with active pipeline |
| `PROJECT_PRD_PARSE_FAILED` | 422 | Failed to parse the provided PRD |
| `PROJECT_IMPORT_FAILED` | 422 | Codebase import failed |
| `PROJECT_REPO_INACCESSIBLE` | 422 | Cannot access the specified repository |

### Pipeline Errors (PIPELINE_*)

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `PIPELINE_NOT_FOUND` | 404 | Pipeline does not exist |
| `PIPELINE_ALREADY_RUNNING` | 400 | Pipeline is already in running state |
| `PIPELINE_NOT_RUNNING` | 400 | Cannot pause/resume a pipeline that is not running |
| `PIPELINE_ALREADY_COMPLETED` | 400 | Pipeline has already completed |
| `PIPELINE_CHECKPOINT_NOT_FOUND` | 404 | Checkpoint does not exist |
| `PIPELINE_RESTORE_WHILE_RUNNING` | 409 | Must pause pipeline before restoring checkpoint |
| `PIPELINE_PHASE_NOT_PENDING` | 400 | Phase is not awaiting approval |

### Agent Errors (AGENT_*)

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `AGENT_NOT_FOUND` | 404 | Agent instance does not exist |
| `AGENT_NOT_RUNNING` | 400 | Agent is not in running state |
| `AGENT_ALREADY_STOPPED` | 400 | Agent is already stopped |
| `AGENT_LLM_ERROR` | 502 | LLM provider returned an error |
| `AGENT_LLM_RATE_LIMITED` | 429 | LLM provider rate limit hit |
| `AGENT_TIMEOUT` | 504 | Agent task exceeded time limit |
| `AGENT_CONTEXT_OVERFLOW` | 422 | Agent context window exceeded |
| `AGENT_DEPENDENCY_FAILED` | 424 | Upstream agent dependency failed |

### Code & File Errors (FILE_*)

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `FILE_NOT_FOUND` | 404 | File does not exist in project |
| `FILE_CONCURRENT_EDIT` | 409 | File was modified by another user/agent |
| `FILE_TOO_LARGE` | 413 | File exceeds maximum size limit |
| `FILE_INVALID_ENCODING` | 400 | File content is not valid UTF-8 |

### Review & Security Errors (REVIEW_*, SECURITY_*)

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `REVIEW_NOT_FOUND` | 404 | Review does not exist |
| `REVIEW_ALREADY_APPROVED` | 400 | Review was already approved |
| `SECURITY_SCAN_RUNNING` | 409 | A security scan is already in progress |
| `SECURITY_SCAN_FAILED` | 500 | Security scan encountered an error |

### Deployment Errors (DEPLOY_*)

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `DEPLOY_TARGET_INVALID` | 400 | Deployment target is not supported |
| `DEPLOY_CONFIG_MISSING` | 400 | Required deployment configuration missing |
| `DEPLOY_IN_PROGRESS` | 409 | A deployment is already in progress |
| `DEPLOY_FAILED` | 500 | Deployment failed |
| `DEPLOY_ROLLBACK_NOT_FOUND` | 404 | Target deployment for rollback not found |
| `DEPLOY_ROLLBACK_IN_PROGRESS` | 409 | A rollback is already in progress |

### GitHub Errors (GITHUB_*)

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `GITHUB_NOT_CONNECTED` | 400 | Project is not connected to a GitHub repo |
| `GITHUB_AUTH_FAILED` | 403 | GitHub token lacks required permissions |
| `GITHUB_REPO_NOT_FOUND` | 404 | GitHub repository does not exist |
| `GITHUB_PUSH_FAILED` | 500 | Failed to push code to GitHub |
| `GITHUB_PR_CREATE_FAILED` | 500 | Failed to create pull request |

### LLM Errors (LLM_*)

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `LLM_PROVIDER_NOT_FOUND` | 404 | LLM provider configuration not found |
| `LLM_PROVIDER_INVALID` | 400 | Invalid provider type |
| `LLM_CONNECTION_FAILED` | 422 | Cannot connect to LLM provider |
| `LLM_API_KEY_INVALID` | 401 | LLM provider API key is invalid |
| `LLM_RATE_LIMITED` | 429 | LLM provider rate limit exceeded |
| `LLM_MODEL_NOT_FOUND` | 404 | Specified model not available |

### System Errors (SYSTEM_*)

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `SYSTEM_INTERNAL_ERROR` | 500 | Unexpected internal server error |
| `SYSTEM_DATABASE_ERROR` | 500 | Database connection or query failure |
| `SYSTEM_REDIS_ERROR` | 500 | Redis connection failure |
| `SYSTEM_RATE_LIMIT_EXCEEDED` | 429 | API rate limit exceeded |
| `SYSTEM_MAINTENANCE` | 503 | System is under maintenance |
| `SYSTEM_RESOURCE_EXHAUSTED` | 503 | Server resources exhausted |

### Error Response Examples

**Validation Error:**

```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      { "field": "name", "issue": "Field is required" },
      { "field": "prd_source", "issue": "Must be one of: text, file, url" }
    ]
  },
  "meta": {
    "request_id": "req_err001",
    "timestamp": "2026-03-18T12:00:00Z"
  }
}
```

**Resource Not Found:**

```json
{
  "status": "error",
  "error": {
    "code": "PROJECT_NOT_FOUND",
    "message": "Project 'prj_invalid' does not exist or you do not have access"
  },
  "meta": {
    "request_id": "req_err002",
    "timestamp": "2026-03-18T12:00:01Z"
  }
}
```

**Rate Limit Exceeded:**

```json
{
  "status": "error",
  "error": {
    "code": "SYSTEM_RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 30 seconds.",
    "details": [
      { "field": "retry_after_seconds", "issue": "30" }
    ]
  },
  "meta": {
    "request_id": "req_err003",
    "timestamp": "2026-03-18T12:00:02Z"
  }
}
```

---

*End of CodeBot API Specification v1.0.0*
