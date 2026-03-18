# CodeBot — Product Requirements Document (PRD)

**Version:** 2.5
**Date:** 2026-03-18
**Status:** Review
**Author:** Architecture Team
**Supersedes:** PRD v2.4 (2026-03-18)

---

## 1. Executive Summary

CodeBot is the most ambitious open-source, autonomous, end-to-end software development platform ever designed. Powered by a graph-centric multi-agent system of 30 specialized AI agents, CodeBot transforms natural language ideas into fully tested, reviewed, secured, and cloud-deployed applications across web, mobile, and backend platforms — with zero manual coding required.

The platform supports the complete software development lifecycle from initial brainstorming through production deployment, covering greenfield projects (built from scratch), inflight projects (joining mid-development), and brownfield projects (modernizing legacy codebases). CodeBot enables real-time collaboration between humans and AI agents, supports multi-repository architectures, deploys to all major cloud providers, and runs against cloud-hosted LLMs or fully self-hosted models for air-gapped and privacy-sensitive environments.

The system is inspired by the MASFactory framework (arXiv:2603.06007), which models multi-agent workflows as directed computation graphs where nodes execute agents/sub-workflows and edges encode dependencies and message passing. CodeBot extends this paradigm with a complete SDLC pipeline, multi-LLM support (including self-hosted), CLI-based coding agent integration (Claude Code, OpenAI Codex, Gemini CLI), native mobile development, cloud deployment automation, and an extensible agent ecosystem where agents can create new skills, hooks, and tools for other agents.

---

## 2. Problem Statement

### 2.1 Current Pain Points

1. **Manual orchestration overhead**: Developers must manually coordinate between brainstorming, planning, coding, testing, security scanning, deployment, and monitoring — each requiring different tools, platforms, and expertise.
2. **Context fragmentation**: Knowledge about requirements, architecture decisions, code context, test results, deployment configurations, and operational insights is scattered across tools, documents, repositories, and human memory.
3. **Sequential bottlenecks**: Traditional development is inherently sequential — you cannot test what has not been coded, and you cannot code what has not been designed. This creates waterfalls even in agile teams.
4. **Quality gaps**: Security reviews, accessibility audits, internationalization, performance profiling, and comprehensive testing are often skipped or performed superficially under time pressure.
5. **LLM lock-in**: Existing AI coding tools are typically locked to a single LLM provider, preventing teams from leveraging the best model for each task or running models locally for privacy compliance.
6. **Platform fragmentation**: Building for web, iOS, Android, and backend simultaneously requires completely different toolchains, languages, and deployment pipelines — multiplying complexity.
7. **No idea-to-deployment pipeline**: Current tools help with isolated phases (coding, testing, deploying) but none provide an autonomous pipeline from initial brainstorming through production deployment and monitoring.
8. **Legacy code burden**: Modernizing, refactoring, and extending existing codebases is one of the most time-consuming and error-prone activities in software engineering, with no AI-native solutions addressing it end-to-end.
9. **Multi-repo complexity**: Modern architectures spanning multiple repositories (monorepos, polyrepos, microservices) require manual coordination of cross-repo dependencies, versioning, and deployment ordering.
10. **Missing collaboration model**: No existing platform enables humans and AI agents to work simultaneously on the same codebase with real-time visibility, live updates, and conflict resolution.

### 2.2 Target Users

| User Persona | Description | Primary Need |
|---|---|---|
| **Solo Developer** | Individual building MVPs or side projects | End-to-end automation from idea to deployed app |
| **Tech Lead** | Engineering leader managing team output | Autonomous agent teams for parallel feature development |
| **Startup CTO** | Technical co-founder with limited engineering resources | Rapid prototyping and production-grade code generation |
| **Enterprise Architect** | Architect defining standards for large organizations | Customizable agent pipelines with governance and compliance |
| **QA Engineer** | Quality assurance professional | Automated test generation, execution, and regression detection |
| **Product Manager** | Non-technical stakeholder with product ideas | Brainstorming-to-product pipeline without writing code |
| **Mobile Developer** | iOS/Android developer | Cross-platform and native mobile app generation |
| **DevOps Engineer** | Infrastructure and deployment specialist | Automated CI/CD, infrastructure provisioning, and monitoring |
| **Legacy System Owner** | Maintainer of aging codebases | Brownfield modernization, refactoring, and migration |
| **Open Source Maintainer** | Maintainer of open source projects | Automated contributions, PR review, issue triage |
| **Consultant / Agency** | Building software for multiple clients | Rapid multi-project delivery with template reuse |

---

## 3. Product Vision

**Vision Statement**: CodeBot transforms a spark of an idea into a fully tested, reviewed, accessible, internationalized, and cloud-deployed multi-platform application through autonomous multi-agent orchestration — supporting every phase from brainstorming through production monitoring, across web, mobile, and backend, for new projects, existing codebases, and legacy modernization.

**One-liner**: "From Brainstorm to Production — Autonomously, Everywhere."

**Guiding Principles**:

1. **Everything is in scope.** If it is part of software development, CodeBot handles it.
2. **Human-in-the-loop, not human-in-the-way.** Humans collaborate in real-time, approve at gates, and override when needed — but never block the pipeline.
3. **Best model for the job.** Cloud LLMs, self-hosted models, and local inference — use whatever is optimal for each task.
4. **Platform agnostic.** Web, iOS, Android, backend, infrastructure — one pipeline to rule them all.
5. **Extensible by design.** Agents create skills, hooks, and tools that other agents consume — the system improves itself.
6. **Open source forever.** Community-driven development with transparent architecture and zero vendor lock-in.

---

## 4. Core Capabilities

### 4.1 Input Processing

| Feature | Description |
|---|---|
| PRD Ingestion | Accept structured PRDs (Markdown, JSON, YAML) or free-form natural language requirements |
| Multi-modal Input | Support text, images (wireframes, screenshots, mockups), diagrams, voice recordings (transcribed), video walkthroughs, and reference URLs |
| Requirement Parsing | NLP-powered extraction of functional requirements, non-functional requirements, constraints, acceptance criteria, and user stories |
| Clarification Loop | Human-in-the-loop questioning when requirements are ambiguous, incomplete, or conflicting |
| Template Selection | Users can select UI/UX templates (Material Design, Ant Design, Tailwind UI, Shadcn/ui, Chakra UI, Bootstrap, custom design systems) at project inception |
| Tech Stack Selection | Users can manually select or let AI recommend: programming language, framework, database, ORM, hosting provider, authentication method, payment gateway, and more |
| Project Type Detection | Automatically detect whether input describes a greenfield, inflight, or brownfield project and configure the pipeline accordingly |
| Existing Codebase Import | Import and analyze existing codebases from local directories, GitHub, GitLab, Bitbucket, or archive files for inflight and brownfield projects |
| Multi-repo Configuration | Configure multi-repository project structures with cross-repo dependency definitions |
| Deployment Opt-in | Users choose whether to include automated deployment (S10) or receive the generated codebase as a local repository with deployment docs. Deployment can also be triggered later on demand |
| Reference App Analysis | Analyze reference applications, competitor products, or inspiration screenshots to inform design and feature requirements |

### 4.2 Brainstorming Phase

| Feature | Description |
|---|---|
| Idea Exploration | Facilitate open-ended brainstorming sessions where the user describes their idea and the system explores possibilities, alternatives, and variations |
| Problem-Solution Mapping | Help users articulate the core problem they are solving and map it to potential solution approaches |
| Competitive Analysis | Research existing solutions, identify gaps, and suggest differentiators |
| Feature Prioritization | Use frameworks like MoSCoW, RICE, or Kano to prioritize features based on user input |
| Trade-off Analysis | Present trade-offs between different architectural approaches, technology choices, and feature scopes with pros/cons for each |
| User Persona Generation | Generate detailed user personas based on the product idea to inform UX decisions |
| Market Fit Assessment | Evaluate product-market fit indicators and suggest pivots or refinements |
| Scope Definition | Help users define MVP scope versus future iterations, preventing scope creep while ensuring core value delivery |
| Visual Brainstorming | Generate concept sketches, mind maps, and flow diagrams during brainstorming to visualize ideas |
| Session Persistence | Save and resume brainstorming sessions, preserving all explored ideas and decisions for future reference |

### 4.3 Research Phase (Stage 2 — AFTER Brainstorming, BEFORE Architecture)

Research runs immediately after brainstorming to gather the technical knowledge needed for informed architecture decisions. The Researcher agent cannot produce useful results without understanding what the user wants (from brainstorming), and the Architect cannot make sound decisions without knowing what is technically feasible (from research).

| Feature | Description |
|---|---|
| Technology Research | Research frameworks, libraries, APIs, and SDKs relevant to the project across all target platforms |
| Pattern Discovery | Identify design patterns, architectural patterns, and anti-patterns applicable to the requirements |
| Dependency Analysis | Discover and evaluate third-party dependencies (licenses, security advisories, maintenance status, bundle size, performance impact) |
| Reference Implementation | Find and analyze reference implementations, open source examples, and best practices |
| API Discovery | Research third-party APIs needed for integrations (payment gateways, authentication providers, analytics, notification services) |
| Mobile SDK Research | Research platform-specific SDKs, native APIs, and mobile-specific libraries for iOS and Android |
| Cloud Provider Research | Compare cloud provider offerings, pricing, and capabilities for the project's deployment needs |
| Security Research | Research security best practices, common vulnerabilities, and compliance requirements (GDPR, HIPAA, SOC2, PCI-DSS) relevant to the project |

### 4.4 Architecture & Design Phase (Stage 3 — AFTER Research, BEFORE Planning)

Architecture runs after research because the Architect needs technology evaluations, library comparisons, and API capability assessments to design the system properly. Four agents work in parallel during this stage.

| Feature | Description |
|---|---|
| System Architecture | Generate C4-model architecture diagrams (Context, Container, Component, Code) based on research findings |
| Database Design | Schema design with ERD generation, migration scripts, seed data, and database optimization recommendations |
| API Design | OpenAPI/GraphQL/gRPC schema generation with endpoint specifications, versioning strategy, and rate limiting configuration |
| UI/UX Design | Component hierarchy, wireframe generation, design system specification, responsive layouts, and dark/light mode support |
| Mobile Architecture | Native iOS (SwiftUI/UIKit) and Android (Jetpack Compose/XML) architecture design, or cross-platform (React Native/Flutter) architecture |
| Infrastructure Design | IaC templates (Terraform, Pulumi, Docker, Kubernetes manifests, Helm charts) for all target cloud providers |
| API Gateway Design | API gateway architecture with routing rules, authentication, rate limiting, request/response transformation, and versioning |
| Event Architecture | Event-driven architecture design with message brokers (Kafka, RabbitMQ, Redis Streams, SQS/SNS) |
| Deployment Architecture | Multi-environment deployment architecture (dev, staging, production) with blue-green, canary, or rolling update strategies |
| Security Architecture | Authentication/authorization architecture (OAuth2, OIDC, JWT, RBAC, ABAC), encryption strategy, and network security design |
| Monitoring Architecture | Observability architecture with logging (ELK, CloudWatch), metrics (Prometheus, Grafana, Datadog), tracing (Jaeger, OpenTelemetry), and alerting |

### 4.5 Planning & Configuration Phase (Stage 4 — AFTER Architecture, BEFORE Implementation)

Planning runs after architecture because you need the system blueprint, database schema, API surface, and component hierarchy to decompose work into actionable tasks, build dependency graphs, and assign agents. Planning without architecture produces meaningless task lists.

| Feature | Description |
|---|---|
| Project Planning | Decompose requirements into epics, stories, tasks, and sub-tasks with dependency graphs based on the architecture |
| Task Scheduling | Topological ordering of tasks with critical path identification and parallel execution planning |
| Technology Selection | AI-driven tech stack recommendation (or confirmation) based on architecture decisions and research findings |
| Estimation | Complexity estimation for each task to optimize agent assignment and resource allocation |
| Platform Planning | Plan parallel development tracks for web, iOS, Android, and backend with shared component identification |
| Multi-repo Planning | Plan repository structure (monorepo, polyrepo, or hybrid) with cross-repo dependency mapping and build ordering |
| Deployment Planning | Plan deployment strategy including target environments, rollout approach, rollback procedures, and monitoring |
| Risk Assessment | Identify technical risks, dependency risks, and integration risks with mitigation strategies |
| Resource Allocation | Assign agents to tasks based on complexity, priority, and agent specialization |
| Template & Scaffold Generation | Apply selected UI/UX templates and generate project scaffold based on confirmed tech stack |

### 4.6 Implementation Phase

| Feature | Description |
|---|---|
| Code Generation | Multi-agent parallel code generation across frontend, backend, middleware, mobile, and infrastructure |
| Git Workflow | Automated branch management with feature branches, commits, PR creation, and merge conflict resolution |
| Worktree Isolation | Each agent works in an isolated git worktree to prevent conflicts |
| Context Management | Hierarchical context system (L0/L1/L2) with on-demand loading to minimize token usage |
| Multi-LLM Routing | Route coding tasks to the optimal LLM based on task type, complexity, and model strengths |
| Mobile Development | Native iOS (Swift/SwiftUI) and Android (Kotlin/Jetpack Compose) code generation, or React Native/Flutter cross-platform development |
| Multi-repo Implementation | Coordinated code generation across multiple repositories with cross-repo dependency management |
| Template Application | Apply selected UI/UX templates and design system components during code generation |
| Shared Component Generation | Generate shared business logic, data models, and utilities that work across web and mobile platforms |
| Real-time Collaboration | Humans can edit code simultaneously while agents work, with live conflict detection and resolution |
| Skill Reuse | Leverage previously created skills, hooks, and tools to accelerate implementation of common patterns |
| Database Implementation | Generate database schemas, migrations, seeders, ORM models, and query optimizations |
| API Implementation | Generate API endpoints, middleware, validation, serialization, and documentation from API design specs |
| Integration Implementation | Implement third-party service integrations with proper error handling, retry logic, and circuit breakers |
| **Sandbox Execution** | All generated code runs in isolated containerized sandbox environments — each agent gets its own container with the project's runtime pre-configured, gVisor/Kata isolation for security, multi-language support (Python, Node.js, Go, Java, C#, Dart), and per-sandbox network egress policies |
| **Live Preview** | Real-time browser-based preview of the running application as it is being built — supports hot-reload on code changes, mobile device viewport emulation, VNC access for desktop/Electron apps, and embedded browser for web applications. Users can interact with the app mid-pipeline |
| **Sandbox Dev Environments** | Ephemeral development environments per agent with filesystem access, command execution, and code interpretation — sandboxes are pre-configured with the selected tech stack, dependencies installed, and database seeded |

