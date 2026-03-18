# CodeBot — Project Structure

**Version:** 2.5
**Date:** 2026-03-18

---

## Repository Layout

```
codebot/
├── README.md
├── LICENSE
├── pyproject.toml                    # Python project config (uv/pip)
├── package.json                      # Node.js workspace root
├── turbo.json                        # Turborepo config
├── docker-compose.yml                # Local development stack
├── Makefile                          # Common commands
├── .env.example                      # Environment variable template
├── .github/
│   └── workflows/
│       ├── ci.yml                    # CI pipeline
│       └── release.yml               # Release pipeline
│
├── apps/
│   ├── server/                       # FastAPI backend server
│   │   ├── pyproject.toml
│   │   ├── src/
│   │   │   └── codebot/
│   │   │       ├── __init__.py
│   │   │       ├── main.py           # FastAPI app entrypoint
│   │   │       ├── config.py         # Settings & environment config
│   │   │       │
│   │   │       ├── api/              # REST API layer
│   │   │       │   ├── __init__.py
│   │   │       │   ├── routes/
│   │   │       │   │   ├── projects.py
│   │   │       │   │   ├── pipeline.py
│   │   │       │   │   ├── agents.py
│   │   │       │   │   ├── code.py
│   │   │       │   │   ├── tests.py
│   │   │       │   │   ├── security.py
│   │   │       │   │   ├── reviews.py
│   │   │       │   │   ├── config.py
│   │   │       │   │   ├── metrics.py
│   │   │       │   │   ├── brainstorm.py         # Brainstorming sessions
│   │   │       │   │   ├── templates.py          # Template management
│   │   │       │   │   ├── techstack.py          # Tech stack recommendations
│   │   │       │   │   ├── deployment.py         # Deployment management
│   │   │       │   │   ├── collaboration.py      # Real-time collaboration
│   │   │       │   │   ├── github_integration.py # GitHub operations
│   │   │       │   │   ├── skills.py             # Skill management
│   │   │       │   │   ├── hooks.py              # Hook management
│   │   │       │   │   ├── auth.py              # Authentication endpoints
│   │   │       │   │   ├── audit.py             # Audit log endpoints
│   │   │       │   │   ├── reports.py           # Project manager reports
│   │   │       │   │   ├── health.py            # Health check endpoints
│   │   │       │   │   ├── retention.py         # Data retention admin
│   │   │       │   │   └── dlq.py               # Dead letter queue admin
│   │   │       │   ├── schemas/      # Pydantic request/response models
│   │   │       │   │   ├── project.py
│   │   │       │   │   ├── pipeline.py
│   │   │       │   │   ├── agent.py
│   │   │       │   │   └── ...
│   │   │       │   ├── deps.py       # Dependency injection
│   │   │       │   └── middleware.py  # Auth, CORS, logging middleware
│   │   │       │
│   │   │       ├── core/             # Core business logic
│   │   │       │   ├── __init__.py
│   │   │       │   ├── orchestrator.py    # Master orchestrator
│   │   │       │   ├── pipeline.py        # Pipeline execution engine
│   │   │       │   ├── phase_executor.py  # Phase-level execution
│   │   │       │   └── task_scheduler.py  # Task scheduling & dependencies
│   │   │       │
│   │   │       ├── agents/           # Agent implementations
│   │   │       │   ├── __init__.py
│   │   │       │   ├── base.py            # BaseAgent abstract class
│   │   │       │   ├── orchestrator.py    # Orchestrator agent
│   │   │       │   ├── planner.py         # Planner agent
│   │   │       │   ├── researcher.py      # Researcher agent
│   │   │       │   ├── architect.py       # Architect agent
│   │   │       │   ├── designer.py        # Designer agent
│   │   │       │   ├── frontend_dev.py    # Frontend Developer agent
│   │   │       │   ├── backend_dev.py     # Backend Developer agent
│   │   │       │   ├── middleware_dev.py   # Middleware Developer agent
│   │   │       │   ├── infra_engineer.py  # Infrastructure Engineer agent
│   │   │       │   ├── security_auditor.py # Security Auditor agent
│   │   │       │   ├── code_reviewer.py   # Code Reviewer agent
│   │   │       │   ├── tester.py          # Tester agent
│   │   │       │   ├── debugger.py        # Debugger agent
│   │   │       │   ├── doc_writer.py      # Documentation Writer agent
│   │   │       │   ├── brainstorming_agent.py    # Initial ideation and requirement refinement
│   │   │       │   ├── techstack_builder_agent.py # Technology selection and configuration
│   │   │       │   ├── template_agent.py          # Template management and scaffolding
│   │   │       │   ├── mobile_developer_agent.py  # iOS/Android/React Native/Flutter
│   │   │       │   ├── database_agent.py          # Database design, optimization, migrations
│   │   │       │   ├── api_gateway_agent.py       # API design, gateway config, versioning
│   │   │       │   ├── devops_agent.py            # CI/CD pipelines, monitoring, alerting
│   │   │       │   ├── performance_agent.py       # Profiling, optimization, benchmarking
│   │   │       │   ├── accessibility_agent.py     # WCAG compliance, a11y testing
│   │   │       │   ├── i18n_agent.py              # Internationalization and localization
│   │   │       │   ├── github_agent.py            # GitHub operations, repos, PRs, Actions
│   │   │       │   ├── skill_creator_agent.py     # Creates reusable skills for agents
│   │   │       │   ├── hooks_creator_agent.py     # Creates lifecycle hooks
│   │   │       │   ├── tools_creator_agent.py     # Creates custom tools and MCP integrations
│   │   │       │   ├── integrations_agent.py      # Third-party service integrations
│   │   │       │   └── project_manager_agent.py  # Progress tracking, status reports, timeline management
│   │   │       │
│   │   │       ├── auth/             # Authentication & authorization
│   │   │       │   ├── __init__.py
│   │   │       │   ├── service.py         # Auth logic, JWT, API keys
│   │   │       │   ├── models.py          # User, ApiKey, AuditLog models
│   │   │       │   ├── middleware.py       # Auth middleware, RBAC
│   │   │       │   └── mfa.py             # TOTP multi-factor auth
│   │   │       │
│   │   │       ├── observability/    # Platform observability
│   │   │       │   ├── __init__.py
│   │   │       │   ├── metrics.py         # Prometheus metrics
│   │   │       │   ├── tracing.py         # OpenTelemetry integration
│   │   │       │   └── health.py          # Health check endpoints
│   │   │       │
│   │   │       ├── project_manager/  # Project management & reporting
│   │   │       │   ├── __init__.py
│   │   │       │   ├── service.py         # Progress tracking, timeline management
│   │   │       │   ├── models.py          # Report data models
│   │   │       │   └── router.py          # Project manager API routes
│   │   │       │
│   │   │       ├── retention/        # Data retention & cleanup
│   │   │       │   ├── __init__.py
│   │   │       │   ├── service.py         # Retention policy enforcement
│   │   │       │   ├── scheduler.py       # Cleanup job scheduling
│   │   │       │   └── models.py          # RetentionPolicy data models
│   │   │       │
│   │   │       ├── dlq/              # Dead letter queue
│   │   │       │   ├── __init__.py
│   │   │       │   ├── service.py         # DLQ management and replay
│   │   │       │   └── models.py          # DLQ item models
│   │   │       │
│   │   │       ├── graph/            # Graph engine (MASFactory-inspired)
│   │   │       │   ├── __init__.py
│   │   │       │   ├── engine.py          # Graph execution engine
│   │   │       │   ├── node.py            # Node primitives
│   │   │       │   ├── edge.py            # Edge primitives (State/Message/Control)
│   │   │       │   ├── graph.py           # Graph data structure
│   │   │       │   ├── loop.py            # Loop component
│   │   │       │   ├── switch.py          # Switch/branching component
│   │   │       │   ├── templates.py       # NodeTemplate & ComposedGraph
│   │   │       │   └── scheduler.py       # Topological sort & parallel scheduling
│   │   │       │
│   │   │       ├── llm/              # Multi-LLM abstraction
│   │   │       │   ├── __init__.py
│   │   │       │   ├── provider.py        # LLMProvider interface
│   │   │       │   ├── openai.py          # OpenAI provider
│   │   │       │   ├── anthropic.py       # Anthropic provider
│   │   │       │   ├── google.py          # Google Gemini provider
│   │   │       │   ├── router.py          # Model routing logic
│   │   │       │   ├── fallback.py        # Fallback chain manager
│   │   │       │   ├── budget.py          # Token budget management
│   │   │       │   └── cost.py            # Cost tracking
│   │   │       │
│   │   │       ├── cli_agents/       # CLI agent integration
│   │   │       │   ├── __init__.py
│   │   │       │   ├── runner.py          # CLIAgentRunner unified interface
│   │   │       │   ├── claude_code.py     # Claude Code integration
│   │   │       │   ├── codex.py           # OpenAI Codex CLI integration
│   │   │       │   ├── gemini_cli.py      # Gemini CLI integration
│   │   │       │   ├── output_parser.py   # Structured output parsing
│   │   │       │   └── session.py         # Session management
│   │   │       │
│   │   │       ├── context/          # Context management system
│   │   │       │   ├── __init__.py
│   │   │       │   ├── adapter.py         # Context Adapter (MASFactory pattern)
│   │   │       │   ├── tiers.py           # L0/L1/L2 tier management
│   │   │       │   ├── memory.py          # Persistent memory manager
│   │   │       │   ├── vector_store.py    # Vector store integration
│   │   │       │   ├── code_indexer.py    # Tree-sitter code indexing
│   │   │       │   ├── compressor.py      # Context compression/summarization
│   │   │       │   └── mcp.py             # MCP protocol integration
│   │   │       │
│   │   │       ├── security/         # Security pipeline
│   │   │       │   ├── __init__.py
│   │   │       │   ├── orchestrator.py    # Security scan orchestrator
│   │   │       │   ├── sast.py            # Semgrep + SonarQube
│   │   │       │   ├── dast.py            # OWASP ZAP integration
│   │   │       │   ├── dependency.py      # Trivy + OpenSCA
│   │   │       │   ├── secrets.py         # Gitleaks
│   │   │       │   ├── license.py         # ScanCode/FOSSology/ORT
│   │   │       │   ├── report.py          # Security report generation
│   │   │       │   └── gate.py            # Security quality gate
│   │   │       │
│   │   │       ├── testing/          # Testing pipeline
│   │   │       │   ├── __init__.py
│   │   │       │   ├── generator.py       # Test case generator
│   │   │       │   ├── runner.py          # Unified test runner
│   │   │       │   ├── coverage.py        # Coverage analysis
│   │   │       │   ├── parser.py          # Test result parser
│   │   │       │   └── regression.py      # Regression detector
│   │   │       │
│   │   │       ├── git/              # Git operations
│   │   │       │   ├── __init__.py
│   │   │       │   ├── repository.py      # Repository management
│   │   │       │   ├── worktree.py        # Worktree pool management
│   │   │       │   ├── branch.py          # Branch strategy
│   │   │       │   ├── commit.py          # Commit management
│   │   │       │   └── pr.py              # PR creation
│   │   │       │
│   │   │       ├── events/           # Event system
│   │   │       │   ├── __init__.py
│   │   │       │   ├── bus.py             # Event bus (pub/sub)
│   │   │       │   ├── types.py           # Event type definitions
│   │   │       │   ├── store.py           # Event persistence
│   │   │       │   └── handlers.py        # Built-in event handlers
│   │   │       │
│   │   │       ├── db/               # Database layer
│   │   │       │   ├── __init__.py
│   │   │       │   ├── models.py          # SQLAlchemy models
│   │   │       │   ├── session.py         # Database session management
│   │   │       │   └── migrations/        # Alembic migrations
│   │   │       │
│   │   │       ├── websocket/        # Real-time communication
│   │   │       │   ├── __init__.py
│   │   │       │   ├── manager.py         # WebSocket connection manager
│   │   │       │   └── events.py          # WebSocket event broadcasting
│   │   │       │
│   │   │       ├── brainstorm/       # Brainstorming session management
│   │   │       │   ├── __init__.py
│   │   │       │   ├── service.py         # Brainstorm session logic
│   │   │       │   ├── models.py          # Brainstorm data models
│   │   │       │   └── router.py          # Brainstorm API routes
│   │   │       │
│   │   │       ├── templates/        # Template management system
│   │   │       │   ├── __init__.py
│   │   │       │   ├── service.py         # Template CRUD and rendering
│   │   │       │   ├── models.py          # Template data models
│   │   │       │   ├── registry.py        # Template discovery and registration
│   │   │       │   └── router.py          # Template API routes
│   │   │       │
│   │   │       ├── techstack/        # Tech stack recommendation engine
│   │   │       │   ├── __init__.py
│   │   │       │   ├── service.py         # Tech stack evaluation logic
│   │   │       │   ├── models.py          # Tech stack data models
│   │   │       │   ├── recommender.py     # Recommendation engine
│   │   │       │   └── router.py          # Tech stack API routes
│   │   │       │
│   │   │       ├── deployment/       # Cloud deployment automation
│   │   │       │   ├── __init__.py
│   │   │       │   ├── service.py         # Deployment orchestration
│   │   │       │   ├── models.py          # Deployment data models
│   │   │       │   ├── providers/         # Cloud provider adapters
│   │   │       │   │   ├── __init__.py
│   │   │       │   │   ├── aws.py         # AWS deployment adapter
│   │   │       │   │   ├── gcp.py         # Google Cloud adapter
│   │   │       │   │   ├── azure.py       # Azure deployment adapter
│   │   │       │   │   ├── vercel.py      # Vercel deployment adapter
│   │   │       │   │   ├── railway.py     # Railway deployment adapter
│   │   │       │   │   └── netlify.py     # Netlify deployment adapter
│   │   │       │   └── router.py          # Deployment API routes
│   │   │       │
│   │   │       ├── mobile/           # Mobile development support
│   │   │       │   ├── __init__.py
│   │   │       │   ├── ios_builder.py          # iOS build pipeline
│   │   │       │   ├── android_builder.py      # Android build pipeline
│   │   │       │   ├── react_native_builder.py # React Native build pipeline
│   │   │       │   └── flutter_builder.py      # Flutter build pipeline
│   │   │       │
│   │   │       ├── collaboration/    # Real-time collaboration
│   │   │       │   ├── __init__.py
│   │   │       │   ├── service.py         # Collaboration session management
│   │   │       │   ├── conflict_resolver.py # Conflict resolution logic
│   │   │       │   ├── presence.py        # User presence tracking
│   │   │       │   └── crdt.py            # CRDT-based state synchronization
│   │   │       │
│   │   │       ├── skills/           # Agent skill management
│   │   │       │   ├── __init__.py
│   │   │       │   ├── service.py         # Skill lifecycle management
│   │   │       │   ├── registry.py        # Skill discovery and registration
│   │   │       │   └── executor.py        # Skill execution engine
│   │   │       │
│   │   │       ├── hooks/            # Lifecycle hook management
│   │   │       │   ├── __init__.py
│   │   │       │   ├── service.py         # Hook lifecycle management
│   │   │       │   ├── registry.py        # Hook registration and lookup
│   │   │       │   └── executor.py        # Hook execution engine
│   │   │       │
│   │   │       ├── tools/            # Custom tool management
│   │   │       │   ├── __init__.py
│   │   │       │   ├── service.py         # Tool lifecycle management
│   │   │       │   ├── registry.py        # Tool discovery and registration
│   │   │       │   └── mcp_server.py      # MCP server for custom tools
│   │   │       │
│   │   │       └── integrations/     # Third-party integrations
│   │   │           ├── __init__.py
│   │   │           ├── service.py         # Integration management
│   │   │           ├── registry.py        # Integration registry
│   │   │           └── adapters/          # Service-specific adapters
│   │   │               ├── __init__.py
│   │   │               ├── stripe.py      # Stripe payments adapter
│   │   │               ├── auth0.py       # Auth0 authentication adapter
│   │   │               ├── sendgrid.py    # SendGrid email adapter
│   │   │               ├── s3.py          # AWS S3 storage adapter
│   │   │               └── firebase.py    # Firebase adapter
│   │   │
│   │   └── tests/                    # Server tests
│   │       ├── conftest.py
│   │       ├── unit/
│   │       ├── integration/
│   │       └── e2e/
│   │
│   ├── dashboard/                    # React web dashboard
│   │   ├── package.json
│   │   ├── vite.config.ts
│   │   ├── tailwind.config.ts
│   │   ├── tsconfig.json
│   │   ├── index.html
│   │   ├── src/
│   │   │   ├── main.tsx
│   │   │   ├── App.tsx
│   │   │   ├── components/
│   │   │   │   ├── layout/
│   │   │   │   │   ├── Sidebar.tsx
│   │   │   │   │   ├── Header.tsx
│   │   │   │   │   └── MainLayout.tsx
│   │   │   │   ├── project/
│   │   │   │   │   ├── ProjectBoard.tsx      # Kanban task board
│   │   │   │   │   ├── ProjectCreate.tsx     # PRD input form
│   │   │   │   │   └── ProjectList.tsx
│   │   │   │   ├── pipeline/
│   │   │   │   │   ├── PipelineView.tsx      # Pipeline phase visualization
│   │   │   │   │   ├── PhaseCard.tsx
│   │   │   │   │   └── PhaseGate.tsx         # Human approval gate
│   │   │   │   ├── agents/
│   │   │   │   │   ├── AgentTimeline.tsx     # Real-time agent graph
│   │   │   │   │   ├── AgentCard.tsx
│   │   │   │   │   ├── AgentLogs.tsx
│   │   │   │   │   └── AgentGraph.tsx        # D3/React Flow graph visualization
│   │   │   │   ├── code/
│   │   │   │   │   ├── CodeViewer.tsx        # Syntax-highlighted viewer
│   │   │   │   │   ├── DiffViewer.tsx
│   │   │   │   │   └── FileTree.tsx
│   │   │   │   ├── review/
│   │   │   │   │   ├── ReviewPanel.tsx
│   │   │   │   │   ├── SecurityFindings.tsx
│   │   │   │   │   └── QualityReport.tsx
│   │   │   │   ├── testing/
│   │   │   │   │   ├── TestResults.tsx
│   │   │   │   │   └── CoverageReport.tsx
│   │   │   │   ├── chat/
│   │   │   │   │   ├── ChatPanel.tsx         # Chat with Orchestrator
│   │   │   │   │   └── MessageBubble.tsx
│   │   │   │   ├── terminal/
│   │   │   │   │   └── EmbeddedTerminal.tsx  # xterm.js terminal
│   │   │   │   ├── metrics/
│   │   │   │   │   ├── TokenUsage.tsx
│   │   │   │   │   ├── CostDashboard.tsx
│   │   │   │   │   └── PerformanceChart.tsx
│   │   │   │   ├── brainstorm/               # Brainstorming session UI
│   │   │   │   │   ├── BrainstormPanel.tsx   # Main brainstorming interface
│   │   │   │   │   ├── IdeaBoard.tsx         # Visual idea organization
│   │   │   │   │   └── RequirementRefiner.tsx # Requirement refinement wizard
│   │   │   │   ├── templates/                # Template selection UI
│   │   │   │   │   ├── TemplateGallery.tsx   # Template browsing and selection
│   │   │   │   │   ├── TemplatePreview.tsx   # Template preview with live demo
│   │   │   │   │   └── TechStackSelector.tsx # Tech stack picker
│   │   │   │   ├── deployment/               # Deployment management UI
│   │   │   │   │   ├── DeploymentPanel.tsx   # Deployment overview
│   │   │   │   │   ├── CloudProviderSelector.tsx # Cloud provider picker
│   │   │   │   │   ├── DeploymentStatus.tsx  # Live deployment status
│   │   │   │   │   └── DeploymentLogs.tsx    # Deployment log viewer
│   │   │   │   ├── collaboration/            # Real-time collaboration UI
│   │   │   │   │   ├── CollaborationPanel.tsx # Collaboration session panel
│   │   │   │   │   ├── PresenceIndicator.tsx  # Active user presence
│   │   │   │   │   ├── ConflictResolver.tsx   # Merge conflict UI
│   │   │   │   │   └── LiveCursor.tsx         # Real-time cursor tracking
│   │   │   │   ├── mobile/                   # Mobile preview UI
│   │   │   │   │   ├── MobilePreview.tsx     # Mobile app preview
│   │   │   │   │   └── DeviceSimulator.tsx   # Device frame simulator
│   │   │   │   ├── github/                   # GitHub integration UI
│   │   │   │   │   ├── GitHubPanel.tsx       # GitHub operations panel
│   │   │   │   │   ├── PRViewer.tsx          # Pull request viewer
│   │   │   │   │   └── ActionsStatus.tsx     # GitHub Actions status
│   │   │   │   ├── accessibility/            # Accessibility reports UI
│   │   │   │   │   ├── A11yReport.tsx        # Accessibility audit report
│   │   │   │   │   └── WCAGChecklist.tsx     # WCAG compliance checklist
│   │   │   │   └── performance/              # Performance reports UI
│   │   │   │       ├── PerformanceReport.tsx  # Performance audit report
│   │   │   │       └── LoadTestResults.tsx    # Load test result viewer
│   │   │   ├── hooks/
│   │   │   │   ├── useWebSocket.ts
│   │   │   │   ├── useProject.ts
│   │   │   │   ├── usePipeline.ts
│   │   │   │   └── useAgents.ts
│   │   │   ├── stores/               # Zustand state stores
│   │   │   │   ├── projectStore.ts
│   │   │   │   ├── pipelineStore.ts
│   │   │   │   ├── agentStore.ts
│   │   │   │   └── settingsStore.ts
│   │   │   ├── services/             # API client
│   │   │   │   ├── api.ts
│   │   │   │   └── websocket.ts
│   │   │   ├── types/
│   │   │   │   └── index.ts
│   │   │   └── styles/
│   │   │       └── globals.css
│   │   └── tests/
│   │
│   └── cli/                          # CLI application
│       ├── package.json
│       ├── tsconfig.json
│       ├── src/
│       │   ├── index.ts              # CLI entrypoint
│       │   ├── commands/
│       │   │   ├── init.ts
│       │   │   ├── start.ts
│       │   │   ├── status.ts
│       │   │   ├── review.ts
│       │   │   ├── deploy.ts
│       │   │   └── config.ts
│       │   ├── utils/
│       │   │   ├── api.ts            # API client for CLI
│       │   │   ├── display.ts        # Terminal output formatting
│       │   │   └── config.ts         # CLI config management
│       │   └── types/
│       │       └── index.ts
│       └── tests/
│
├── libs/                             # Shared libraries
│   ├── agent-sdk/                    # Agent SDK (Python)
│   │   ├── pyproject.toml
│   │   └── src/
│   │       └── codebot_agent_sdk/
│   │           ├── __init__.py
│   │           ├── agent.py          # Agent base classes
│   │           ├── tools.py          # Tool definitions
│   │           ├── context.py        # Context utilities
│   │           └── types.py          # Shared type definitions
│   │
│   ├── shared-types/                 # Shared TypeScript types
│   │   ├── package.json
│   │   └── src/
│   │       └── index.ts
│   │
│   └── graph-engine/                 # Graph engine (Python)
│       ├── pyproject.toml
│       └── src/
│           └── codebot_graph/
│               ├── __init__.py
│               ├── graph.py
│               ├── node.py
│               ├── edge.py
│               └── executor.py
│
├── sdks/                             # Client SDKs
│   ├── python/                       # Python SDK for CodeBot API
│   │   ├── pyproject.toml
│   │   ├── src/
│   │   │   └── codebot_sdk/
│   │   │       ├── __init__.py
│   │   │       ├── client.py
│   │   │       └── types.py
│   │   └── tests/
│   │
│   └── typescript/                   # TypeScript SDK for CodeBot API
│       ├── package.json
│       ├── tsconfig.json
│       ├── src/
│       │   ├── index.ts
│       │   ├── client.ts
│       │   └── types.ts
│       └── tests/
│
├── configs/                          # Configuration templates
│   ├── default.yaml                  # Default agent & pipeline config
│   ├── providers/
│   │   ├── openai.yaml
│   │   ├── anthropic.yaml
│   │   └── google.yaml
│   ├── security/
│   │   ├── semgrep-rules.yaml
│   │   ├── trivy.yaml
│   │   └── gitleaks.toml
│   ├── pipelines/
│   │   ├── full.yaml                 # Full SDLC pipeline
│   │   ├── quick.yaml                # Quick prototype pipeline
│   │   └── review-only.yaml          # Review-only pipeline
│   ├── templates/                    # Template definitions
│   │   ├── react-material.yaml
│   │   ├── react-shadcn.yaml
│   │   ├── react-antd.yaml
│   │   ├── vue-vuetify.yaml
│   │   ├── nextjs-tailwind.yaml
│   │   ├── flutter-material.yaml
│   │   └── react-native-paper.yaml
│   ├── techstacks/                   # Tech stack definitions
│   │   ├── fullstack-react-node.yaml
│   │   ├── fullstack-nextjs.yaml
│   │   ├── fullstack-django-react.yaml
│   │   ├── mobile-react-native.yaml
│   │   ├── mobile-flutter.yaml
│   │   ├── serverless-aws.yaml
│   │   └── microservices-k8s.yaml
│   ├── deployment/                   # Deployment provider configs
│   │   ├── aws.yaml
│   │   ├── gcp.yaml
│   │   ├── azure.yaml
│   │   ├── vercel.yaml
│   │   └── railway.yaml
│   ├── skills/                       # Built-in skill definitions
│   ├── hooks/                        # Built-in hook definitions
│   └── integrations/                 # Integration adapter configs
│
├── templates/                        # Code generation templates
│   ├── prompts/                      # Agent system prompts
│   │   ├── orchestrator.md
│   │   ├── planner.md
│   │   ├── researcher.md
│   │   ├── architect.md
│   │   ├── designer.md
│   │   ├── frontend_dev.md
│   │   ├── backend_dev.md
│   │   ├── middleware_dev.md
│   │   ├── infra_engineer.md
│   │   ├── security_auditor.md
│   │   ├── code_reviewer.md
│   │   ├── tester.md
│   │   ├── debugger.md
│   │   ├── doc_writer.md
│   │   └── project_manager.md
│   ├── project/                      # Project scaffolding templates
│   │   ├── react-vite/
│   │   ├── nextjs/
│   │   ├── fastapi/
│   │   ├── express/
│   │   └── fullstack/
│   ├── pipelines/                    # Pipeline graph definitions
│   │   ├── standard_sdlc.py
│   │   └── rapid_prototype.py
│   ├── ui/                           # UI component templates
│   ├── scaffolds/                    # Project scaffolding templates
│   └── mobile/                       # Mobile app templates
│
├── docker/                           # Docker configurations
│   ├── Dockerfile.server
│   ├── Dockerfile.dashboard
│   ├── Dockerfile.sandbox            # Sandbox for code execution
│   └── docker-compose.dev.yml
│
├── scripts/                          # Development & deployment scripts
│   ├── setup.sh                      # Initial setup script
│   ├── dev.sh                        # Start development environment
│   └── seed.sh                       # Seed database with examples
│
├── docs/                             # Documentation
│   ├── prd/
│   │   └── PRD.md
│   ├── architecture/
│   │   └── ARCHITECTURE.md
│   ├── technical/
│   │   └── TECHNICAL_REQUIREMENTS.md
│   ├── design/
│   │   ├── SYSTEM_DESIGN.md
│   │   └── PROJECT_STRUCTURE.md
│   ├── api/
│   │   └── API_SPECIFICATION.md
│   ├── workflows/
│   │   └── AGENT_WORKFLOWS.md
│   └── references/
│       └── ref.md
│
└── workspace/                        # Runtime workspace (gitignored)
    ├── projects/                     # Generated project directories
    ├── worktrees/                    # Git worktree pool
    ├── checkpoints/                  # Pipeline checkpoints
    ├── artifacts/                    # Build artifacts
    └── logs/                         # Agent execution logs
```

