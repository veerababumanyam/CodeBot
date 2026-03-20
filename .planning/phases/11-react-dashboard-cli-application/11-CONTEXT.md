# Phase 11: React Dashboard + CLI Application - Context

**Gathered:** 2026-03-20
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase builds two user interfaces: (1) a React web dashboard with real-time pipeline visualization (React Flow), agent monitoring, code viewer (Monaco), and terminal (xterm.js), and (2) a TypeScript CLI for project creation, pipeline control, and log streaming. Also implements Creator agents (Skill, Hooks, Tools) as stubs registered in the agent registry.

</domain>

<decisions>
## Implementation Decisions

### Dashboard Architecture
- React Flow with custom nodes for pipeline graph — node per agent, edges per dependencies, real-time status colors
- Socket.IO client matching server for real-time updates with auto-reconnect and room subscriptions
- Zustand for client state + TanStack Query for server state (per CLAUDE.md stack decisions)
- Monaco editor in read-only mode for generated code viewing — editing deferred to post-v1.0

### CLI Design & Creator Agents
- Commander.js + chalk + ora for CLI framework (per CLAUDE.md stack)
- SSE from API server for log streaming — lightweight, unidirectional
- Creator agents (Skill/Hooks/Tools) as stub implementations — register in registry, accept input, return placeholder. Full implementation deferred
- Interactive project creation with inquirer-style prompts (name, description, type, preset)

### Claude's Discretion
- Dashboard layout and component structure
- CLI command names and flag conventions
- Color schemes and theming details

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `apps/server/src/codebot/api/` — Full REST API with auth, project, pipeline, agent endpoints
- `apps/server/src/codebot/websocket/` — Socket.IO server with NATS bridge
- `apps/dashboard/` — Vite + React scaffold (from Phase 1)
- `apps/cli/` — TypeScript CLI scaffold (from Phase 1)

### Established Patterns
- Tailwind CSS for styling, Shadcn/ui components
- TypeScript strict mode with ESM
- pnpm workspace for Node packages

### Integration Points
- Dashboard connects to API at `/api/v1/*` and WebSocket at `/ws`
- CLI connects to same API endpoints
- Dashboard pipeline view reads from pipeline and agent API endpoints

</code_context>

<specifics>
## Specific Ideas

No specific requirements — follow existing dashboard scaffold and API spec.

</specifics>

<deferred>
## Deferred Ideas

- Monaco editor write mode — deferred to post-v1.0
- Dashboard theming/dark mode — deferred to post-v1.0
- Full Creator agent implementations — deferred to post-v1.0

</deferred>
