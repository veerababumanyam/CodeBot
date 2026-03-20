---
phase: 10-fastapi-server-api-layer
plan: 01
subsystem: api
tags: [fastapi, jwt, bcrypt, pydantic, sqlalchemy, auth, crud, rbac, slowapi]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: SQLAlchemy ORM models (User, ApiKey, Project), DB engine, config.py
provides:
  - JWT token creation/verification (create_access_token, create_refresh_token, decode_token)
  - Password hashing (hash_password, verify_password)
  - API key generation and hashing
  - Response envelope models (ResponseEnvelope, PaginatedEnvelope, ErrorResponse)
  - FastAPI dependency injection (get_db, get_current_user, require_role)
  - CORS, rate limiting, request-ID middleware
  - Auth endpoints (register, login, refresh, logout, me, api-keys)
  - Project CRUD endpoints (create, list, get, update, delete)
  - AuthService and ProjectService business logic layer
  - API test infrastructure with savepoint-based transaction isolation
affects: [10-02-PLAN, dashboard, cli, pipeline-api, agent-api]

# Tech tracking
tech-stack:
  added: [pyjwt[crypto], bcrypt, slowapi, email-validator]
  patterns: [Annotated[T, Depends()] for DI, ResponseEnvelope[T] generics, savepoint test isolation, service layer pattern]

key-files:
  created:
    - apps/server/src/codebot/auth/jwt.py
    - apps/server/src/codebot/auth/password.py
    - apps/server/src/codebot/auth/api_key.py
    - apps/server/src/codebot/api/envelope.py
    - apps/server/src/codebot/api/deps.py
    - apps/server/src/codebot/api/middleware.py
    - apps/server/src/codebot/api/schemas/auth.py
    - apps/server/src/codebot/api/schemas/projects.py
    - apps/server/src/codebot/api/routes/auth.py
    - apps/server/src/codebot/api/routes/projects.py
    - apps/server/src/codebot/api/routes/health.py
    - apps/server/src/codebot/services/auth_service.py
    - apps/server/src/codebot/services/project_service.py
    - apps/server/tests/api/conftest.py
    - apps/server/tests/api/test_auth.py
    - apps/server/tests/api/test_projects.py
  modified:
    - apps/server/pyproject.toml
    - apps/server/src/codebot/config.py
    - apps/server/src/codebot/main.py

key-decisions:
  - "Annotated[T, Depends()] pattern instead of default Depends() to satisfy ruff B008"
  - "Pydantic Generic[T] with noqa UP046 -- Pydantic requires Generic subclass syntax, not Python 3.12 type params"
  - "Savepoint-based test isolation with after_transaction_end event for clean rollback"
  - "raise HTTPException from None in exception handlers to satisfy ruff B904"
  - "datetime.UTC alias instead of timezone.utc per ruff UP017"

patterns-established:
  - "Service layer pattern: route -> service -> ORM for all business logic"
  - "Annotated[T, Depends(dep)] for all FastAPI dependency injection"
  - "ResponseEnvelope[T] and PaginatedEnvelope[T] for all API responses"
  - "Savepoint transaction isolation in API test conftest for clean rollback"
  - "field_validator(mode='before') for ORM enum-to-string conversion in response schemas"

requirements-completed: [SRVR-01, SRVR-03]

# Metrics
duration: 8min
completed: 2026-03-20
---

# Phase 10 Plan 01: API Foundation Summary

**JWT auth with bcrypt password hashing, response envelope contract, RBAC dependency injection, and project CRUD endpoints with 14 passing integration tests**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-20T09:26:05Z
- **Completed:** 2026-03-20T09:34:44Z
- **Tasks:** 2
- **Files modified:** 30

## Accomplishments
- Complete JWT auth flow (register, login, refresh, logout, /me) with bcrypt password hashing
- Project CRUD (create, list with pagination, get, update, delete) with ownership verification
- Role-based access control enforced via require_role dependency (viewers blocked from creating projects)
- Standard response envelope contract (ResponseEnvelope[T], PaginatedEnvelope[T], ErrorResponse)
- CORS, rate limiting (slowapi), and X-Request-ID middleware
- API key authentication alongside Bearer token auth
- 14 integration tests with savepoint-based transaction isolation

## Task Commits

Each task was committed atomically:

1. **Task 1: Auth module, response envelope, deps, middleware, and config updates** - `1e20d8c` (feat)
2. **Task 2: Auth and project routes with service layer, main.py wiring, and tests** - `eb7e6e8` (feat)

## Files Created/Modified
- `apps/server/src/codebot/auth/jwt.py` - JWT create/decode with HS256
- `apps/server/src/codebot/auth/password.py` - bcrypt hash/verify
- `apps/server/src/codebot/auth/api_key.py` - API key generation with SHA-256
- `apps/server/src/codebot/api/envelope.py` - ResponseEnvelope, PaginatedEnvelope, ErrorResponse
- `apps/server/src/codebot/api/deps.py` - get_db, get_current_user, require_role
- `apps/server/src/codebot/api/middleware.py` - CORS, rate limit, request-ID
- `apps/server/src/codebot/api/schemas/auth.py` - Auth request/response Pydantic models
- `apps/server/src/codebot/api/schemas/projects.py` - Project request/response models
- `apps/server/src/codebot/api/schemas/common.py` - PaginationParams
- `apps/server/src/codebot/api/routes/auth.py` - 7 auth endpoints
- `apps/server/src/codebot/api/routes/projects.py` - 5 project endpoints
- `apps/server/src/codebot/api/routes/health.py` - Health check (extracted from main.py)
- `apps/server/src/codebot/services/auth_service.py` - AuthService business logic
- `apps/server/src/codebot/services/project_service.py` - ProjectService with pagination
- `apps/server/src/codebot/main.py` - Router wiring with lifespan
- `apps/server/src/codebot/config.py` - JWT/CORS/rate-limit settings
- `apps/server/pyproject.toml` - New dependencies
- `apps/server/tests/api/conftest.py` - Test fixtures with savepoint isolation
- `apps/server/tests/api/test_auth.py` - 8 auth tests
- `apps/server/tests/api/test_projects.py` - 6 project tests

## Decisions Made
- **Annotated[T, Depends()]**: Used Annotated type hints for all FastAPI Depends() calls to satisfy ruff B008 rule against function calls in default arguments
- **Pydantic Generic[T]**: Kept Generic[T] subclass syntax with noqa UP046 because Pydantic v2 does not support Python 3.12 type parameter syntax for generic models
- **Savepoint test isolation**: Used SQLAlchemy after_transaction_end event to restart nested savepoints after each commit(), enabling service code to call commit() while maintaining test-level rollback
- **datetime.UTC**: Used datetime.UTC alias instead of timezone.utc per ruff UP017 recommendation

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed lint violations across all new files**
- **Found during:** Task 2
- **Issue:** Ruff flagged B008 (Depends in defaults), B904 (raise from), UP046 (Generic), UP017 (UTC alias), I001 (import sort), F401 (unused import), S105 (false positive password)
- **Fix:** Switched to Annotated[T, Depends()] pattern, added `from None` to exception reraises, added noqa for Pydantic-required Generic[T], auto-fixed import order and unused imports
- **Files modified:** deps.py, envelope.py, routes/auth.py, routes/projects.py, schemas/auth.py, services/auth_service.py, services/project_service.py, auth/jwt.py
- **Verification:** `ruff check` passes with zero errors
- **Committed in:** eb7e6e8 (Task 2 commit)

**2. [Rule 3 - Blocking] Fixed savepoint transaction isolation for API tests**
- **Found during:** Task 2
- **Issue:** Initial conftest using begin_nested() with yield failed because service commit() closed the outer transaction
- **Fix:** Used connection-scoped transaction with after_transaction_end event to automatically restart savepoints after each commit
- **Files modified:** tests/api/conftest.py
- **Verification:** All 14 tests pass, no data leaks between tests
- **Committed in:** eb7e6e8 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking)
**Impact on plan:** Both auto-fixes necessary for correctness and test reliability. No scope creep.

## Issues Encountered
- Leftover test data from a failed initial test run (before savepoint fix) had to be manually cleaned from the database before tests could pass

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Auth foundation complete: JWT, password hashing, API keys, RBAC
- Response envelope contract established for all future endpoints
- Service layer pattern established for all future routes
- Test infrastructure ready for additional API test suites
- Ready for Plan 02 (pipeline management, agent management, WebSocket endpoints)

---
*Phase: 10-fastapi-server-api-layer*
*Plan: 01*
*Completed: 2026-03-20*