**Total: ~350+ files and directories**

---

## Module Responsibilities

### `apps/server/` — Backend API Server (Python/FastAPI)

The central orchestration server that manages all agent operations, project state, and provides APIs for the dashboard and CLI.

| Module | Responsibility |
|---|---|
| `api/` | REST endpoint definitions, request validation, response serialization |
| `core/` | Pipeline execution, task scheduling, orchestration logic |
| `agents/` | Individual agent implementations with role-specific logic |
| `graph/` | Graph execution engine inspired by MASFactory |
| `llm/` | Multi-LLM provider abstraction, model routing, cost tracking |
| `cli_agents/` | Integration with Claude Code, Codex, Gemini CLI |
| `context/` | Three-tier context management, RAG, memory |
| `security/` | Security scanning tool orchestration |
| `testing/` | Test generation and execution framework |
| `git/` | Git operations, worktree management, PR creation |
| `events/` | Event bus for real-time inter-agent communication |
| `db/` | Database models and migrations |
| `websocket/` | Real-time updates to dashboard |
| `brainstorm/` | Brainstorming session management and ideation workflows |
| `templates/` | Template discovery, registration, rendering, and scaffolding |
| `techstack/` | Tech stack evaluation, recommendation engine, configuration |
| `deployment/` | Cloud deployment automation with multi-provider support |
| `mobile/` | Mobile build pipelines for iOS, Android, React Native, Flutter |
| `collaboration/` | Real-time collaboration, CRDT sync, presence, conflict resolution |
| `skills/` | Agent skill lifecycle management, registry, and execution |
| `hooks/` | Lifecycle hook registration, lookup, and execution |
| `tools/` | Custom tool management and MCP server integration |
| `integrations/` | Third-party service adapters (Stripe, Auth0, SendGrid, S3, Firebase) |
| `auth/` | JWT authentication, API key management, RBAC enforcement, MFA |
| `observability/` | Prometheus metrics, OpenTelemetry tracing, health checks |
| `project_manager/` | Progress tracking, status reports, timeline management, blocker identification |
| `retention/` | Data retention policy enforcement, automated cleanup |
| `dlq/` | Dead letter queue management, message replay |