### 4.7 Review Phase

| Feature | Description |
|---|---|
| Code Quality Review | Automated SAST via Semgrep, SonarQube, ESLint, Pylint, and language-specific linters |
| Security Scanning | Vulnerability scanning via Trivy, secret detection via Gitleaks, DAST via ZAP/Shannon, dependency vulnerability scanning |
| License Compliance | Dependency license scanning via ScanCode/FOSSology/ORT with policy enforcement |
| Architecture Review | Automated verification that implementation matches planned architecture |
| Code Style | Linting, formatting (Prettier, Black, gofmt), and style guide enforcement |
| Accessibility Review | WCAG 2.1 AA/AAA compliance checking, screen reader compatibility testing, keyboard navigation verification, color contrast analysis |
| i18n/L10n Review | Internationalization completeness check — hardcoded strings, locale support, RTL layout, date/number/currency formatting, pluralization rules |
| Mobile Review | Platform-specific review for iOS (App Store guidelines, Human Interface Guidelines) and Android (Material Design guidelines, Play Store policies) |
| Performance Review | Static performance analysis — bundle size, render performance, memory leaks, unnecessary re-renders, N+1 queries |
| API Review | API design review for RESTful conventions, GraphQL best practices, versioning consistency, and error response standardization |

### 4.8 Testing Phase

| Feature | Description |
|---|---|
| Unit Test Generation | Automatic unit test creation for all generated code across all platforms |
| Integration Testing | API and service integration test generation and execution with Testcontainers |
| E2E Testing | Browser-based end-to-end testing via Playwright/Cypress for web, XCTest/Espresso/Detox for mobile |
| UI Component Testing | Component-level rendering and interaction testing via Storybook and Testing Library |
| Visual Regression Testing | Screenshot comparison testing to detect unintended UI changes (Playwright screenshots, Percy) |
| Smoke Testing | Post-build and post-deployment basic sanity verification of critical paths and health endpoints |
| Regression Testing | Full test suite re-execution after any code changes to detect regressions, tracked across fix cycles |
| Performance Testing | Load testing (k6, Artillery), stress testing, Core Web Vitals (Lighthouse), and benchmarking with threshold enforcement |
| Security Testing | Penetration testing (OWASP ZAP), OWASP Top 10 verification, authentication/authorization testing, dependency vulnerability scanning |
| Accessibility Testing | Automated WCAG 2.1 AA/AAA testing with axe-core, Lighthouse, pa11y, and platform-specific accessibility scanners |
| API Contract Testing | Consumer-driven contract testing (Pact, Dredd) for microservices and cross-service API validation |
| Cross-browser Testing | Automated testing across Chrome, Firefox, Safari, Edge via Playwright multi-browser support |
| Mobile Testing | Device-specific testing, responsive layout testing, gesture testing, offline mode testing, deep link testing |
| Mutation Testing | Test suite quality verification via Stryker (JS/TS) and mutmut (Python) — ensures tests actually catch bugs |
| Test Coverage | Coverage analysis with minimum threshold enforcement: line >= 80%, branch >= 70%, function >= 85% |
| Chaos Testing | Optional resilience testing for distributed systems using Chaos Monkey/Litmus |

### 4.9 Debug & Fix Cycle

| Feature | Description |
|---|---|
| Failure Analysis | Automated root cause analysis when tests fail, with stack trace parsing and error classification |
| Fix Generation | AI-powered fix generation with targeted test case creation |
| Regression Testing | Run full test suite after fixes to prevent regressions |
| Fix Verification | Verify fix resolves the original issue and test case passes |
| Iterative Loop | Continue fix-test cycle until all tests pass or escalate to human |
| Cross-platform Fix Propagation | When a fix applies to shared logic, propagate across web and mobile codebases |
| Performance Fix Cycle | Detect performance regressions and generate optimizations |
| Accessibility Fix Cycle | Detect accessibility violations and generate compliant fixes |
| Dependency Conflict Resolution | Resolve version conflicts, breaking changes, and compatibility issues in dependencies |

### 4.10 Deployment & Delivery Phase (Optional)

> **This stage is optional.** Users can skip deployment entirely and receive the generated codebase as a local repository. Not all projects need cloud deployment — libraries, CLI tools, packages, local-only apps, and users who prefer manual deployment can end the pipeline after documentation (S9). Deployment is opt-in during project initialization (S0) or can be triggered later on demand.

| Feature | Description |
|---|---|
| Build & Package | Automated build pipeline with artifact generation for all platforms (web bundles, Docker images, iOS IPA, Android APK/AAB) |
| CI/CD Pipeline Generation | Generate GitHub Actions, GitLab CI, CircleCI, or Jenkins pipeline configurations |
| AWS Deployment | Automated deployment to AWS (ECS, EKS, Lambda, S3+CloudFront, Amplify, Elastic Beanstalk, App Runner) with Terraform/CDK |
| GCP Deployment | Automated deployment to Google Cloud (Cloud Run, GKE, Cloud Functions, Firebase Hosting, App Engine) with Terraform |
| Azure Deployment | Automated deployment to Azure (AKS, Azure Functions, App Service, Static Web Apps, Container Instances) with Terraform/Bicep |
| Vercel Deployment | Automated deployment to Vercel with edge functions, ISR, and preview deployments |
| Railway Deployment | Automated deployment to Railway with database provisioning and environment management |
| Netlify Deployment | Automated deployment to Netlify with serverless functions and form handling |
| Fly.io Deployment | Automated deployment to Fly.io with global edge deployment and Machines API |
| DigitalOcean Deployment | Automated deployment to DigitalOcean App Platform, Droplets, or Kubernetes |
| iOS App Store | Automated iOS build, signing, TestFlight upload, and App Store submission preparation |
| Google Play Store | Automated Android build, signing, internal testing track upload, and Play Store submission preparation |
| Multi-environment Management | Manage dev, staging, and production environments with promotion workflows |
| Rollback Automation | Automated rollback on deployment failure with health check verification |
| SSL/TLS Configuration | Automated SSL certificate provisioning and renewal via Let's Encrypt or cloud provider |
| DNS Configuration | Automated DNS record management for custom domains |
| Documentation Generation | Auto-generated API docs, README, deployment guides, architecture decision records, runbooks, and onboarding guides |
| Handoff Report | Comprehensive report of all decisions made, trade-offs considered, architecture rationale, and maintenance recommendations |
| Monitoring Setup | Automated setup of monitoring, logging, alerting, and error tracking (Sentry, PagerDuty, Datadog) |
| Cost Estimation | Provide estimated monthly cloud costs based on deployment configuration and expected traffic |

---

## 5. Multi-LLM Support

### 5.1 Cloud LLM Providers

| Provider | Models | Use Cases |
|---|---|---|
| **Anthropic** | Claude Opus 4.6, Sonnet 4, Haiku 3.5 | Architecture, complex reasoning, code review, brainstorming |
| **OpenAI** | GPT-4.1, o3, o4-mini, Codex | Code generation, API design, testing, performance optimization |
| **Google** | Gemini 2.5 Pro, 2.5 Flash | Research, documentation, large context analysis, multi-modal input |
| **Mistral** | Mistral Large, Codestral | European compliance, code generation, fast inference |
| **Cohere** | Command R+ | Enterprise search, RAG, document analysis |
| **DeepSeek** | DeepSeek-V3, DeepSeek-Coder | Cost-effective code generation, mathematical reasoning |

### 5.2 Self-Hosted LLM Support

| Platform | Description | Use Cases |
|---|---|---|
| **Ollama** | Local model runner with simple API | Development, privacy-sensitive projects, offline development |
| **vLLM** | High-throughput inference server | Production self-hosted deployments, batch processing |
| **LocalAI** | OpenAI-compatible local API | Drop-in replacement for OpenAI API in air-gapped environments |
| **LM Studio** | Desktop application with local models | Individual developer workstations, experimentation |
| **llama.cpp** | CPU/GPU inference engine | Lightweight local inference, edge deployment |
| **Text Generation WebUI** | Feature-rich local inference | Advanced local model configuration and testing |
| **TGI (Text Generation Inference)** | Hugging Face inference server | Self-hosted production deployments with HuggingFace models |

### 5.3 Self-Hosted Configuration

| Feature | Description |
|---|---|
| Model Registry | Register and manage self-hosted models with capability metadata (context window, strengths, speed) |
| Automatic Detection | Auto-detect running Ollama/vLLM/LocalAI instances on the local network |
| Hybrid Routing | Route tasks between cloud and self-hosted models based on privacy requirements, cost, and capability |
| Offline Mode | Full pipeline operation with only self-hosted models when no internet connection is available |
| Model Download Management | Automated downloading and management of open-weight models (Llama, CodeLlama, DeepSeek-Coder, StarCoder, Phi) |
| Performance Profiling | Benchmark self-hosted models to calibrate routing decisions based on actual throughput and quality |
| GPU/CPU Detection | Auto-detect available hardware (CUDA, Metal, ROCm, CPU) and configure inference accordingly |

**Offline-First Architecture:**

- Full pipeline operation requires at minimum one self-hosted model with 13B+ parameters
- Offline mode automatically disables: GitHub integration, cloud deployment, template remote registry, external API research
- All dependencies must be pre-cached (pip/npm packages, Docker images)
- Context/vector store operates fully local with ChromaDB
- Offline mode indicator in dashboard and CLI

### 5.4 CLI Agent Integration

| CLI Agent | Provider | Integration Method |
|---|---|---|
| **Claude Code** | Anthropic | Direct SDK integration via Claude Agent SDK |
| **OpenAI Codex CLI** | OpenAI | CLI subprocess with structured output parsing |
| **Gemini CLI** | Google | CLI subprocess with structured output parsing |
| **Aider** | Multiple | CLI subprocess for multi-model code editing |
| **Continue** | Multiple | IDE extension integration for collaborative editing |

### 5.5 Model Routing Strategy

The system implements intelligent model routing:

- **Task-based routing**: Different models for different task types (e.g., Claude for architecture, GPT for code gen, Gemini for research, self-hosted for boilerplate)
- **Complexity-based routing**: Use cheaper/faster models (Haiku, Flash, local models) for simple tasks, powerful models (Opus, o3) for complex reasoning
- **Privacy-based routing**: Route sensitive code (auth, payments, PII handling) to self-hosted models; route non-sensitive tasks to cloud models for speed
- **Cost-based routing**: Optimize for cost by routing to the cheapest model that meets quality thresholds for each task type
- **Latency-based routing**: Route time-sensitive tasks (real-time collaboration, interactive brainstorming) to the fastest available model
- **Fallback chains**: If primary model fails or is rate-limited, fall back to alternative provider or self-hosted model
- **User override**: Users can pin specific models to specific agent roles or tasks
- **A/B routing**: Optionally route same tasks to multiple models and select the best output

---

## 6. Agent Architecture (Stage-Grouped, Graph-Centric)

### 6.1 Pipeline Stages and Agent Groups

Based on the MASFactory framework, agents are organized as nodes in a directed computation graph and **grouped into 10 execution stages**. Each stage represents a logical phase of the SDLC with clear entry/exit gates, parallel execution opportunities, and user interaction points.

#### Stage Overview

| Stage | Name | Agents | Parallelism | User Interaction |
|---|---|---|---|---|
| S0 | **Project Initialization** | Orchestrator, GitHub Agent | Sequential | Project type selection, codebase import |
| S1 | **Discovery & Brainstorming** | Brainstorming Agent | Sequential (interactive) | Real-time ideation, requirement refinement |
| S2 | **Research & Analysis** | Researcher | Internal parallel | Review research findings (optional) |
| S3 | **Architecture & Design** | Architect, Designer, Database Agent, API Gateway Agent | Full parallel (fan-out) | Approve architecture, review wireframes |
| S4 | **Planning & Configuration** | Planner, TechStack Builder, Template Agent | Sequential + parallel | Approve plan, select tech stack, choose templates |
| S5 | **Implementation** | Frontend Dev, Backend Dev, Middleware Dev, Mobile Agent, Infrastructure Engineer, Integrations Agent | Full parallel (isolated worktrees) | Real-time code visibility, live editing |
| S6 | **Quality Assurance** | Code Reviewer, Security Auditor, Accessibility Agent, i18n Agent, Performance Agent | Full parallel | Review findings, approve exceptions |
| S7 | **Testing & Validation** | Tester | Internal parallel (test suites) | Review test results, approve coverage |
| S8 | **Debug & Stabilization** | Debugger | Sequential per issue | Escalation if stuck, manual fix input |
| S9 | **Documentation & Knowledge** | Documentation Writer, Skill Creator, Hooks Creator, Tools Creator | Internal parallel | Review generated docs |
| S10 | **Deployment & Delivery** *(optional)* | DevOps Agent, Infrastructure Engineer, Project Manager | Sequential (pipeline) | Approve deployment, verify health. **Skippable** — users can take the generated codebase without deploying |

