# Phase 11: React Dashboard + CLI Application -- Research

**Researched:** 2026-03-18
**Status:** Complete
**Phase Goal:** Users can monitor, control, and interact with CodeBot through a real-time web dashboard and a command-line interface

---

## 1. Scope and Requirements

Phase 11 covers three workstreams: **React Dashboard** (DASH-01 through DASH-08), **CLI Application** (CLI-01 through CLI-04), and **Creator Agents** (AGNT-09, AGNT-10, AGNT-11).

### 1.1 Dashboard Requirements (DASH-01 to DASH-08)

| ID | Requirement | Key Technology |
|----|------------|----------------|
| DASH-01 | Real-time pipeline visualization with node status | React Flow (@xyflow/react 12.10+) + Socket.IO |
| DASH-02 | Agent monitoring panel: status, logs, metrics, cost | TanStack Query + Zustand + Socket.IO |
| DASH-03 | Code editor integration for viewing/editing generated code | Monaco Editor |
| DASH-04 | Terminal emulator for CLI interaction within dashboard | xterm.js + @xterm/addon-fit |
| DASH-05 | CRDT-based real-time collaboration for human-AI co-editing | Yjs + y-monaco + y-websocket |
| DASH-06 | Socket.IO live updates for pipeline progress and agent events | Socket.IO 4.8+ client |
| DASH-07 | Cost dashboard: token usage and cost breakdown per agent/stage/model | Recharts or Tremor + TanStack Query |
| DASH-08 | Live preview panel showing running application mid-pipeline | iframe sandbox with hot-reload proxy |

### 1.2 CLI Requirements (CLI-01 to CLI-04)

| ID | Requirement | Key Technology |
|----|------------|----------------|
| CLI-01 | Project creation with interactive prompts | Click 8.x + Rich |
| CLI-02 | Pipeline execution commands (start, pause, resume, stop) | Click + httpx (async API client) |
| CLI-03 | Agent status and log streaming from terminal | httpx + SSE/WebSocket streaming |
| CLI-04 | Pipeline preset selection (full, quick, review-only) | Click options/arguments |

### 1.3 Creator Agent Requirements (AGNT-09 to AGNT-11)