### `apps/dashboard/` — Web Dashboard (React/TypeScript)

Real-time web interface for monitoring and controlling the agent pipeline.

| Module | Responsibility |
|---|---|
| `components/project/` | Project creation, listing, Kanban board |
| `components/pipeline/` | Pipeline visualization, phase gates |
| `components/agents/` | Agent timeline, graph visualization, logs |
| `components/code/` | Code viewer, diff viewer, file tree |
| `components/review/` | Security findings, quality reports |
| `components/testing/` | Test results, coverage reports |
| `components/chat/` | Chat interface with Orchestrator |
| `components/terminal/` | Embedded terminal for manual intervention |
| `components/metrics/` | Token usage, cost tracking, performance |
| `components/brainstorm/` | Brainstorming sessions, idea boards, requirement refinement |
| `components/templates/` | Template gallery, preview, tech stack selection |
| `components/deployment/` | Deployment management, cloud provider selection, logs |
| `components/collaboration/` | Real-time collaboration, presence indicators, conflict resolution |
| `components/mobile/` | Mobile app preview, device simulation |
| `components/github/` | GitHub operations panel, PR viewer, Actions status |
| `components/accessibility/` | Accessibility audit reports, WCAG compliance checklists |
| `components/performance/` | Performance audit reports, load test results |

