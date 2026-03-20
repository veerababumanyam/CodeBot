# Phase 10: FastAPI Server + API Layer - Context

**Gathered:** 2026-03-20
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase exposes the entire CodeBot system through a REST API and WebSocket interface. Users and frontends can create/manage projects, control pipelines (start/stop/pause/resume), manage individual agents, and receive real-time updates. Authentication via JWT with refresh tokens. Standard response envelope for all endpoints.

</domain>

<decisions>
## Implementation Decisions

### API Design & Authentication
- JWT with refresh tokens for stateless authentication
- Standard response envelope: `{data, error, meta}` for all endpoints
- RESTful CRUD + action endpoints for pipeline control (`POST /pipelines/{id}/start`, etc.)
- Per-user rate limits via middleware (100 req/min default, configurable)

### WebSocket & Real-time Updates
- Socket.IO for WebSocket transport — auto-reconnect, room-based subscriptions
- Stream pipeline phase transitions, agent status changes, and log output to clients
- Individual agent control via API — start, stop, restart, reconfigure endpoints
- Auto-generated OpenAPI docs via FastAPI at `/docs` and `/redoc`

### Claude's Discretion
- Specific endpoint URL patterns and request/response schemas
- Middleware ordering and dependency injection patterns
- Error code taxonomy and HTTP status code mapping

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `apps/server/src/codebot/db/` — Full ORM layer (SQLAlchemy models, migrations)
- `apps/server/src/codebot/pipeline/` — Pipeline lifecycle, workflows, gates
- `apps/server/src/codebot/agents/registry.py` — Agent registry with 30 agents
- `apps/server/src/codebot/events/bus.py` — NATS event bus for real-time events

### Established Patterns
- Pydantic v2 for all request/response schemas
- FastAPI dependency injection for services
- Async-first with asyncio.TaskGroup

### Integration Points
- API routes in `apps/server/src/codebot/api/` (new directory)
- WebSocket handler in `apps/server/src/codebot/api/ws.py`
- Auth middleware in `apps/server/src/codebot/api/auth.py`
- Main app in `apps/server/src/codebot/main.py`

</code_context>

<specifics>
## Specific Ideas

No specific requirements — follow API_SPECIFICATION.md for endpoint definitions.

</specifics>

<deferred>
## Deferred Ideas

- OAuth2 social login — deferred to post-v1.0
- API versioning (v1/v2) — deferred to post-v1.0
- GraphQL alternative endpoint — deferred to post-v1.0

</deferred>