**Cross-Cutting Agents** (active across all stages):
- **Orchestrator** (#1) — Master coordinator, always active
- **Project Manager Agent** (#30) — Progress tracking, status reports, blocker identification
- **GitHub Agent** (#24) — Repository operations throughout the pipeline

#### 6.1.1 Stage 0: Project Initialization

| # | Agent Role | Responsibility |
|---|---|---|
| 1 | **Orchestrator** | Receive input, classify project type (greenfield/inflight/brownfield), initialize pipeline graph, assign agents |
| 24 | **GitHub Agent** | Repository creation/import, branch protection, CI/CD scaffold, project board setup |

**Project type routing:**
- **Greenfield** → Full pipeline S1-S9, then S10 if deployment opted in
- **Inflight** → Codebase Analysis → Architecture Recovery → Gap Analysis → S1 (scoped) → S4-S9, then S10 if opted in
- **Brownfield** → Legacy Assessment → Modernization Strategy → Safety Net → S3-S9 (incremental), then S10 if opted in
- **Improve** → Codebase Analysis → Metric Baselining → ExperimentLoop (optimize target metrics) → Results Report

#### 6.1.2 Stage 1: Discovery & Brainstorming (Interactive)

| # | Agent Role | Responsibility |
|---|---|---|
| 2 | **Brainstorming Agent** | Facilitate ideation sessions, explore alternatives, trade-off analysis, feature prioritization, scope definition, visual brainstorming |

**User interaction:** Real-time interactive session. User and agent explore ideas together. No downstream work begins until user confirms requirements.

#### 6.1.3 Stage 2: Research & Analysis

| # | Agent Role | Responsibility |
|---|---|---|
| 5 | **Researcher** | Technology research, framework evaluation, API discovery, reference implementations, competitive analysis, security best practices, mobile SDK research |

**Why Research comes BEFORE Architecture:** The Architect needs research results (technology capabilities, library evaluations, API options, competitive patterns) to make informed architecture decisions. Researching after planning would mean planning without knowing what's technically feasible.

#### 6.1.4 Stage 3: Architecture & Design (Parallel)

| # | Agent Role | Responsibility |
|---|---|---|
| 6 | **Architect** | System architecture (C4 model), API design, deployment architecture, security architecture, event architecture |
| 7 | **Designer** | UI/UX design, component hierarchy, wireframes, design system, responsive layouts, dark/light mode |
| 13 | **Database Agent** | Database schema design, ERD generation, migration scripts, seed data, optimization recommendations |
| 14 | **API Gateway Agent** | API gateway architecture, routing rules, rate limiting, request transformation, versioning strategy |

All four agents work in parallel using research results. Architect produces the system blueprint; Designer handles UI/UX; Database Agent designs the data layer; API Gateway Agent designs the API surface.

**User interaction:** Approve system architecture, review wireframes, confirm database design.

#### 6.1.5 Stage 4: Planning & Configuration

| # | Agent Role | Responsibility |
|---|---|---|
| 3 | **Planner** | Task decomposition into epics/stories/tasks, dependency graphs, topological ordering, critical path analysis, sprint planning, resource allocation |
| 4 | **TechStack Builder Agent** | Technology stack recommendation, compatibility checking, version pinning, license compliance (parallel with Planner) |
| 8 | **Template Agent** | Template selection, scaffold generation, design system components, boilerplate code (after TechStack Builder) |

**Why Planning comes AFTER Architecture:** You cannot decompose work into tasks, estimate complexity, assign agents, or build dependency graphs without knowing the system architecture, database schema, API surface, and component hierarchy. Planning without architecture produces meaningless task lists.

**User interaction:** Approve project plan, select/confirm tech stack, choose UI templates.

#### 6.1.6 Stage 5: Implementation (Full Parallel)

| # | Agent Role | Responsibility |
|---|---|---|
| 9 | **Frontend Developer** | Web UI implementation, component coding, client-side logic, SPA/SSR/SSG |
| 10 | **Backend Developer** | API implementation, business logic, data access, server-side rendering |
| 11 | **Middleware Developer** | Integration layer, message queues, caching, auth middleware |
| 12 | **Mobile Agent** | Native iOS (Swift/SwiftUI), Android (Kotlin/Compose), React Native, Flutter |
| 15 | **Infrastructure Engineer** | IaC templates, Docker configs, Kubernetes manifests, cloud provisioning |
| 25 | **Integrations Agent** | Third-party service integrations: payment gateways, auth providers, analytics, notifications |

All agents work in **isolated git worktrees** on separate branches, merged in dependency order after completion.

**User interaction:** Real-time visibility into each agent's progress. Users can edit code simultaneously via CRDT-based collaboration. Agents respond to inline comments.

#### 6.1.7 Stage 6: Quality Assurance (Full Parallel)

| # | Agent Role | Responsibility |
|---|---|---|
| 18 | **Code Reviewer** | Code quality, style, best practices, architecture conformance, DRY/SOLID violations |
| 17 | **Security Auditor** | SAST (Semgrep, SonarQube), DAST (ZAP), secret scanning (Gitleaks), SCA, compliance verification |
| 19 | **Accessibility Agent** | WCAG 2.1 AA/AAA compliance, screen reader support, keyboard navigation, color contrast |
| 20 | **i18n/L10n Agent** | String externalization, locale management, RTL support, date/number formatting, pluralization |
| 21 | **Performance Agent** | Bundle analysis, render performance, memory leak detection, N+1 queries, caching strategy |

All five quality agents run **simultaneously** against the merged codebase. Findings are categorized as critical/high/medium/low with automated fix suggestions.

**User interaction:** Review flagged findings, approve security exceptions, override false positives.

#### 6.1.8 Stage 7: Testing & Validation (Parallel Test Suites)

| # | Agent Role | Responsibility |
|---|---|---|
| 22 | **Tester** | Test generation, execution, coverage analysis across all platforms and test types |

The Tester agent generates and runs **all test types in parallel where possible**:

| Test Type | Tools | Parallelism | Description |
|---|---|---|---|
| Unit Tests | Jest, pytest, JUnit, XCTest | Parallel | Individual function/component testing |
| Integration Tests | Supertest, pytest, Testcontainers | Parallel | API and service integration verification |
| E2E Tests | Playwright, Cypress, Detox | Parallel | Critical user flow validation |
| UI Component Tests | Storybook, Testing Library | Parallel | Component rendering and interaction |
| Visual Regression Tests | Playwright screenshots, Percy | Parallel | Screenshot comparison for UI changes |
| Smoke Tests | Custom health checks | Sequential | Post-build basic sanity verification |
| Performance Tests | k6, Artillery, Lighthouse | Parallel | Load testing, Core Web Vitals, benchmarks |
| Security Tests | OWASP ZAP, custom pen tests | Parallel | Penetration testing, auth/authz verification |
| Accessibility Tests | axe-core, Lighthouse, pa11y | Parallel | WCAG automated compliance |
| API Contract Tests | Pact, Dredd | Parallel | Consumer-driven contract verification |
| Cross-browser Tests | Playwright (Chrome, Firefox, Safari, Edge) | Parallel | Multi-browser compatibility |
| Mobile Device Tests | XCTest, Espresso, Detox | Parallel | Device-specific, gesture, offline mode, deep link testing |
| Mutation Tests | Stryker, mutmut | Sequential | Test suite quality verification |
| Chaos Tests | Chaos Monkey, Litmus | Optional | Resilience testing for distributed systems |

**Coverage targets:** Line >= 80%, Branch >= 70%, Function >= 85%. All critical paths must have E2E coverage.

**User interaction:** Review test results dashboard, approve coverage levels, decide on failing test disposition.

#### 6.1.9 Stage 8: Debug & Stabilization

| # | Agent Role | Responsibility |
|---|---|---|
| 23 | **Debugger** | Root cause analysis, fix generation, regression testing, cross-platform fix propagation |

Iterative loop: Debugger analyzes failures → generates fixes → Tester re-runs affected tests → repeat until all pass or escalate after 3 iterations.

**User interaction:** Escalation point if Debugger cannot resolve after 3 iterations. User can provide manual fixes, hints, or override failing tests.

#### 6.1.10 Stage 9: Documentation & Knowledge

| # | Agent Role | Responsibility |
|---|---|---|
| 29 | **Documentation Writer** | API docs, README, ADRs, deployment guides, runbooks, onboarding guides, changelog, architecture diagrams |
| 26 | **Skill Creator Agent** | Codify successful patterns into reusable skills for future projects |
| 27 | **Hooks Creator Agent** | Create lifecycle hooks for pipeline customization |
| 28 | **Tools Creator Agent** | Build custom MCP tools and integrations |

Documentation is generated from code, architecture decisions, and pipeline artifacts. Meta-agents (Skill/Hook/Tool Creators) run in parallel to capture reusable patterns.

**User interaction:** Review generated documentation, approve skills/hooks/tools before activation.

#### 6.1.11 Stage 10: Deployment & Delivery (Optional, Final Stage)

| # | Agent Role | Responsibility |
|---|---|---|
| 16 | **DevOps Agent** | CI/CD pipeline generation, monitoring setup, logging, alerting, SLA enforcement |
| 15 | **Infrastructure Engineer** | Cloud resource provisioning, IaC deployment, SSL/TLS, DNS configuration |
| 30 | **Project Manager Agent** | Final status report, handoff documentation, timeline summary, lessons learned |

Deployment is the **last and optional stage** — it only executes if the user opted in during project initialization (S0) or triggers it on demand. It runs after all code is written, reviewed, tested, debugged, and documented. Users who skip deployment receive a fully functional local repository with build scripts, CI/CD configurations, and deployment documentation — ready for manual deployment whenever they choose.

When enabled, deployment follows a strict sequential pipeline:

1. Build & Package (web bundles, Docker images, iOS IPA, Android AAB)
2. Deploy to staging environment
3. Run smoke tests against staging
4. **User approval gate** for production deployment
5. Deploy to production (blue-green / canary / rolling)
6. Health check verification
7. Monitoring and alerting setup
8. Rollback automation (if health checks fail)
9. Handoff report generation
10. Cost estimation and optimization recommendations

**User interaction:** Approve production deployment, verify health checks, review cost estimates.

### 6.2 Graph Execution Model

```
User Input (Idea / PRD / Existing Codebase)
    |
    v
+=======================================================+
| STAGE 0: PROJECT INITIALIZATION                       |
|  Orchestrator --> classify project type                |
|  GitHub Agent --> repo setup                           |
|  [USER: select project type, import codebase]         |
+=======================================================+
    |
    |--- Greenfield --------+
    |--- Inflight (analysis)|--- merge into pipeline
    |--- Brownfield (assess)|
    |--- Improve (baseline) |--- ExperimentLoop → Results Report
    |
    v
+=======================================================+
| STAGE 1: DISCOVERY & BRAINSTORMING                    |
|  Brainstorming Agent <--> User (interactive session)  |
|  [USER: explore ideas, confirm requirements]          |
|  GATE G1: Requirements confirmed                      |
+=======================================================+
    |
    v
+=======================================================+
| STAGE 2: RESEARCH & ANALYSIS                          |
|  Researcher (parallel research queries)               |
|  --> tech evaluation, patterns, APIs, competition     |
|  GATE G2: Research completeness check                 |
+=======================================================+
    |
    v
+=======================================================+
| STAGE 3: ARCHITECTURE & DESIGN (parallel)             |
|  +----------+  +---------+  +-------+  +---------+   |
|  | Architect |  | Designer|  |DB Agent| |API GW   |   |
|  | (system)  |  | (UI/UX) |  |(schema)| |Agent    |   |
|  +----------+  +---------+  +-------+  +---------+   |
|  [USER: approve architecture, review wireframes]      |
|  GATE G3: Architecture approved                       |
+=======================================================+
    |
    v
+=======================================================+
| STAGE 4: PLANNING & CONFIGURATION                     |
|  +--------+    +---------------+                      |
|  | Planner|    |TechStack      |--> Template Agent     |
|  | (tasks)|    |Builder (stack)|    (scaffold)         |
|  +--------+    +---------------+                      |
|  [USER: approve plan, select stack, choose templates]  |
|  GATE G4: Plan + stack approved                       |
+=======================================================+
    |
    v
+=======================================================+
| STAGE 5: IMPLEMENTATION (full parallel, worktrees)    |
|  +------+ +------+ +------+ +------+ +------+ +----+ |
|  |Front | |Back  | |Middle| |Mobile| |Infra | |Intg| |
|  |end   | |end   | |ware  | |Agent | |Engr  | |Agent||
|  +------+ +------+ +------+ +------+ +------+ +----+ |
|  [USER: real-time visibility, live code editing]      |
|  GATE G5: All agents complete, code compiles          |
+=======================================================+
    |
    v
+=======================================================+
| STAGE 6: QUALITY ASSURANCE (full parallel)            |
|  +------+ +------+ +------+ +------+ +------+        |
|  |Code  | |Secur.| |A11y  | |i18n  | |Perf  |        |
|  |Review| |Audit | |Agent | |Agent | |Agent |        |
|  +------+ +------+ +------+ +------+ +------+        |
|  [USER: review findings, approve exceptions]          |
|  GATE G6: No critical/blocker findings                |
+=======================================================+
    |
    v
+=======================================================+
| STAGE 7: TESTING & VALIDATION (parallel suites)       |
|  Unit | Integration | E2E | UI Component | Visual     |
|  Smoke | Performance | Security | A11y | Contract     |
|  Cross-browser | Mobile Device | Mutation | Chaos      |
|  [USER: review results, approve coverage]             |
|  GATE G7: Coverage met, no critical failures          |
+=======================================================+
    |
    v
+=======================================================+
| STAGE 8: DEBUG & STABILIZATION                        |
|  Debugger <--> Tester (fix-test loop, max 3 iters)   |
|  [USER: escalation if stuck, manual fix input]        |
|  GATE G8: All tests pass                              |
+=======================================================+
    |
    v
+=======================================================+
| STAGE 9: DOCUMENTATION & KNOWLEDGE                    |
|  Doc Writer | Skill Creator | Hooks Creator | Tools   |
|  [USER: review docs, approve new skills/hooks/tools]  |
|  GATE G9: Documentation complete                      |
+=======================================================+
    |
    v
+=======================================================+
| STAGE 10: DEPLOYMENT & DELIVERY (last)                |
|  DevOps Agent --> CI/CD --> staging --> smoke test     |
|  [USER: approve production deployment]                |
|  Infrastructure --> deploy --> health check --> live   |
|  Project Manager --> handoff report                   |
|  GATE G10: Health checks pass, handoff complete       |
+=======================================================+
    |
    v
  DELIVERED APPLICATION
```

### 6.2.1 Inflight Project Pipeline Variation

For projects joining mid-development, the pipeline adds analysis stages before entering the standard flow:

```
Codebase Import
    |
    v
+-- ANALYSIS PHASE (replaces S1-S2) ---+
|  Codebase Analysis (structure, deps)  |
|  Architecture Recovery (reverse C4)   |
|  Convention Detection (style, naming) |
|  Gap Analysis (missing tests, docs)   |
+---------------------------------------+
    |
    v
S1: Brainstorming (scoped to remaining work)
    |
    v
S3: Architecture (validate/extend recovered architecture)
    |
    v
S4-S10: Standard pipeline (remaining work only)
```

### 6.2.2 Brownfield Project Pipeline Variation

For legacy modernization, the pipeline adds assessment stages and operates incrementally:

```
Legacy Codebase Import
    |
    v
+-- ASSESSMENT PHASE (replaces S1-S2) ----+
|  Legacy Assessment (tech debt, patterns) |
|  Modernization Strategy (strangler fig,  |
|    incremental refactoring, migration)   |
|  Safety Net (characterization tests,     |
|    baseline metrics, integration tests)  |
|  [USER: approve modernization strategy]  |
+------------------------------------------+
    |
    v
S3: Architecture (modernized target architecture)
    |
    v
S4: Planning (incremental modernization plan)
    |
    v
S5-S10: Standard pipeline (one module at a time, with
        regression testing after each module)
```

### 6.3 Communication Protocol

Following MASFactory's Message Adapter pattern:

- **State Flow**: Shared state propagated through the graph (project context, architecture decisions, tech stack selections, deployment targets)
- **Message Flow**: Direct agent-to-agent messages for task handoff, results, and real-time collaboration updates
- **Control Flow**: Orchestrator-driven triggers for phase transitions, error escalation, and human approval gates
- **Event Flow**: Event-driven notifications for real-time collaboration (code changes, test results, deployment status)
- **Broadcast Flow**: System-wide announcements (schema changes, dependency updates, security advisories) that all agents must process

**Message Format Specification:**

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
  "metadata": {}
}
```

- Messages are delivered at-least-once via the event bus
- Ordering guaranteed per source-target pair
- Messages larger than 100KB are stored in blob storage with a reference in the message

### 6.4 Agent Learning & Continuous Improvement

CodeBot agents are not stateless workers — they learn, adapt, and improve over time through multiple feedback loops that capture lessons learned, refine behavior, and build institutional knowledge.

#### 6.4.1 Lessons Learned System

After every pipeline run (and at key stage boundaries), agents automatically capture lessons learned:

| Lesson Type | When Captured | What's Recorded | How It's Used |
|---|---|---|---|
| **Fix Loop Patterns** | After Debug stage (S8) | Root cause of each bug, fix applied, number of iterations, which tests caught it | Agents pre-emptively avoid similar bugs in future projects by checking past fix patterns before generating code |
| **Architecture Decisions** | After Architecture stage (S3) | Options considered, option chosen, rationale, outcome after implementation | Architect Agent reviews past decisions for similar project types to make better choices |
| **Test Gap Analysis** | After Testing stage (S7) | Which tests caught real bugs vs. which areas had no test coverage for bugs found later | Tester Agent generates more targeted tests in areas that historically have defects |
| **Performance Insights** | After QA stage (S6) | Performance bottlenecks found, optimizations applied, before/after metrics | Backend/Frontend agents apply known optimizations proactively |
| **Security Findings** | After QA stage (S6) | Vulnerability patterns found, OWASP categories, remediation applied | Coding agents avoid generating code with known vulnerability patterns |
| **Code Review Feedback** | After QA stage (S6) | Reviewer comments, issues found by type (style, logic, performance, security), resolution | Coding agents internalize common review feedback to reduce review cycles |
| **Deployment Issues** | After Deployment stage (S10) | Deployment failures, configuration mistakes, environment-specific issues | Infra Agent learns environment-specific requirements across projects |
| **User Overrides** | Any stage with user input | When the user overrides an agent's decision, what was changed and why | All agents learn user preferences and adjust defaults accordingly |
| **Experiment Results** | After any ExperimentLoop (Debug, Improve, QA optimization) | Hypothesis proposed, metric before/after, keep/discard decision, code diff size, experiment duration | Agents learn which optimization strategies produce the best improvements for each project type and metric domain |

#### 6.4.2 Agent Behavior Adaptation

| Mechanism | Description |
|---|---|
| **Prompt Refinement** | Agent system prompts are dynamically augmented with relevant lessons learned from past projects — not just static templates. Before each task, agents query episodic memory for "what went wrong last time in this type of task" |
| **Pattern Library** | Successful code patterns, architecture patterns, and configuration patterns are extracted and indexed. Agents search this library before generating new code, preferring proven patterns over novel ones |
| **Anti-Pattern Registry** | Failed approaches, common mistakes, and rejected patterns are captured with context. Agents check this registry before generating code to avoid repeating mistakes |
| **Model Routing Optimization** | Track which LLM produces the best results for each task type. If Claude excels at architecture but GPT-4 is better at unit tests for a specific language, the model router learns this and optimizes routing over time |
| **Quality Score Tracking** | Each agent's output is scored on dimensions (correctness, test pass rate, review approval rate, security scan results). Scores are tracked across projects to identify degradation or improvement trends |
| **User Preference Learning** | Track user choices on tech stack, coding style, architecture patterns, review strictness. Build a user profile that agents use to tailor their defaults and suggestions |

#### 6.4.3 Skill & Knowledge Creation

| Feature | Description |
|---|---|
| **Skill Learning** | Skill Creator Agent codifies successful patterns into reusable skills that all agents can invoke — e.g., "how to set up auth with Clerk in Next.js" becomes a skill after being done successfully twice |
| **Hook System** | Hooks Creator Agent creates lifecycle hooks that allow custom logic at any pipeline stage — learning from failures to add pre-flight checks |
| **Tool Creation** | Tools Creator Agent builds custom MCP tools and integrations that extend agent capabilities — e.g., after discovering a project needs a specific API, it creates a tool for that API |
| **Knowledge Distillation** | After every 10 pipeline runs, the system consolidates episodic observations into distilled knowledge documents — removing noise, keeping insights, creating a growing knowledge base |
| **Cross-Project Transfer** | When a new project starts, agents search the knowledge base for similar past projects and pre-load relevant lessons, patterns, skills, and anti-patterns |

#### 6.4.4 Feedback Loops

```
┌─────────────────────────────────────────────────────────────────┐
│                    FEEDBACK LOOP ARCHITECTURE                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Pipeline Run N                                                  │
│  ┌──────┐  ┌────────┐  ┌──────┐  ┌──────┐  ┌──────┐           │
│  │ Code │→│ Review │→│ Test │→│Debug │→│Deploy│           │
│  └──┬───┘  └───┬────┘  └──┬───┘  └──┬───┘  └──┬───┘           │
│     │          │          │          │          │                 │
│     ▼          ▼          ▼          ▼          ▼                 │
│  ┌──────────────────────────────────────────────────┐            │
│  │           OBSERVATION CAPTURE                     │            │
│  │  (what happened, what worked, what failed)        │            │
│  └──────────────────────┬───────────────────────────┘            │
│                         │                                        │
│                         ▼                                        │
│  ┌──────────────────────────────────────────────────┐            │
│  │           LESSON EXTRACTION                       │            │
│  │  (root causes, patterns, anti-patterns)           │            │
│  └──────────────────────┬───────────────────────────┘            │
│                         │                                        │
│                         ▼                                        │
│  ┌──────────────────────────────────────────────────┐            │
│  │      KNOWLEDGE CONSOLIDATION (every 10 runs)     │            │
│  │  (distill observations → knowledge documents)     │            │
│  └──────────────────────┬───────────────────────────┘            │
│                         │                                        │
│                         ▼                                        │
│  Pipeline Run N+1                                                │
│  ┌──────────────────────────────────────────────────┐            │
│  │  CONTEXT AUGMENTATION                             │            │
│  │  (pre-load relevant lessons + patterns + skills)  │            │
│  └──────────────────────────────────────────────────┘            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### 6.4.5 Measurable Improvement Metrics

| Metric | Description | Target |
|---|---|---|
| **Fix loop reduction** | Average number of debug iterations decreases across projects | < 3 iterations by project 10 (vs. < 5 for project 1) |
| **First-pass review approval** | % of code that passes review without changes | > 70% by project 10 |
| **Test coverage precision** | % of generated tests that catch actual regressions | > 60% by project 10 |
| **Security scan pass rate** | % of generated code that passes security scanning on first attempt | > 85% by project 10 |
| **Deployment success rate** | % of deployments succeeding without rollback | > 95% by project 10 |
| **User override frequency** | How often users override agent decisions (should decrease) | < 10% by project 10 |
| **Skill reuse rate** | % of tasks that leverage previously created skills | > 40% after 10 projects |

### 6.5 Agent Lifecycle Management

```
Agent States: IDLE → INITIALIZING → RUNNING → WAITING → COMPLETED/FAILED → TERMINATED
```

- **Spawn**: Orchestrator creates agent with role-specific config and system prompt
- **Initialize**: Agent loads context (L0), connects to LLM provider, registers tools
- **Execute**: Agent processes tasks, produces artifacts, emits events
- **Checkpoint**: Agent state serialized at phase boundaries for resume
- **Terminate**: Agent releases resources, worktree cleaned up, metrics recorded
- **Health Check**: Orchestrator pings agents every 30s; unresponsive agents are restarted
- **Resource Limits**: Per-agent token budget, execution timeout, memory limit
- **Graceful Degradation**: If agent fails 3 times, orchestrator reassigns to fallback model/agent

### 6.6 Intelligent Error Recovery & Self-Healing

CodeBot doesn't just handle errors — it diagnoses root causes, applies intelligent fixes, and learns from failures to prevent recurrence.

#### Error Taxonomy:

| Category | Examples | Handling |
|---|---|---|
| **Transient** | LLM rate limit, network timeout, API 503 | Retry with exponential backoff (max 3), auto-switch to fallback LLM provider |
| **Recoverable** | Test failure, lint error, type error | Route to Debugger agent for automated fix with root cause analysis |
| **Blocking** | Missing dependency, invalid config | Pause pipeline, attempt auto-resolution (install dep, suggest config), notify user if unresolved |
| **Fatal** | Credential invalid, disk full, OOM | Stop pipeline, preserve full state for resume, alert user with diagnosis |
| **Quality Gate** | Security vulnerability, coverage below threshold | Block phase transition, route to fix agent with specific remediation guidance |
| **Cascade** | Failure in one agent affecting downstream agents | Isolate failure, roll back affected agent's work, re-route pipeline around failed stage if possible |

#### Self-Healing Capabilities:

| Feature | Description |
|---|---|
| **Automatic Dependency Resolution** | When a build fails due to missing dependencies, the system analyzes the error, installs the correct packages, and retries |
| **Configuration Auto-Fix** | When configuration errors are detected (wrong ports, missing env vars, invalid paths), the system attempts to fix them using project context |
| **Test Flakiness Detection** | Tests that fail intermittently are flagged, isolated, and re-run with increased timeout or in a clean sandbox — persistent flakes are reported separately from real failures |
| **LLM Fallback Chain** | If the primary LLM fails or produces low-quality output (detected by validation), the system automatically retries with an alternative model before involving the user |
| **Pipeline Resume** | After any failure, the pipeline can resume from the exact point of failure — no re-running completed stages. Full state is checkpointed at every stage boundary |
| **Partial Rollback** | If a stage produces broken output, the system can roll back just that stage's artifacts without affecting other completed work |
| **Dead Letter Queue** | Failed messages stored for manual inspection and replay with full context of what was being attempted |
| **Circuit Breaker** | If an LLM provider fails 5 consecutive requests, circuit opens and routes to fallback provider. Auto-resets after 5 minutes |

### 6.7 Prompt Engineering Standards

- All agent system prompts stored as versioned Markdown files in `templates/prompts/`
- Prompts follow a standard structure: Role → Context → Instructions → Constraints → Output Format
- Prompt versioning tied to agent version; changes require review
- Prompt testing: each prompt has a test suite with expected behavior assertions
- Token budget per prompt: L0 context + system prompt must fit in 4K tokens
- No hardcoded prompts in agent code; all prompts loaded from template files

### 6.8 Agent Safety Guardrails

- Skill/Hook/Tool Creator agents operate in a sandboxed environment
- All created artifacts are reviewed by Code Reviewer and Security Auditor before activation
- Version control for all created skills, hooks, and tools with rollback capability
- Rate limiting: max 5 new skills/hooks/tools per pipeline run
- Capability boundaries: created tools cannot access credentials, modify other agents' prompts, or bypass security gates
- Human approval required for tools that access external networks or execute arbitrary code

---

## 7. Context Management

CodeBot implements a unified, observable, self-evolving context system that gives every agent access to the right information at the right time — without overwhelming token budgets. The system combines hierarchical context loading, episodic memory, and real-time synchronization as first-class platform features.

> **Research foundations:** The tiered loading architecture draws from OpenViking's filesystem-paradigm context model (L0/L1/L2 hierarchy, directory-based retrieval, observable retrieval trajectories). The episodic memory subsystem applies techniques from claude-mem (lifecycle hooks, semantic compression, progressive disclosure). These are not direct dependencies — CodeBot builds these capabilities natively, informed by the patterns these projects validated.

### 7.1 Hierarchical Context System

CodeBot manages context in three tiers, loading progressively to minimize token consumption while ensuring agents always have what they need:

| Tier | Content | Loading Strategy | Token Budget |
|---|---|---|---|
| **L0 (Always Loaded)** | Project summary, current task, agent role instructions, tech stack config, active template | Pre-loaded at agent initialization from the context store | ~2K tokens |
| **L1 (On-Demand)** | Relevant code files, architecture docs, test results, deployment configs, cross-repo context | Loaded when agent requests or when the context adapter detects relevance via directory-based retrieval + semantic search | ~10K tokens |
| **L2 (Deep Retrieval)** | Full codebase search, external documentation, research results, historical decisions, multi-repo search | RAG-based retrieval with recursive directory search + vector + keyword hybrid search | ~20K tokens |

**How it works:**
- Each project has a **context directory tree** (filesystem-paradigm) that organizes memories, resources, skills, and artifacts in a navigable hierarchy — not a flat vector dump
- Agents mount the project's L0 directory at init, then query L1/L2 paths on demand
- All retrieval trajectories are **observable**: the dashboard shows exactly what context each agent loaded and why, enabling debugging of agent reasoning
- Automatic **context compression** summarizes older context entries to keep token budgets within limits while preserving critical decisions

### 7.2 Episodic Memory

CodeBot captures **cross-session and cross-project memory** — what happened, what worked, what failed, and what was decided — so agents learn from experience rather than starting fresh on every pipeline run.

| Feature | Description |
|---|---|
| **Automatic Observation Capture** | Lifecycle hooks at key agent events (task start, tool completion, decision point, task end) automatically record agent activity as retrievable observations |
| **Semantic Compression** | AI-generated summaries of observations reduce token overhead (~10x savings) while preserving critical context about past decisions and outcomes |
| **Progressive Disclosure** | Three-layer retrieval: compact index → timeline context → full observation details. Agents start with lightweight summaries and drill into details only when needed |
| **Cross-Session Search** | Semantic + keyword hybrid search across all previous sessions for a project, enabling agents to find relevant past work without re-reading entire histories |
| **Cross-Project Learning** | Agents can search episodic memory across projects to find reusable patterns, solutions to similar problems, and lessons learned from previous builds |
| **Decision Audit Trail** | All agent decisions are captured with rationale, enabling retrospective analysis, debugging, and continuous improvement of agent behavior |
| **Memory Consolidation** | Episodic observations are periodically consolidated into long-term project memory in the context store, creating a growing knowledge base per project |

### 7.3 Context Sources

| Source | Purpose | Backing Store |
|---|---|---|
| **Project Context Store** | Primary hierarchical context — project knowledge, decisions, learnings, brainstorming history, architecture artifacts | Filesystem-paradigm context DB (SQLite + file tree) |
| **Episodic Memory** | Cross-session observations, decisions, tool usage history, compressed summaries | Vector DB (Chroma) + SQLite with semantic + keyword search |
| **Code Context** | Code-aware semantic search with AST understanding across all repositories | Vector DB (Chroma/Weaviate) + Tree-sitter indexing |
| **Documentation** | Project docs, API specs, requirement tracing, template docs | RAG pipeline with deep document understanding |
| **Tool Results** | Real-time tool output injection (test results, scan reports, deployment status) | MCP Protocol event stream |
| **Collaboration Context** | Real-time edits, cursor positions, and change streams from human collaborators | CRDT Store (Yjs/Automerge) |
| **Cross-repo Context** | Shared models, API contracts, and dependency information across repositories | Multi-repo index with cross-reference tracking |
| **Template Context** | Selected template components, design tokens, and usage patterns | Template registry |
| **Deployment Context** | Current deployment state, environment variables, resource utilization | Cloud provider API adapters |

### 7.4 Context Synchronization

| Feature | Description |
|---|---|
| Real-time Sync | Context updates are pushed to all active agents within 500ms of any change via the platform event bus |
| Conflict Resolution | CRDT-based conflict resolution for simultaneous human and agent edits |
| Cross-repo Sync | Changes in one repository that affect shared interfaces trigger context updates in dependent repositories |
| Context Compression | Automatic summarization of older context to keep token budgets within limits |
| Context Versioning | All context changes are versioned, allowing agents to reason about how context evolved |
| Observable Retrieval | Retrieval trajectories are visualized in the dashboard — developers can trace exactly what context each agent loaded and why |
| Memory Consolidation | Episodic observations are periodically consolidated into long-term project memory, creating a growing knowledge base |

---

## 8. User Interface

### 8.1 Primary Interface: Web Dashboard

| Component | Description |
|---|---|
| **Pipeline Stage View** | Visual pipeline showing all 10 stages (S0-S10) with current stage highlighted, completed stages checked, and upcoming stages grayed out. Click any stage to drill into agent details |
| **Agent Activity Panel** | Real-time view of every active agent: what it is currently doing, which files it is editing, tokens consumed, artifacts produced, and estimated progress percentage |
| **Agent Detail View** | Deep dive into a single agent: live streaming output, current LLM conversation, tool invocations, decision log, and performance metrics |
| **Interactive Input Panel** | Unified panel for all user interaction points: approval gates, clarification requests, tech stack selection, template selection, and manual overrides. Shows pending inputs with context |
| **Project Board** | Kanban-style board showing tasks across stages with agent assignments, dependencies, and blockers |
| **Code Viewer** | Syntax-highlighted code viewer with diff support, inline comments, multi-file comparison, and live agent edit indicators |
| **Terminal** | Embedded terminal for manual intervention and direct command execution |
| **Chat Interface** | Natural language interaction with the Orchestrator and individual agents. Users can ask any agent to explain its decisions or change approach |
| **Review Panel** | Code review interface with inline comments, approval workflow, severity filtering, and automated suggestion application |
| **Test Results Dashboard** | Comprehensive view of all test suites: unit, integration, E2E, UI component, visual regression, smoke, performance, security, accessibility, contract, cross-browser, mobile, and mutation tests with pass/fail/skip counts and coverage metrics |
| **Monitoring Dashboard** | Token usage per agent, cost tracking per stage, LLM performance metrics, and cloud cost estimates |
| **Brainstorming Board** | Interactive brainstorming interface with mind maps, concept cards, idea voting, and session history |
| **Template Gallery** | Visual gallery of available UI/UX templates with live previews and one-click selection |
| **Tech Stack Configurator** | Interactive tech stack selection with compatibility checking, recommendation engine, and preset configurations |
| **Live Preview Panel** | Real-time browser-based preview of the running application inside its sandbox — supports hot-reload on code changes, mobile device emulation (viewport simulation), VNC for desktop apps, and side-by-side before/after comparisons |
| **Sandbox Manager** | View and manage all active sandbox environments — start/stop/restart sandboxes, view resource usage, access sandbox terminals, inspect running processes, and configure per-sandbox network policies |
| **Deployment Dashboard** | Multi-environment deployment status, health checks, rollback controls, smoke test results, and cost monitoring |
| **Collaboration Workspace** | Real-time collaborative editing space where humans and agents work simultaneously with presence indicators |
| **Multi-repo Navigator** | Cross-repository file browser, dependency graph visualizer, and impact analysis tool |
| **Notification Center** | Centralized notifications for approval requests, deployment status, test results, security alerts, and agent escalations |
| **Project History** | Full audit trail of every decision made, every agent action taken, every user approval, with timestamps and rationale |
| **Cost & Budget Tracker** | Real-time token usage and cloud cost tracking per agent, per stage, per LLM provider. Budget alerts, spend forecasts, and cost optimization recommendations |
| **Project Analytics** | Post-run analytics: time per stage, agent efficiency scores, quality gate pass rates, test coverage trends, improvement over previous runs. Exportable reports |
| **Dependency Graph** | Interactive visualization of project dependencies — packages, services, API contracts, database relationships — with vulnerability and update indicators |
| **Architecture Visualizer** | Auto-generated architecture diagrams (C4 model) from the actual generated code — not just planned architecture. Side-by-side comparison of planned vs. actual |
| **Git Timeline** | Visual git history showing branches, merges, agent commits, and human commits on an interactive timeline. Click any commit to see the agent's reasoning |
| **Knowledge Base Browser** | Browse the growing knowledge base of lessons learned, patterns, anti-patterns, and skills across all projects. Search, filter, and tag entries |

### 8.2 Real-time Collaboration Features

| Feature | Description |
|---|---|
| Live Cursor Tracking | See where agents and humans are working in real-time across the codebase |
| Simultaneous Editing | Multiple humans and agents can edit different files simultaneously with CRDT-based conflict resolution |
| Agent Activity Feed | Live stream of agent actions, decisions, and outputs |
| Inline Commenting | Comment on agent-generated code in real-time; agents respond to comments |
| Approval Gates | Human approval required at configurable checkpoints (architecture sign-off, pre-deployment review, etc.) |
| Voice/Video Integration | Optional voice or video channel for human team members to discuss with agents via speech-to-text |
| Change Broadcast | All participants see changes propagated in real-time across the entire project |
| Conflict Resolution UI | Visual interface for resolving merge conflicts between human and agent edits |

### 8.3 Secondary Interface: CLI

| Command | Description |
|---|---|
| `codebot init` | Initialize a new project from PRD, idea description, or existing codebase |
| `codebot brainstorm` | Start an interactive brainstorming session |
| `codebot plan` | Generate project plan from requirements |
| `codebot start` | Start the agent pipeline |
| `codebot status` | Check pipeline status and agent progress |
| `codebot review` | Enter review mode for human approval |
| `codebot deploy` | Trigger deployment pipeline to specified environment |
| `codebot rollback` | Rollback to previous deployment |
| `codebot config` | Configure LLM providers, agent settings, cloud providers |
| `codebot templates` | Browse and select UI/UX templates |
| `codebot stack` | Configure or view tech stack selection |
| `codebot agents` | List, configure, and monitor active agents |
| `codebot collab` | Start real-time collaboration session |
| `codebot import` | Import existing codebase for inflight/brownfield projects |
| `codebot repos` | Manage multi-repository configuration |
| `codebot costs` | View LLM and cloud cost tracking |
| `codebot skills` | List, create, and manage agent skills |
| `codebot hooks` | List, create, and manage lifecycle hooks |
| `codebot tools` | List, create, and manage custom tools |

### 8.4 Tertiary Interface: IDE Extensions

| IDE | Integration |
|---|---|
| **VS Code** | Extension with sidebar panel, inline agent suggestions, and real-time collaboration |
| **JetBrains (IntelliJ, WebStorm, etc.)** | Plugin with tool window, code inspections, and agent integration |
| **Neovim** | Lua plugin with telescope integration and agent commands |
| **Cursor** | Native integration leveraging Cursor's AI infrastructure |

---

## 9. Project Type Support

### 9.1 Greenfield Projects

| Feature | Description |
|---|---|
| From-Scratch Generation | Build entirely new projects from an idea, PRD, or brainstorming session |
| Full Pipeline | Execute the complete pipeline from brainstorming through deployment |
| Template Bootstrap | Initialize project with selected UI/UX template and tech stack |
| Repository Setup | Automated repository creation, branch protection, CI/CD setup, and team configuration |
| Scaffold Generation | Generate complete project structure with boilerplate, configuration, and initial code |

### 9.2 Inflight Projects

| Feature | Description |
|---|---|
| Codebase Analysis | Deep analysis of existing codebase to understand architecture, patterns, dependencies, and conventions |
| Convention Detection | Automatically detect and adopt existing coding conventions, naming patterns, and project structure |
| Dependency Map | Build a comprehensive dependency map of the existing codebase |
| Knowledge Extraction | Extract implicit knowledge from code, comments, commit history, and documentation |
| Seamless Continuation | Continue development following existing patterns and architecture decisions |
| Gap Analysis | Identify missing tests, documentation, and security measures in the existing codebase |
| Incremental Enhancement | Add new features, fix bugs, or improve existing code without disrupting the existing architecture |

### 9.3 Brownfield Projects

| Feature | Description |
|---|---|
| Legacy Analysis | Analyze legacy codebases to understand outdated patterns, deprecated dependencies, and technical debt |
| Modernization Planning | Generate a prioritized modernization plan with risk assessment and effort estimation |
| Incremental Refactoring | Refactor code incrementally while maintaining backward compatibility |
| Migration Automation | Automate migrations (framework upgrades, language version updates, database migrations) |
| Technical Debt Tracking | Identify, categorize, and prioritize technical debt items |
| Strangler Fig Pattern | Implement gradual replacement of legacy components using the strangler fig pattern |
| Compatibility Testing | Ensure modernized components maintain compatibility with legacy systems during transition |
| Documentation Generation | Generate documentation for undocumented legacy code to aid understanding |

### 9.4 Improve Mode Projects (Autonomous Optimization)

Inspired by autonomous experimentation frameworks (e.g., Karpathy's autoresearch), Improve mode takes an existing codebase and autonomously runs structured experiment loops to optimize specified quality metrics — without human intervention during the loop.

| Feature | Description |
|---|---|
| **Optimization Target Selection** | User specifies what to optimize: performance, security, test coverage, accessibility, bundle size, or a combination. Each target maps to measurable metrics (Lighthouse score, Semgrep findings count, mutation kill rate, axe-core violations, etc.) |
| **Time Budget** | User sets a total time budget for the experiment session (e.g., "run for 4 hours"). Individual experiments get a fixed time slice (configurable, default 10 minutes) to ensure comparable results across attempts |
| **Constraint Specification** | User defines boundaries: "do not change public API," "do not modify auth module," "stay within 500-token budget per experiment." Constraints are enforced before each experiment is applied |
| **Metric Baselining** | Before any experiments, the system runs the full measurement suite to establish baseline scores across all target metrics. All experiments are compared against this baseline |
| **ExperimentLoop Execution** | The core loop: (1) agent proposes optimization hypothesis, (2) applies change to experiment branch, (3) runs measurement suite, (4) compares to baseline, (5) keeps if improved and no regressions, (6) discards otherwise, (7) logs result, (8) repeats |
| **Multi-Metric Regression Guard** | Improvements in the target metric must not regress other metrics beyond a configurable threshold. A security improvement that breaks 5 tests is discarded |
| **Simplicity Criterion** | Changes that increase code complexity (cyclomatic complexity, coupling, LOC) must produce proportionally larger metric improvements. Simplifications that maintain metrics are always kept |
| **Experiment Log** | Every experiment is logged to `experiment_log.tsv`: commit hash, hypothesis, metric before, metric after, delta, keep/discard, code diff size, duration. This log is the primary artifact of an Improve session |
| **Git-Based Experiment Tracking** | Each experiment gets its own branch. Success = merge to working branch. Failure = branch deleted. The git history shows only successful improvements, while the experiment log captures the full history of attempts |
| **Circuit Breakers** | The loop stops automatically when: time budget exhausted, token budget exhausted, N consecutive experiments show no improvement, or all target metrics exceed user-defined "good enough" thresholds |
| **Human Review Gate** | After the loop completes, all merged experiments are presented as a single PR for human review before merging to main. Each experiment commit includes the hypothesis and metric deltas in the commit message |
| **Results Report** | A summary report showing: baseline vs. final metrics, total experiments run, keep/discard ratio, top improvements by impact, and cost breakdown (tokens, time, compute) |

**Improve mode pipeline:**
```
Codebase Import → Metric Baselining → ExperimentLoop → Results Report → Human Review PR
                                          ↑                    |
                                          └────────────────────┘
                                          (repeat until budget exhausted)
```

---

## 10. Cost Intelligence & Budget Management

CodeBot tracks and optimizes costs across all dimensions — LLM token usage, cloud infrastructure, and development time — giving users full visibility and control.

### 10.1 Token Cost Tracking

| Feature | Description |
|---|---|
| **Per-Agent Cost** | Real-time tracking of tokens consumed and cost incurred by each agent, broken down by input/output tokens and model used |
| **Per-Stage Cost** | Aggregate cost per pipeline stage (S0-S10) with comparison to previous runs |
| **Model Cost Comparison** | Side-by-side comparison of cost vs. quality for different LLMs on the same task, enabling informed model routing decisions |
| **Budget Limits** | Set hard budget limits per project, per run, or per stage. Pipeline pauses and alerts the user when approaching limits |
| **Cost Forecasting** | Based on project complexity and historical data, forecast total pipeline cost before starting. Users can approve or adjust before committing |
| **Optimization Suggestions** | After each run, suggest cheaper model alternatives that would have produced equivalent quality for specific task types |

### 10.2 Cloud Cost Estimation

| Feature | Description |
|---|---|
| **Pre-Deployment Estimate** | Before deploying, estimate monthly cloud costs based on selected infrastructure, expected traffic, and resource requirements |
| **Right-Sizing** | Recommend appropriate instance sizes and service tiers based on actual application requirements, not worst-case assumptions |
| **Cost Alerts** | Monitor deployed application costs and alert when spending exceeds thresholds |
| **Multi-Cloud Comparison** | Compare deployment costs across AWS, GCP, and Azure for the same application to identify the cheapest option |

---

## 11. Project Intelligence

### 11.1 Project Template Generation

After completing a project, CodeBot can extract and save the project's architecture, patterns, and configurations as a reusable template for future projects.

| Feature | Description |
|---|---|
| **Auto-Template Extraction** | After a successful deployment, extract the project's architecture, tech stack, code patterns, and configurations into a reusable project template |
| **Template Parameterization** | Automatically identify project-specific values (names, endpoints, credentials) and replace them with configurable parameters |
| **Template Marketplace** | Share and discover project templates. Users can publish templates (with sensitive data removed) for community reuse |
| **Template Versioning** | Templates are versioned and can be updated when new patterns or best practices are discovered |
| **Quick Start from Template** | Start a new project from a template — skip brainstorming and architecture stages, jump directly to customization and implementation |

### 11.2 Project Analytics & Insights

| Feature | Description |
|---|---|
| **Pipeline Performance Report** | After each run: time per stage, agent efficiency scores, quality gate pass rates, token usage breakdown, cost analysis |
| **Quality Trend Dashboard** | Track quality metrics across projects and runs: test coverage, security scan results, code review approval rates, deployment success rates |
| **Agent Performance Leaderboard** | Which agents are most effective, which need prompt tuning, which benefit most from model upgrades |
| **Improvement Trajectory** | Visualize how the system improves over time — fewer fix loops, higher first-pass approval, better test coverage precision |
| **Complexity Analysis** | After implementation, analyze code complexity metrics (cyclomatic complexity, coupling, cohesion) and compare to industry benchmarks |
| **Technical Debt Score** | Continuous technical debt scoring with trend analysis — is technical debt growing or shrinking across runs? |
| **Time-to-Value Tracking** | Track the elapsed time from idea input to deployed application, with breakdown by wait time (user input) vs. active time (agent work) |

### 11.3 Rollback & Version Recovery

| Feature | Description |
|---|---|
| **Stage-Level Rollback** | Roll back any individual stage's output without affecting other stages — e.g., revert to a previous architecture without re-running brainstorming |
| **Full Pipeline Rollback** | Roll back the entire pipeline to any previous checkpoint — restore the project to a known good state |
| **Code Version Recovery** | Every code change by every agent is committed with full context. Any change can be reverted individually |
| **Config Snapshot** | Full project configuration (tech stack, template, deployment config) is snapshotted at each stage boundary. Any config state can be restored |
| **Deployment Rollback** | One-click rollback of deployed applications to any previous deployment version with automatic health check verification |
| **Branching from Checkpoint** | Create a new pipeline branch from any checkpoint — explore alternative approaches without losing the original path |

### 11.4 Smart Suggestions & Proactive Insights

| Feature | Description |
|---|---|
| **Architecture Recommendations** | Based on project requirements, proactively suggest architectural patterns used successfully in similar past projects |
| **Dependency Risk Alerts** | Proactively flag dependencies with known vulnerabilities, deprecated status, low maintenance activity, or license concerns |
| **Performance Prediction** | Before deployment, predict performance bottlenecks based on architecture patterns and code analysis — suggest optimizations before they become problems |
| **Scalability Assessment** | Analyze the generated architecture for scalability concerns and suggest improvements before deployment |
| **API Design Review** | Proactively review generated API designs for RESTful best practices, consistency, versioning strategy, and documentation completeness |
| **Database Query Analysis** | Analyze generated database queries for N+1 problems, missing indexes, and inefficient joins before they reach production |
| **Accessibility Pre-Check** | During implementation (not just review), proactively ensure components meet WCAG standards — prevention over detection |

---

## 12. Extensibility & Plugin System

### 12.1 Plugin Architecture

| Feature | Description |
|---|---|
| **Agent Plugins** | Third parties can create custom agents that plug into the pipeline at any stage. Plugins define their agent's role, tools, and position in the graph |
| **Tool Plugins** | Custom MCP tools can be installed to give agents new capabilities — access to proprietary APIs, internal tools, custom workflows |
| **Template Plugins** | Custom UI/UX templates and design systems can be packaged as plugins and shared across teams |
| **LLM Provider Plugins** | Add support for new LLM providers beyond the built-in ones — custom model endpoints, fine-tuned models, specialized models |
| **Stage Plugins** | Insert custom stages into the pipeline — e.g., a compliance review stage between QA and deployment for regulated industries |
| **Notification Plugins** | Custom notification channels — Slack, Teams, Discord, PagerDuty, custom webhooks |

### 12.2 Webhook & Event System

| Feature | Description |
|---|---|
| **Pipeline Events** | Subscribe to events at any granularity: stage start/end, agent start/end, quality gate pass/fail, deployment status change |
| **Webhook Delivery** | Reliable webhook delivery with retry logic, signature verification, and delivery logs |
| **Event Filtering** | Subscribe to specific event types, specific agents, or specific stages — don't get overwhelmed with events you don't care about |
| **Custom Actions** | Trigger custom actions on events — e.g., post to Slack when deployment succeeds, create a Jira ticket when a quality gate fails |

### 12.3 API-First Design

| Feature | Description |
|---|---|
| **Full REST API** | Every feature available in the dashboard is available via the API — start pipelines, check status, approve gates, retrieve artifacts |
| **GraphQL Endpoint** | Flexible querying of project data, agent status, and analytics — get exactly the data you need without over-fetching |
| **SDK Libraries** | Official client libraries for Python, TypeScript, and Go — making API integration straightforward |
| **CLI Tool** | Full-featured CLI for headless operation, CI/CD integration, and automation scripting |

---

## 13. Template & Tech Stack System

### 13.1 UI/UX Template System

| Category | Available Templates |
|---|---|
| **Component Libraries** | Material UI (MUI), Ant Design, Chakra UI, Mantine, Radix UI, Headless UI |
| **Tailwind-based** | Tailwind UI, Shadcn/ui, DaisyUI, Flowbite, HyperUI |
| **CSS Frameworks** | Bootstrap 5, Bulma, Foundation |
| **Mobile** | React Native Paper, NativeBase, React Native Elements, Flutter Material, Flutter Cupertino |
| **Admin/Dashboard** | AdminLTE, CoreUI, Tremor, Refine |
| **E-commerce** | Medusa UI, Saleor Storefront |
| **Custom** | User-provided design system with token import (Figma tokens, Style Dictionary) |

| Feature | Description |
|---|---|
| Template Preview | Visual preview of each template with live interactive examples |
| Template Composition | Mix and match components from different templates within a single project |
| Design Token Import | Import design tokens from Figma, Sketch, or Style Dictionary for custom design systems |
| Theme Customization | Customize colors, typography, spacing, and border radius after template selection |
| Component Catalog | Browsable catalog of all available components in the selected template |

### 13.2 Tech Stack Selection System

| Category | Options |
|---|---|
| **Frontend Language** | TypeScript, JavaScript, Dart (Flutter) |
| **Frontend Framework** | React, Next.js, Vue, Nuxt, Svelte, SvelteKit, Angular, Astro, Remix, Solid |
| **Mobile Framework** | Swift/SwiftUI (iOS native), Kotlin/Jetpack Compose (Android native), React Native, Flutter, Expo |
| **Backend Language** | TypeScript/Node.js, Python, Go, Rust, Java, C#, Ruby, Elixir |
| **Backend Framework** | Express, Fastify, NestJS, Django, FastAPI, Flask, Gin, Axum, Spring Boot, ASP.NET, Rails, Phoenix |
| **Database** | PostgreSQL, MySQL, MongoDB, SQLite, Redis, DynamoDB, CockroachDB, PlanetScale, Supabase, Firebase |
| **ORM/ODM** | Prisma, Drizzle, TypeORM, Sequelize, SQLAlchemy, GORM, Diesel, Entity Framework, ActiveRecord |
| **Authentication** | NextAuth, Clerk, Auth0, Supabase Auth, Firebase Auth, Keycloak, custom JWT |
| **Payment** | Stripe, PayPal, Square, Braintree, Lemon Squeezy, Paddle |
| **Hosting** | AWS, GCP, Azure, Vercel, Railway, Netlify, Fly.io, DigitalOcean, Render, Cloudflare |
| **Message Queue** | Kafka, RabbitMQ, Redis Streams, SQS, Bull/BullMQ |
| **Search** | Elasticsearch, OpenSearch, Meilisearch, Typesense, Algolia |
| **Monitoring** | Prometheus + Grafana, Datadog, New Relic, Sentry, LogRocket |
| **CDN** | Cloudflare, CloudFront, Fastly, Akamai |
| **Email** | SendGrid, Postmark, Resend, AWS SES, Mailgun |
| **File Storage** | S3, GCS, Cloudflare R2, MinIO, UploadThing |

| Feature | Description |
|---|---|
| AI Recommendation | AI recommends optimal tech stack based on project requirements, team size, performance needs, and budget |
| Compatibility Check | Verify that selected technologies are compatible with each other |
| Opinionated Presets | Pre-configured stack presets (e.g., "T3 Stack", "MERN", "Django + React", "Rails + Hotwire", "Go + HTMX") |
| Custom Stack | Users can define completely custom stacks with any combination of technologies |
| Version Pinning | Pin specific versions of frameworks and libraries for reproducibility |
| License Compliance | Verify that all selected technologies comply with organizational license policies |

---

## 14. Non-Functional Requirements

### 14.1 Performance

| Metric | Target |
|---|---|
| Agent startup time | < 5 seconds per agent |
| Inter-agent message latency | < 500ms |
| Concurrent agents | Support 30+ parallel agents |
| Context retrieval latency | < 2 seconds for L1, < 5 seconds for L2 |
| Real-time collaboration latency | < 200ms for edit propagation |
| Deployment automation | < 10 minutes from build to live (excluding cloud provisioning) |
| Brainstorming response time | < 3 seconds for interactive brainstorming responses |
| Template rendering | < 2 seconds for template preview generation |
| Cross-repo context resolution | < 5 seconds for cross-repository dependency analysis |

### 14.2 Reliability

| Metric | Target |
|---|---|
| Agent failure recovery | Automatic retry with exponential backoff and model fallback |
| Checkpoint/resume | Save pipeline state every phase; resume from last checkpoint on any failure |
| Data durability | All artifacts persisted to git and database with automatic backup |
| Graceful degradation | Continue with available agents if one provider is down; fall back to self-hosted models if cloud is unavailable |
| Pipeline availability | 99.5% uptime for the orchestration engine |
| Zero data loss | All generated code, decisions, and artifacts are version-controlled and persisted |

### 14.3 Security

| Requirement | Implementation |
|---|---|
| API key management | Encrypted credential store (age, SOPS, or Vault), never in code or logs |
| Code isolation | Git worktree isolation per agent with restricted file system access |
| Audit trail | Every agent action logged with full provenance, timestamp, and model used |
| Sandbox execution | Generated code runs in Docker containers with resource limits and network isolation |
| Secrets scanning | Pre-commit hooks + Gitleaks integration + runtime secret detection |
| Network isolation | Optional air-gapped mode with self-hosted LLMs and no external network access |
| RBAC | Role-based access control for multi-user deployments |
| Encryption at rest | All stored credentials, API keys, and sensitive configuration encrypted at rest |
| Encryption in transit | TLS 1.3 for all network communication between agents, dashboard, and external services |
| Compliance | Support for GDPR, HIPAA, SOC2, and PCI-DSS compliance requirements through self-hosted LLMs and data residency controls |

CodeBot itself implements JWT-based authentication with RS256 signing. API keys use HMAC-SHA256 with key rotation. Sessions expire after 1 hour with refresh token rotation. Multi-factor authentication (TOTP) available for admin accounts. RBAC enforces admin/user/viewer roles. All auth events are audit-logged.

### 14.4 Scalability

| Dimension | Approach |
|---|---|
| Project size | Support projects up to 2000+ files across multiple repositories |
| Agent parallelism | Horizontal scaling via task queue (Redis, RabbitMQ) |
| LLM throughput | Connection pooling, rate limit management, multi-provider load balancing, self-hosted model scaling |
| Context window | Tiered context management with automatic chunking and summarization to stay within model limits |
| Multi-repo scaling | Support projects spanning 10+ repositories with cross-repo dependency resolution |
| Concurrent users | Support multiple concurrent users collaborating on the same project |
| Template library | Support hundreds of templates with lazy loading and caching |

### 14.5 Extensibility

| Dimension | Approach |
|---|---|
| Custom agents | Plugin architecture for adding custom agent types |
| Custom skills | Skill Creator Agent produces reusable skills consumable by any agent |
| Custom hooks | Hooks Creator Agent enables pipeline customization at any lifecycle stage |
| Custom tools | Tools Creator Agent builds MCP-compatible tools that extend agent capabilities |
| Custom templates | Users can contribute and share custom UI/UX templates |
| Custom model providers | Plugin interface for adding new LLM providers beyond built-in support |
| Custom deployment targets | Plugin interface for adding new cloud providers and deployment platforms |

### 14.6 Observability

| Signal | Technology | Purpose |
|---|---|---|
| Metrics | Prometheus + Grafana | Agent throughput, token usage, cost, latency, error rates |
| Logs | Structured JSON → stdout | Agent actions, LLM calls, tool invocations |
| Traces | OpenTelemetry → Jaeger | End-to-end request tracing across agents |
| Events | Event bus + WebSocket | Real-time pipeline state to dashboard |
| Alerts | Prometheus Alertmanager | Budget exhaustion, agent failures, pipeline stalls |
| Dashboards | Grafana | Pipeline health, cost tracking, agent performance |

### 14.7 Data Retention Policy

| Data Type | Retention | Cleanup |
|---|---|---|
| Project data | Indefinite (user-controlled) | Manual delete |
| Agent execution logs | 90 days | Auto-purge |
| LLM request/response | 30 days | Auto-purge |
| Event bus messages | 7 days | Auto-purge |
| Pipeline checkpoints | Until project archived | Cascade delete |
| Build artifacts | 30 days after project completion | Auto-purge |
| Security scan results | 1 year | Auto-archive |

---

## 15. Competitive Landscape

| Product | Type | Differentiator | CodeBot Advantage |
|---|---|---|---|
| **Devin (Cognition)** | Autonomous AI developer | Full autonomy, browser + terminal | Open-source, multi-LLM, 30 agents, full SDLC |
| **GitHub Copilot Workspace** | AI-assisted development | GitHub-native, PR workflow | Broader lifecycle, security pipeline, deployment |
| **Cursor** | AI-first IDE | Tight editor integration | No IDE required, autonomous end-to-end |
| **Bolt.new / Lovable** | AI app generators | Fast prototyping, browser-based | Production-grade, testing, security, deployment |
| **Cline / Roo Code** | VS Code AI agents | IDE extensions, local execution | Platform-agnostic, graph orchestration, multi-agent |
| **Windsurf (Codeium)** | AI IDE | IDE with AI flows | Autonomous pipeline, not IDE-dependent |
| **AutoGen / CrewAI** | Multi-agent frameworks | Generic agent orchestration | SDLC-specific, production pipeline, not framework |
| **Automaker** | Kanban + Claude Agent SDK | Tight Claude integration | Multi-LLM, full pipeline, 30 agent types |

CodeBot's unique position: Open-source, multi-LLM, graph-centric, full-lifecycle autonomous development platform with 30 specialized agents, integrated security/quality gates, multi-platform support, and extensible agent ecosystem.

---

## 16. Success Metrics

| Metric | Definition | Target |
|---|---|---|
| **End-to-end completion rate** | % of PRDs that result in a deployable application with passing test suite | > 75% |
| **Code quality score** | SonarQube quality gate pass rate | > 90% |
| **Security scan pass rate** | % of generated code with zero critical/high vulnerabilities | > 95% |
| **Test coverage** | Average line coverage of generated tests | > 80% |
| **Time-to-working-app** | Time from PRD submission to first passing build | < 30 minutes for simple apps, < 2 hours for complex apps |
| **Time-to-deployed-app** | Time from PRD submission to live cloud deployment | < 45 minutes for simple apps, < 3 hours for complex apps |
| **Fix loop convergence** | Average iterations to resolve test failures | < 3 iterations |
| **User satisfaction** | Post-generation user rating | > 4.2/5.0 |
| **Cross-platform consistency** | UI/UX consistency score between web and mobile versions | > 85% |
| **Accessibility compliance** | WCAG 2.1 AA pass rate for generated applications | > 95% |
| **i18n readiness** | % of user-facing strings properly externalized | > 99% |
| **Deployment success rate** | % of automated deployments that succeed without manual intervention | > 90% |
| **Collaboration effectiveness** | Reduction in merge conflicts when humans and agents work simultaneously | > 80% fewer conflicts |
| **Self-hosted LLM performance** | Quality parity with cloud models for supported task types | > 85% quality parity |
| **Template adoption** | % of users who select and successfully use a UI/UX template | > 60% |
| **Brownfield analysis accuracy** | % of correctly identified technical debt items and modernization opportunities | > 80% |
| **Multi-repo coordination** | % of cross-repo changes that are correctly coordinated without breaking dependencies | > 90% |
| **Agent skill reuse** | % of implementation tasks that leverage previously created skills | > 40% after 10 projects |

---

## 17. Technical Constraints & Technology Stack

### 17.1 Core Runtime Requirements

| # | Requirement | Version | Purpose |
|---|---|---|---|
| 1 | Python 3.12+ | Primary runtime | Orchestration layer, agent framework, backend API |
| 2 | Node.js 22+ | Secondary runtime | Web dashboard, CLI agent integrations, real-time collaboration |
| 3 | Docker | Latest stable | Sandbox execution, infrastructure agent, dev environments |
| 4 | Git 2.40+ | Required | Worktree management, multi-repo support |
| 5 | Minimum 16GB RAM | (32GB for self-hosted LLMs) | Running multiple agents concurrently |
| 6 | GPU (optional) | NVIDIA CUDA 12+, Apple Metal, AMD ROCm | Self-hosted LLM inference |

### 17.2 Open-Source Technology Stack

CodeBot maximizes reuse of proven open-source tools to reduce custom development effort while maintaining full control through self-hosting.

#### Agent Orchestration Layer

| Component | Technology | Stars | License | Purpose |
|---|---|---|---|---|
| Agent Graph Engine | LangGraph | 24.6K | MIT | DAG-based multi-agent orchestration with checkpointing |
| Durable Execution | Temporal | 18.9K | MIT | Workflow durability, retry, distributed execution |
| LLM Gateway | LiteLLM Proxy | 39.2K | MIT | Unified API for 100+ LLM providers with cost tracking |
| Smart Routing | RouteLLM | — | Apache-2.0 | Cost-quality model routing optimization |
| MCP Framework | FastMCP 2.0 | 21.9K | Apache-2.0 | MCP server/client for agent tool integration |
| Event Bus | NATS + JetStream | 19.4K | Apache-2.0 | Sub-ms inter-agent messaging with durable delivery |
| Task Queue | Taskiq | 2K | MIT | Async-native Python task distribution |

#### Context & Memory Layer

| Component | Technology | Stars | License | Purpose |
|---|---|---|---|---|
| Vector Database | LanceDB (dev) / Qdrant (prod) | 10K / 29.6K | Apache-2.0 | Hybrid search for code and episodic memory |
| RAG Framework | LlamaIndex | 47.7K | MIT | Code-aware retrieval with 150+ data connectors |
| Context Store | SQLite + DuckDB | — / 36.7K | Public Domain / MIT | L0/L1 relational context, L2 analytical queries |
| Code Parsing | Tree-sitter | 24.2K | MIT | Multi-language AST parsing (100+ grammars) |
| Code Search | ast-grep | 12.9K | MIT | AST-aware structural search and rewrite |

#### Frontend & Dashboard Layer

| Component | Technology | Stars | License | Purpose |
|---|---|---|---|---|
| Admin Framework | Refine | 34.2K | MIT | Headless React admin with real-time support |
| UI Components | Shadcn/ui + Tremor | 110K / 16.5K | MIT / Apache-2.0 | Components + data visualization charts |
| Pipeline Graph | React Flow + ELKjs | 35.6K / 2.4K | MIT / EPL-2.0 | Interactive DAG pipeline visualization |
| Code Editor | Monaco Editor | 45.8K | MIT | Syntax highlighting, diff view, LSP support |
| Terminal | xterm.js | 19.5K | MIT | Browser-based terminal emulation |
| Real-time | Socket.IO | 62.9K | MIT | WebSocket with rooms, broadcasting, auto-reconnect |
| CRDT Collaboration | Yjs | 21.4K | MIT | Real-time collaborative editing |

#### Testing & Quality Layer

| Component | Technology | Stars | License | Purpose |
|---|---|---|---|---|
| E2E Testing | Playwright | 84.4K | Apache-2.0 | Cross-browser testing with multi-language bindings |
| Unit Testing (JS/TS) | Vitest | 16.2K | MIT | Vite-native with browser mode |
| Unit Testing (Python) | pytest | 13.8K | MIT | Fixture system, rich plugin ecosystem |
| Mutation Testing | Stryker | 2.8K | Apache-2.0 | Test suite quality verification |
| Load Testing | k6 | 29.9K | AGPL-3.0 | Developer-centric performance testing |
| Accessibility | axe-core | 6.9K | MPL-2.0 | WCAG 2.2 automated compliance |
| Contract Testing | Pact | — | MIT | Consumer-driven microservice contracts |
| Integration Testing | Testcontainers | 9K+ | MIT | Throwaway Docker containers for tests |
| API Mocking | Prism | 4.9K | Apache-2.0 | OpenAPI-driven mock servers |

#### Security & Compliance Layer

| Component | Technology | Stars | License | Purpose |
|---|---|---|---|---|
| SAST | Semgrep + Bandit | 14.5K / 7.9K | LGPL-2.1 / Apache-2.0 | Multi-language + Python-specific static analysis |
| SCA / SBOM | Trivy + Syft + Grype | 33.2K / 8.4K / 11.7K | Apache-2.0 | Container, dependency scanning, SBOM generation |
| Secret Detection | Gitleaks | 24.4K | MIT | Pre-commit and CI secret scanning |
| DAST | OWASP ZAP | 14.8K | Apache-2.0 | Dynamic application security testing |
| License Compliance | ORT + ScanCode | 1.8K / 2.4K | Apache-2.0 | Automated open-source license compliance |
| Code Quality | SonarQube CE | 10.3K | LGPL-3.0 | Continuous code quality inspection |
| Formatting (JS/TS) | Biome | 24K | MIT | 10-100x faster linting + formatting |
| Formatting (Python) | Ruff | 46.2K | MIT | 10-100x faster Python linting + formatting |

#### DevOps & Infrastructure Layer

| Component | Technology | Stars | License | Purpose |
|---|---|---|---|---|
| IaC Generation | Pulumi | 23.1K | Apache-2.0 | Programmatic IaC in Python/TypeScript |
| IaC (HCL) | OpenTofu | ~23K | MPL-2.0 | Open-source Terraform alternative |
| CI/CD Generation | Dagger | 15.5K | Apache-2.0 | Pipelines as code in Python/TypeScript |
| Monorepo | Nx | 28.3K | MIT | Build system with caching and affected-only runs |
| Config Management | Ansible | 68.1K | GPL-3.0 | Agentless configuration management |

#### Observability & Operations Layer

| Component | Technology | Stars | License | Purpose |
|---|---|---|---|---|
| All-in-One APM | SigNoz | 25K | Open-source | Traces, metrics, logs with LLM observability |
| Metrics | Prometheus | 63.2K | Apache-2.0 | Pull-based metrics collection |
| Dashboards | Grafana | 67.6K | AGPL-3.0 | Visualization and alerting |
| Tracing | OpenTelemetry + Jaeger | 4.5K / 22.6K | Apache-2.0 | Distributed tracing across agents |
| Error Tracking | Sentry (self-hosted) | 9.2K | FSL→Apache-2.0 | Exception monitoring, session replay |
| LLM Observability | Langfuse | 23.3K | MIT | Per-agent cost tracking, prompt management |
| Prompt Testing | Promptfoo | 12.8K | MIT | A/B testing, red-teaming, CI/CD integration |

#### Utilities & Integration Layer

| Component | Technology | Stars | License | Purpose |
|---|---|---|---|---|
| Plugin System | pluggy | 1.5K | MIT | Hook-based plugin architecture (powers pytest) |
| Project Templates | Copier | 3K | MIT | Parameterized scaffolding with update/sync |
| Diagrams | Mermaid + D2 | 86.6K / 23.2K | MIT / MPL-2.0 | Text-to-diagram generation |
| API Docs | OpenAPI Generator | 25.9K | Apache-2.0 | SDK and doc generation from OpenAPI specs |
| DB Migrations | Alembic | 4K | MIT | SQLAlchemy-based schema migrations |
| Notifications | Apprise | 14.1K | BSD | 100+ notification channels, single library |
| Dependency Updates | Renovate | 20K | AGPL-3.0 | Automated dependency update PRs |
| Sandbox Execution | E2B (managed) / Nsjail (self-hosted) | 8.9K / 3K | Apache-2.0 | Isolated code execution environments |
| Live Preview | code-server | 76.7K | MIT | Full VS Code in browser for live preview |
| Git Operations | GitPython + simple-git + gh CLI | 5.1K / 3.8K / 43.1K | BSD/MIT | Programmatic git and GitHub automation |

### 17.3 Additional Requirements

| # | Requirement | Details |
|---|---|---|
| 1 | API keys for at least one LLM provider | OR a self-hosted model for fully offline operation |
| 2 | Xcode 16+ | Required for iOS development (macOS only) |
| 3 | Android Studio / Android SDK | Required for Android development |
| 4 | WebSocket support | Required for real-time collaboration features |
| 5 | PostgreSQL 16+ | Persistent storage of project state, agent history, metrics |
| 6 | Redis 7+ or compatible | Task queue, caching, real-time pub/sub |

---

## 18. Milestones

| Milestone | Deliverable | Dependencies | Target |
|---|---|---|---|
| **M1: Foundation** | Core orchestration engine, agent graph execution, context management, project state persistence | None | Month 1-2 |
| **M2: Core Agents** | First 14 agent types (Orchestrator through Doc Writer) with basic LLM integration | M1 | Month 2-3 |
| **M3: Brainstorming & Planning** | Brainstorming Agent, interactive brainstorming sessions, enhanced planning with tech stack and template selection | M2 | Month 3-4 |
| **M4: Multi-LLM** | OpenAI, Anthropic, Gemini, Mistral integration with intelligent model routing | M2 | Month 3-4 |
| **M5: Self-Hosted LLM** | Ollama, vLLM, LocalAI, LM Studio integration with hybrid routing and offline mode | M4 | Month 4-5 |
| **M6: CLI Agents** | Claude Code, Codex, Gemini CLI, Aider integration | M4 | Month 4-5 |
| **M7: Template & Stack System** | Template gallery, tech stack configurator, Template Agent, TechStack Builder Agent | M3 | Month 4-5 |
| **M8: Extended Agents** | Database Agent, API Gateway Agent, Performance Agent, Accessibility Agent, i18n Agent | M2 | Month 5-6 |
| **M9: Meta Agents** | Skill Creator, Hooks Creator, Tools Creator agents with extensibility framework | M2, M8 | Month 5-6 |
| **M10: GitHub & Integrations** | GitHub Agent, Integrations Agent with third-party service support | M2 | Month 5-6 |
| **M11: Review & Security** | Security scanning, code review, accessibility review, i18n review, quality gates | M2, M8 | Month 6-7 |
| **M12: Testing Loop** | Test generation, execution, debug/fix cycle, performance testing, visual regression | M2, M11 | Month 6-7 |
| **M13: Mobile Development** | Mobile Agent with iOS (Swift/SwiftUI), Android (Kotlin/Compose), React Native, Flutter support | M2, M7 | Month 7-8 |
| **M14: Multi-repo Support** | Multi-repository project support, cross-repo context, coordinated builds and deployments | M2, M10 | Month 7-8 |
| **M15: Cloud Deployment** | Deployment to AWS, GCP, Azure, Vercel, Railway, Netlify, Fly.io, DigitalOcean, DevOps Agent | M2, M10 | Month 8-9 |
| **M16: App Store Deployment** | iOS App Store and Google Play Store build, signing, and submission automation | M13, M15 | Month 9-10 |
| **M17: Real-time Collaboration** | Live collaborative editing, CRDT-based conflict resolution, presence awareness | M1 | Month 8-9 |
| **M18: Web Dashboard** | Full web UI with real-time agent monitoring, brainstorming board, deployment dashboard | M2, M17 | Month 9-10 |
| **M19: IDE Extensions** | VS Code, JetBrains, and Neovim extensions with agent integration | M18 | Month 10-11 |
| **M20: Brownfield Support** | Legacy codebase analysis, modernization planning, incremental refactoring, migration automation | M2, M14 | Month 10-11 |
| **M21: Inflight Support** | Existing codebase import, convention detection, knowledge extraction, seamless continuation | M2, M14 | Month 10-11 |
| **M22: Beta Release** | End-to-end pipeline with documentation, tutorials, and community onboarding | M1-M21 | Month 12 |
| **M23: Production Release** | Hardened, battle-tested release with enterprise features and SLA | M22 | Month 14 |

### 18.1 Delivery Tiers

| Tier | Features |
|---|---|
| **Core (Open Source)** | Foundation engine, 14 core agents, basic pipeline, SQLite, single-LLM, CLI |
| **Pro (Self-Hosted)** | All 30 agents, multi-LLM routing, self-hosted LLM, dashboard, deployment automation, real-time collaboration |
| **Enterprise (Managed)** | SaaS offering, multi-tenant, SSO/SAML, audit logs, SLA, dedicated support, compliance certifications |

### 18.2 Monetization Model

| Revenue Stream | Description |
|---|---|
| Open Source Core | Free forever, community-driven |
| Pro License | Annual license for self-hosted Pro features |
| Enterprise License | Per-seat annual license with SLA |
| Cloud Hosted | Usage-based pricing for managed cloud offering |
| Template Marketplace | Revenue share on premium templates |
| Support & Training | Professional services, onboarding, custom agent development |

### 18.3 Team & Resource Requirements

| Role | Count | Responsibility |
|---|---|---|
| Tech Lead / Architect | 1 | System architecture, agent design, code review |
| Backend Engineers | 2-3 | Core engine, agent framework, API, graph engine |
| Frontend Engineers | 1-2 | Dashboard, real-time UI, visualization |
| ML/AI Engineers | 1-2 | LLM integration, prompt engineering, model routing |
| DevOps Engineer | 1 | CI/CD, deployment automation, infrastructure |
| QA Engineer | 1 | Testing framework, quality assurance |
| Technical Writer | 0.5 | Documentation, tutorials, API docs |
| **Total** | **7-11** | |

---

## 19. Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| LLM rate limiting disrupts pipeline | High | High | Multi-provider fallback, self-hosted model fallback, request queuing, response caching, token budget management |
| Generated code has security vulnerabilities | Medium | Critical | Multi-layer security scanning (SAST, DAST, SCA), sandbox execution, human approval gates, Security Auditor agent |
| Agent hallucination produces incorrect code | High | High | Code review agent, test verification, architecture conformance checking, human-in-the-loop gates, multi-model verification |
| Context window overflow for large projects | Medium | High | Tiered context management, code chunking, summarization, cross-repo context partitioning |
| Inter-agent coordination failures | Medium | Medium | Checkpoint/resume, dead letter queue, orchestrator monitoring, automatic agent restart |
| Cost overrun from excessive LLM calls | Medium | Medium | Token budgets per agent, cost tracking dashboard, model routing optimization, self-hosted models for high-volume tasks |
| Self-hosted model quality insufficient | Medium | Medium | Hybrid routing (self-hosted for simple tasks, cloud for complex), quality threshold monitoring, automatic fallback to cloud |
| Real-time collaboration conflicts | Medium | Medium | CRDT-based conflict resolution, file-level locking for critical sections, human override capability |
| Cloud deployment failures | Medium | High | Multi-cloud fallback, infrastructure-as-code validation, dry-run deployments, automated rollback, health check verification |
| Mobile app store rejection | Medium | High | Platform guideline compliance checking, automated screenshot validation, pre-submission review agent |
| Multi-repo coordination failures | Medium | Medium | Dependency graph validation, cross-repo integration testing, atomic multi-repo commits, version pinning |
| Template incompatibility | Low | Medium | Template compatibility matrix, automated testing of template combinations, fallback to base components |
| Scope creep in brownfield projects | High | Medium | Incremental modernization planning, risk-bounded refactoring, automated compatibility testing |
| Privacy/compliance violations | Low | Critical | Self-hosted LLM option, data residency controls, audit logging, GDPR/HIPAA compliance tooling, no telemetry in offline mode |
| Agent skill/hook/tool conflicts | Low | Medium | Skill versioning, conflict detection, sandbox testing of new skills before deployment, rollback capability |
| Open source contribution quality | Medium | Medium | Contribution guidelines, automated PR review, CI/CD quality gates, community code review |
| Experiment loop runaway cost | Medium | Medium | Hard token/time budget per experiment, circuit breakers (N consecutive non-improvements), multi-metric regression guards, human review gate before merge |
| Autonomous optimization degrades codebase | Low | High | Multi-metric regression checks (improvement in one metric must not regress others), simplicity criterion enforcement, mandatory human review PR at end of Improve session |

---

## 20. Glossary

| Term | Definition |
|---|---|
| **Agent** | An autonomous LLM-powered worker with a specific role, tools, and skills |
| **Agent Graph** | Directed computation graph where nodes are agents and edges are dependencies |
| **Agent Graph Engine** | The runtime that executes the directed computation graph of agents |
| **Brainstorming Phase** | Initial interactive phase where the system explores ideas, alternatives, and trade-offs with the user before planning |
| **Brownfield** | An existing legacy project that needs modernization, refactoring, or migration |
| **Circuit Breaker** | Pattern that stops calling a failing service after repeated failures |
| **CLI Agent** | An external coding agent (Claude Code, Codex, Gemini CLI) invoked as a subprocess |
| **CRDT** | Conflict-free Replicated Data Type — data structure enabling real-time collaboration without coordination |
| **Episodic Memory** | CodeBot's built-in cross-session memory system — captures agent observations, decisions, and outcomes with semantic compression and progressive disclosure retrieval |
| **Context Tier** | Hierarchical context loading strategy (L0/L1/L2) inspired by OpenViking patterns |
| **Dead Letter Queue** | Storage for failed messages that could not be processed after max retries |
| **Design Token** | Atomic design decision (color, spacing, typography) that can be imported from design tools |
| **ExperimentLoop** | An autonomous optimization loop where an agent proposes a code change (hypothesis), applies it to an experiment branch, measures outcome against baseline metrics, and keeps or discards the change. Inspired by Karpathy's autoresearch framework |
| **Experiment Log** | TSV file tracking all experiment attempts: commit hash, hypothesis, metric before/after, keep/discard decision, diff size, duration |
| **Fix Loop** | Iterative debug-fix-test cycle until all tests pass |
| **Improve Mode** | Project type where CodeBot takes an existing codebase and autonomously runs ExperimentLoop to optimize specified quality metrics (performance, security, coverage, accessibility) within a time/token budget |
| **Greenfield** | A brand new project built from scratch with no existing codebase |
| **Hook** | A lifecycle callback that executes custom logic at a specific pipeline stage (pre-build, post-deploy, etc.) |
| **IaC** | Infrastructure as Code — managing infrastructure through declarative configuration files |
| **Inflight** | An existing project that is mid-development and needs continuation |
| **MCP** | Model Context Protocol — standard for tool integration with LLMs |
| **Live Preview** | Real-time browser-based preview of the running application inside its sandbox, with hot-reload and device emulation |
| **Model Router** | Component that selects optimal LLM for each task based on type, complexity, privacy, cost, and latency |
| **Multi-repo** | Project architecture spanning multiple Git repositories |
| **Project Manager Agent** | Agent responsible for progress tracking, status reports, and blocker identification |
| **Quality Gate** | A checkpoint that blocks pipeline progression unless quality criteria are met |
| **Self-hosted LLM** | Language model running on local or private infrastructure rather than cloud API |
| **Skill** | A reusable capability created by the Skill Creator Agent that other agents can invoke |
| **SAST** | Static Application Security Testing |
| **DAST** | Dynamic Application Security Testing |
| **SCA** | Software Composition Analysis |
| **Tech Stack** | The combination of programming languages, frameworks, databases, and tools used in a project |
| **Template** | A pre-built UI/UX component library or design system that can be applied to generated projects |
| **Tool** | A custom MCP-compatible integration created by the Tools Creator Agent |
| **Vibe Graphing** | Natural language to workflow graph compilation (MASFactory concept) |
| **WCAG** | Web Content Accessibility Guidelines — international standard for web accessibility |
| **Worktree** | Git worktree providing isolated working directory per agent |
| **Sandbox** | Isolated containerized execution environment for running generated code — supports multi-language runtimes, filesystem access, network policies, and live preview |
| **i18n** | Internationalization — designing software to support multiple languages and locales |
| **L10n** | Localization — adapting software for a specific language, region, or culture |