| ID | Requirement | Agent | Key Patterns |
|----|------------|-------|-------------|
| AGNT-09 | Skill Creator agent generates reusable skills | Skill Creator (Agent #26) | Pattern extraction, skill registry, YAML+code packaging |
| AGNT-10 | Hooks Creator agent creates event-triggered hooks | Hooks Creator (Agent #27) | Hook generation, hook registry, pipeline integration |
| AGNT-11 | Tools Creator agent exposes new tool capabilities | Tools Creator (Agent #28) | Tool code generation, MCP server config, tool registry |

---

## 2. Technology Stack Decisions

All technologies are confirmed from `.planning/research/STACK.md` (license-audited):

### Dashboard Stack

| Technology | Version | License | Purpose |
|-----------|---------|---------|---------|
| React | 19+ | MIT | UI framework |
| Vite | 6+ | MIT | Build tool with HMR |
| TypeScript | 5.5+ | Apache-2.0 | Strict mode, ESM only |
| Tailwind CSS | 4.0+ | MIT | Styling (Oxide engine) |
| shadcn/ui | latest v4 | MIT | Component library (copy-paste model) |
| @xyflow/react | 12.10+ | MIT | Pipeline graph visualization |
| Zustand | 5.0+ | MIT | Client state management |
| TanStack Query | 5.90+ | MIT | Server state / data fetching |
| Monaco Editor | latest | MIT | In-browser code editor |
| xterm.js | latest | MIT | Terminal emulator |
| Socket.IO client | 4.8+ | MIT | Real-time WebSocket communication |
| Yjs | 13.6+ | MIT | CRDT collaborative editing |

### CLI Stack

| Technology | Version | License | Purpose |
|-----------|---------|---------|---------|
| Click | 8.x | BSD-3 | Python CLI framework |
| Rich | latest | MIT | Terminal formatting, progress bars |
| httpx | latest | BSD-3 | Async HTTP client for API communication |

---

## 3. Architecture Patterns

### 3.1 Dashboard Architecture

```
apps/dashboard/src/
  components/
    pipeline/           # React Flow graph components
      pipeline-view.tsx       # Main graph canvas
      agent-node.tsx          # Custom node for agents
      stage-group.tsx         # Grouping by pipeline stage
      edge-types.tsx          # Custom edges (data, control, conditional)
    monitoring/         # Agent monitoring panel
      agent-panel.tsx         # Agent status, logs, metrics
      cost-breakdown.tsx      # Cost per agent/stage/model
      log-viewer.tsx          # Real-time log streaming
    editor/             # Code editor
      code-editor.tsx         # Monaco wrapper
      file-tree.tsx           # File navigator
      collab-indicator.tsx    # Yjs collaboration awareness
    terminal/           # Terminal emulator
      terminal-panel.tsx      # xterm.js wrapper
      terminal-manager.ts     # Multi-session management
    preview/            # Live preview
      preview-frame.tsx       # Sandboxed iframe
  hooks/
    use-socket.ts            # Socket.IO connection hook
    use-pipeline-events.ts   # Pipeline event subscription
    use-agent-status.ts      # Agent real-time status
  stores/
    pipeline-store.ts        # Zustand: pipeline state
    agent-store.ts           # Zustand: agent status/logs
    editor-store.ts          # Zustand: active file/editor state
    ui-store.ts              # Zustand: layout, panels, theme
  api/
    client.ts                # TanStack Query client setup
    pipelines.ts             # Pipeline CRUD queries/mutations
    agents.ts                # Agent management queries
    projects.ts              # Project CRUD queries
  lib/
    socket.ts                # Socket.IO singleton
    yjs-provider.ts          # Yjs WebSocket provider
```

### 3.2 Socket.IO Event Architecture

Socket.IO namespaces separate concerns (from Phase 10's SRVR-02 WebSocket endpoint):

| Namespace | Events | Purpose |
|-----------|--------|---------|
| `/pipeline` | `stage:start`, `stage:complete`, `stage:error`, `gate:pending`, `gate:approved` | Pipeline progress |
| `/agents` | `agent:status`, `agent:log`, `agent:metrics`, `agent:output` | Agent monitoring |
| `/editor` | `file:change`, `cursor:move` (via Yjs) | Collaborative editing |
| `/terminal` | `terminal:data`, `terminal:resize` | Terminal I/O |

### 3.3 React Flow Graph Model

Pipeline visualization maps directly to the graph engine's topology:

- **Custom node types**: `AgentNode`, `SubgraphNode`, `GateNode`, `ParallelNode`, `MergeNode`
- **Node status colors**: IDLE (gray), EXECUTING (blue pulse), COMPLETED (green), FAILED (red), WAITING (amber)
- **Edge types**: `DataEdge` (solid), `ControlEdge` (dashed), `ConditionalEdge` (dotted with label)
- **Grouping**: Pipeline stages (S0-S9) as React Flow groups with collapsible sections
- **Layout**: Dagre or ELK layout algorithm for automatic positioning from DAG topology

### 3.4 CLI Architecture

```
apps/cli/
  codebot/
    __init__.py
    main.py              # Click entry point
    commands/
      project.py         # create, list, delete, import
      pipeline.py        # start, pause, resume, stop, status
      agent.py           # list, logs, restart
      config.py          # set, get, preset
    client/
      api.py             # httpx async API client (wraps Phase 10 REST endpoints)
      streaming.py       # SSE/WebSocket log streaming
    output/
      formatters.py      # Rich table/panel formatters
      spinners.py        # Progress indicators
```

### 3.5 Creator Agents Architecture

All three creator agents follow the existing BaseAgent pattern from Phase 3:

1. **Extend BaseAgent** with PRA cognitive cycle
2. **Register in AgentType enum** (Phase 3's agent registry)
3. **YAML configuration** for model, tools, context tiers, retry policy
4. **Tool bindings**: Each creator has specialized tools (pattern_extractor, hook_generator, tool_generator, etc.)
5. **Registry integration**: Each produces artifacts that register in the skill/hook/tool registry

---

## 4. Key Integration Points

### 4.1 Dashboard <-> Server (Phase 10)

- **REST API**: TanStack Query wraps all SRVR-01 endpoints for project CRUD, pipeline control, agent management
- **WebSocket**: Socket.IO client connects to SRVR-02 for real-time updates
- **Authentication**: Auth tokens from SRVR-03 stored in Zustand, attached to all API/WebSocket requests

### 4.2 CLI <-> Server (Phase 10)

- **REST API**: httpx async client wraps same SRVR-01 endpoints
- **Streaming**: SSE or WebSocket for agent log streaming (CLI-03)
- **Auth**: Token-based auth, stored in `~/.codebot/credentials`

### 4.3 Creator Agents <-> Agent Framework (Phase 3)

- Creator agents are standard BaseAgent subclasses
- Registered in the pipeline as cross-cutting agents (not bound to a single stage)
- Communicate via NATS event bus (Phase 1) and SharedState (Phase 2)
- Outputs (skills, hooks, tools) register in their respective registries

---

## 5. Validation Architecture

### 5.1 Dashboard Validation

| Criterion | Validation Method |
|-----------|-------------------|
| Pipeline graph renders with correct topology | Unit test: mock graph data -> React Flow renders N nodes, M edges |
| Real-time updates flow from Socket.IO to UI | Integration test: emit mock events -> verify Zustand store updates |
| Monaco editor loads file content | Unit test: mount editor with content -> verify rendered text |
| xterm.js terminal connects and displays output | Integration test: WebSocket mock -> terminal displays data |
| Cost breakdown aggregates correctly | Unit test: mock cost data -> verify table sums match |

### 5.2 CLI Validation

| Criterion | Validation Method |
|-----------|-------------------|
| `codebot create` prompts and creates project | CLI test: simulate inputs -> verify API call made |
| `codebot start` triggers pipeline execution | CLI test: mock API -> verify correct endpoint called |
| `codebot logs` streams agent output | CLI test: mock SSE stream -> verify terminal output |
| `codebot config preset full` selects preset | CLI test: verify config stored and sent to API |

### 5.3 Creator Agent Validation

| Criterion | Validation Method |
|-----------|-------------------|
| Skill Creator produces valid skill YAML | Unit test: sample code -> skill output validates against schema |
| Hooks Creator registers hooks in pipeline | Integration test: hook creation -> verify in hook registry |
| Tools Creator generates MCP config | Unit test: tool spec -> valid MCP JSON output |

---

## 6. Risks and Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| React Flow performance with large graphs (30+ agents, 100+ edges) | MEDIUM | Virtualize off-screen nodes, use React Flow's viewport culling, limit animation complexity |
| Monaco + Yjs integration complexity for collaborative editing | MEDIUM | Use existing y-monaco binding library; fall back to view-only mode if CRDT sync fails |
| Socket.IO reconnection handling during pipeline runs | HIGH | Implement reconnection with replay from last-seen event ID (NATS JetStream consumer position) |
| xterm.js session management across multiple agents | LOW | Tabbed terminal interface with session pooling; max concurrent terminals limit |
| CLI must handle both sync (CRUD) and async (streaming) in single framework | LOW | Click handles command dispatch; httpx async context for streaming commands |
| Creator agents depend on mature agent framework (Phase 3) and tool registry | LOW | By Phase 11, framework is battle-tested through Phases 7-9 |

---

## 7. Build Order Recommendation

**Wave 1 (parallel):**
- Plan 11-01: Dashboard foundation -- React app setup, Socket.IO connection, pipeline graph view (DASH-01, DASH-06)
- Plan 11-02: CLI application -- Click structure, API client, all commands (CLI-01 through CLI-04)

**Wave 2 (depends on Wave 1):**
- Plan 11-03: Dashboard advanced panels + Creator agents -- Monitoring, editor, terminal, cost dashboard, Yjs collaboration, live preview, and three creator agents (DASH-02 through DASH-08, AGNT-09 through AGNT-11)

---

## RESEARCH COMPLETE

Phase 11 is well-defined with clear technology choices (all MIT/Apache-2.0), established library patterns, and strong integration points from Phase 10's API layer. The main architectural decisions are:
1. React Flow for graph visualization with custom node types per graph engine NodeType
2. Socket.IO namespaces for event separation (pipeline, agents, editor, terminal)
3. Zustand + TanStack Query for client/server state split
4. Click + httpx for CLI with streaming support
5. Creator agents as standard BaseAgent subclasses with specialized tools and registries