### `apps/cli/` — Command Line Interface (TypeScript)

Developer-facing CLI for headless operation and CI/CD integration.

### `libs/` — Shared Libraries

Reusable packages shared between server components.

### `sdks/` — Client SDKs

Client libraries for integrating with the CodeBot API from external applications.

| SDK | Responsibility |
|---|---|
| `python/` | Python client SDK for programmatic API access |
| `typescript/` | TypeScript/JavaScript client SDK for web and Node.js integration |

### `configs/` — Configuration

YAML-based configuration for agents, LLM providers, security tools, pipeline definitions, templates, tech stacks, deployment providers, skills, hooks, and integrations.

### `templates/` — Templates

Agent system prompts, project scaffolding templates, UI component templates, and mobile app templates for different tech stacks.

---

## Key Dependencies

### Python Dependencies (Backend — `apps/server/`)

| Package | Purpose |
|---|---|
| `fastapi`, `uvicorn`, `pydantic` | Web framework, ASGI server, data validation |
| `langgraph` | Agent orchestration / graph engine |
| `temporalio` | Durable workflow execution |
| `litellm` | Unified LLM gateway (OpenAI, Anthropic, Google, self-hosted) |
| `fastmcp` | MCP framework (Model Context Protocol 2.0) |
| `nats-py` | Event bus (pub/sub messaging) |
| `taskiq`, `taskiq-nats` | Distributed task queue over NATS |
| `lancedb` | Vector database (development / local) |
| `qdrant-client` | Vector database (production / scaled) |
| `llama-index` | RAG framework for context retrieval |
| `tree-sitter` | Multi-language code parsing (AST) |
| `langfuse` | LLM observability and cost tracking |
| `pluggy` | Plugin system for extensibility |
| `copier` | Project scaffolding / template rendering |
| `alembic`, `sqlalchemy` | Database migrations and ORM |
| `apprise` | Multi-channel notifications |
| `gitpython` | Git operations and worktree management |
| `semgrep`, `bandit` | Security static analysis (SAST) |
| `promptfoo` | Prompt testing and evaluation |

### Node.js Dependencies (Frontend — `apps/dashboard/`)

| Package | Purpose |
|---|---|
| `react`, `next` (or `vite`) | UI framework and build tooling |
| `@refinedev/core` | Admin / CRUD framework |
| `@xyflow/react` | Pipeline graph visualization |
| `@shadcn/ui` | UI component library |
| `@tremor/react` | Charts and data visualization |
| `monaco-editor` | In-browser code editor |
| `@xterm/xterm` | Embedded terminal emulator |
| `socket.io-client` | Real-time WebSocket communication |
| `yjs`, `y-monaco` | Real-time collaboration (CRDT) |
| `mermaid` | Diagram rendering |
