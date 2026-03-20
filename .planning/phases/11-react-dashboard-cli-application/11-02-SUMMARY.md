---
phase: 11-react-dashboard-cli-application
plan: 02
subsystem: cli
tags: [commander, chalk, ora, inquirer, websocket, typescript, vitest, esm]

# Dependency graph
requires:
  - phase: 10-fastapi-server-api-layer
    provides: REST API endpoints and WebSocket streaming the CLI consumes
provides:
  - "@codebot/cli TypeScript package with commander-based CLI"
  - "CodeBotClient async API client wrapping all Phase 10 REST endpoints"
  - "WebSocket log streaming with chalk-formatted real-time output"
  - "Project create/list/delete, pipeline start/pause/resume/stop commands"
  - "Agent list/logs monitoring commands"
  - "Config preset/show/set with ~/.codebot/config.json persistence"
  - "Top-level convenience aliases (create, start, logs)"
  - "Vitest test suite with 14 passing tests"
affects: [12-testing-documentation-polish]

# Tech tracking
tech-stack:
  added: [commander@13, "@inquirer/prompts@7", chalk@5, ora@8, ws@8, vitest@3, tsx@4]
  patterns: [native-fetch-api-client, websocket-log-streaming, cli-command-groups, config-file-persistence]

key-files:
  created:
    - apps/cli/src/index.ts
    - apps/cli/src/types.ts
    - apps/cli/src/client/api.ts
    - apps/cli/src/client/streaming.ts
    - apps/cli/src/output/formatters.ts
    - apps/cli/src/output/spinners.ts
    - apps/cli/src/commands/project.ts
    - apps/cli/src/commands/pipeline.ts
    - apps/cli/src/commands/agent.ts
    - apps/cli/src/commands/config.ts
    - apps/cli/tests/project.test.ts
    - apps/cli/tests/pipeline.test.ts
    - apps/cli/tests/agent.test.ts
    - apps/cli/vitest.config.ts
  modified:
    - apps/cli/package.json
    - apps/cli/tsconfig.json
    - pnpm-lock.yaml

key-decisions:
  - "Native fetch for API client instead of axios/got -- zero additional HTTP deps for Node 22 LTS"
  - "exactOptionalPropertyTypes requires explicit RequestInit construction to avoid body: undefined type error"
  - "token field uses `token?: string | undefined` for exactOptionalPropertyTypes compliance"
  - "Top-level command aliases (create, start, logs) registered alongside subcommand groups for DX"
  - "Tests mock global fetch directly rather than testing through Commander to avoid interactive prompt issues"

patterns-established:
  - "CLI command registration: registerXxxCommands(program) pattern for modular command groups"
  - "API error handling: CodeBotAPIError with statusCode for 401 auth gate messaging"
  - "Config persistence: ~/.codebot/config.json with loadConfig/saveConfig helpers"
  - "Preset mapping: review-only -> review_only at command boundary before API call"

requirements-completed: [CLI-01, CLI-02, CLI-03, CLI-04]

# Metrics
duration: 5min
completed: 2026-03-20
---

# Phase 11 Plan 02: CLI Application Summary

**Commander-based TypeScript CLI with project/pipeline/agent/config commands, native fetch API client, WebSocket log streaming, and 14-test Vitest suite**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-20T09:59:29Z
- **Completed:** 2026-03-20T10:04:40Z
- **Tasks:** 2
- **Files modified:** 17

## Accomplishments
- Full CLI application with 4 command groups (project, pipeline, agent, config) plus top-level shortcuts
- Native fetch API client wrapping all Phase 10 REST endpoints with typed responses
- WebSocket log streaming with chalk-formatted real-time agent output
- 14 Vitest tests covering API client operations, formatters, and error handling

## Task Commits

Each task was committed atomically:

1. **Task 1: TypeScript CLI package scaffold, API client, streaming, formatters** - `f24236a` (feat)
2. **Task 2: Commander command implementations and Vitest test suite** - `0d5dc35` (feat)

## Files Created/Modified
- `apps/cli/package.json` - ESM package with commander, chalk, ora, inquirer, ws, vitest
- `apps/cli/tsconfig.json` - Strict TypeScript with NodeNext modules and exactOptionalPropertyTypes
- `apps/cli/vitest.config.ts` - Vitest configuration for Node environment
- `apps/cli/src/index.ts` - Commander entry point with command groups and global options
- `apps/cli/src/types.ts` - Shared response/request types matching Phase 10 API schema
- `apps/cli/src/client/api.ts` - CodeBotClient class with native fetch for all REST endpoints
- `apps/cli/src/client/streaming.ts` - WebSocket log streaming with chalk level colors
- `apps/cli/src/output/formatters.ts` - Table formatters for projects, pipelines, agents
- `apps/cli/src/output/spinners.ts` - Ora spinner utility
- `apps/cli/src/commands/project.ts` - Project create/list/delete with inquirer prompts
- `apps/cli/src/commands/pipeline.ts` - Pipeline start/pause/resume/stop with preset mapping
- `apps/cli/src/commands/agent.ts` - Agent list and real-time log streaming
- `apps/cli/src/commands/config.ts` - Config preset/show/set with ~/.codebot/config.json
- `apps/cli/tests/project.test.ts` - 5 tests for project API client and formatters
- `apps/cli/tests/pipeline.test.ts` - 6 tests for pipeline API client and formatters
- `apps/cli/tests/agent.test.ts` - 3 tests for agent API client and formatters

## Decisions Made
- Used native fetch instead of axios/got for zero additional HTTP dependencies on Node 22 LTS
- exactOptionalPropertyTypes requires explicit RequestInit construction (body cannot be `undefined`, must be omitted)
- Token field uses `token?: string | undefined` union for exactOptionalPropertyTypes compliance in CLIConfig
- Top-level command aliases (create, start, logs) registered alongside subcommand groups for developer convenience
- Tests mock global fetch directly to avoid interactive prompt complexity in Commander action testing

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed RequestInit body type with exactOptionalPropertyTypes**
- **Found during:** Task 1 (API client implementation)
- **Issue:** `body: body ? JSON.stringify(body) : undefined` fails TypeScript check because exactOptionalPropertyTypes makes `body: string | undefined` incompatible with `body: BodyInit | null`
- **Fix:** Construct RequestInit object explicitly and only add body property when body is defined
- **Files modified:** apps/cli/src/client/api.ts
- **Verification:** `tsc --noEmit` passes cleanly
- **Committed in:** f24236a (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minor TypeScript strict mode adjustment. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- CLI package complete and ready for integration testing in Phase 12
- All 4 CLI requirements (CLI-01 through CLI-04) implemented
- Dashboard (11-01) and CLI (11-02) provide complete user interfaces for the platform

## Self-Check: PASSED

All 17 files verified present. Both task commits (f24236a, 0d5dc35) confirmed in git history.

---
*Phase: 11-react-dashboard-cli-application*
*Completed: 2026-03-20*
