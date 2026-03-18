# CodeBot — Data Models & Configuration Design

**Version:** 2.4
**Date:** 2026-03-18

---

## 1. Core Data Models (Original)

### 1.1 Project

```
┌──────────────────────────────────────────┐
│                Project                   │
├──────────────────────────────────────────┤
│ id: UUID (PK)                            │
│ user_id: UUID (FK → User)                │
│ name: String                             │
│ description: Text                        │
│ status: ProjectStatus                    │
│ project_type: ProjectType                │
│ prd_content: Text                        │
│ prd_format: Enum(markdown,json,yaml)     │
│ tech_stack: JSON                         │
│ tech_stack_config_id: UUID (FK, nullable)│
│ template_id: UUID (FK, nullable)         │
│ repository_path: String                  │
│ repository_url: String (nullable)        │
│ config: JSON                             │
│ created_at: DateTime                     │
│ updated_at: DateTime                     │
│ completed_at: DateTime (nullable)        │
└──────────────────────────────────────────┘

ProjectStatus: CREATED | PLANNING | BRAINSTORMING | RESEARCHING | ARCHITECTING |
               DESIGNING | IMPLEMENTING | REVIEWING | TESTING | DEBUGGING |
               DOCUMENTING | DEPLOYING | DELIVERING | COMPLETED | FAILED |
               PAUSED | CANCELLED

ProjectType: GREENFIELD | INFLIGHT | BROWNFIELD | IMPROVE
```

### 1.2 Pipeline

```
┌──────────────────────────────────────────┐
│                Pipeline                  │
├──────────────────────────────────────────┤
│ id: UUID (PK)                            │
│ project_id: UUID (FK → Project)          │
│ status: PipelineStatus                   │
│ current_phase: String                    │
│ graph_definition: JSON                   │
│ checkpoint_data: JSON (nullable)         │
│ started_at: DateTime                     │
│ completed_at: DateTime (nullable)        │
│ total_tokens_used: Integer               │
│ total_cost_usd: Decimal                  │
│ error_message: Text (nullable)           │
└──────────────────────────────────────────┘

PipelineStatus: PENDING | RUNNING | PAUSED | COMPLETED | FAILED | CANCELLED
```

### 1.3 PipelinePhase

```
┌──────────────────────────────────────────┐
│            PipelinePhase                 │
├──────────────────────────────────────────┤
│ id: UUID (PK)                            │
│ pipeline_id: UUID (FK → Pipeline)        │
│ name: String                             │
│ phase_type: PhaseType                    │
│ status: PhaseStatus                      │
│ order: Integer                           │
│ requires_approval: Boolean               │
│ approved_by: String (nullable)           │
│ started_at: DateTime (nullable)          │
│ completed_at: DateTime (nullable)        │
│ input_data: JSON                         │
│ output_data: JSON (nullable)             │
│ error_message: Text (nullable)           │
└──────────────────────────────────────────┘

PhaseType: BRAINSTORMING | TECH_STACK_SELECTION | TEMPLATE_SELECTION | PLANNING |
           RESEARCH | ARCHITECTURE | DESIGN | IMPLEMENTATION | REVIEW | TESTING |
           DEBUG_FIX | DOCUMENTATION | DEPLOYMENT | DELIVERY

PhaseStatus: PENDING | WAITING_APPROVAL | RUNNING | COMPLETED | FAILED | SKIPPED
```

### 1.4 Task

```
┌──────────────────────────────────────────┐
│                 Task                     │
├──────────────────────────────────────────┤
│ id: UUID (PK)                            │
│ project_id: UUID (FK → Project)          │
│ phase_id: UUID (FK → PipelinePhase)      │
│ parent_task_id: UUID (nullable, FK)      │
│ title: String                            │
│ description: Text                        │
│ status: TaskStatus                       │
│ priority: Integer                        │
│ assigned_agent_type: String              │
│ dependencies: JSON (list of UUIDs)       │
│ input_context: JSON                      │
│ output_artifacts: JSON (nullable)        │
│ created_at: DateTime                     │
│ started_at: DateTime (nullable)          │
│ completed_at: DateTime (nullable)        │
│ error_message: Text (nullable)           │
└──────────────────────────────────────────┘

TaskStatus: PENDING | BLOCKED | IN_PROGRESS | COMPLETED | FAILED | CANCELLED
```

### 1.5 Agent

```
┌──────────────────────────────────────────┐
│                Agent                     │
├──────────────────────────────────────────┤
│ id: UUID (PK)                            │
│ project_id: UUID (FK → Project)          │
│ agent_type: AgentType                    │
│ status: AgentStatus                      │
│ llm_provider: String                     │
│ llm_model: String                        │
│ worktree_path: String (nullable)         │
│ cli_agent_type: String (nullable)        │
│ system_prompt_hash: String               │
│ tokens_used: Integer                     │
│ cost_usd: Decimal                        │
│ started_at: DateTime                     │
│ completed_at: DateTime (nullable)        │
│ error_count: Integer                     │
└──────────────────────────────────────────┘

AgentType: ORCHESTRATOR | PLANNER | RESEARCHER | ARCHITECT | DESIGNER |
           FRONTEND_DEV | BACKEND_DEV | MIDDLEWARE_DEV | INFRA_ENGINEER |
           SECURITY_AUDITOR | CODE_REVIEWER | TESTER | DEBUGGER | DOC_WRITER |
           BRAINSTORM_FACILITATOR | TECH_STACK_ADVISOR | TEMPLATE_CURATOR |
           DEPLOYER | COLLABORATION_MANAGER | MOBILE_DEV | PERFORMANCE_TESTER |
           ACCESSIBILITY_AUDITOR | GITHUB_INTEGRATOR | SKILL_MANAGER |
           HOOK_MANAGER | TOOL_BUILDER | INTEGRATION_ADAPTER |
           I18N_SPECIALIST | API_DESIGNER | PROJECT_MANAGER

AgentStatus: IDLE | INITIALIZING | RUNNING | WAITING | COMPLETED | FAILED | TERMINATED
```

### 1.6 AgentExecution

```
┌──────────────────────────────────────────┐
│           AgentExecution                 │
├──────────────────────────────────────────┤
│ id: UUID (PK)                            │
│ agent_id: UUID (FK → Agent)              │
│ task_id: UUID (FK → Task)                │
│ llm_provider: String                     │
│ llm_model: String                        │
│ input_tokens: Integer                    │
│ output_tokens: Integer                   │
│ total_tokens: Integer                    │
│ cost_usd: Decimal                        │
│ duration_ms: Integer                     │
│ status: ExecutionStatus                  │
│ input_messages: JSON                     │
│ output_messages: JSON                    │
│ tool_calls: JSON                         │
│ error_message: Text (nullable)           │
│ created_at: DateTime                     │
└──────────────────────────────────────────┘

ExecutionStatus: SUCCESS | FAILURE | TIMEOUT | RATE_LIMITED | CANCELLED
```

### 1.7 CodeArtifact

```
┌──────────────────────────────────────────┐
│            CodeArtifact                  │
├──────────────────────────────────────────┤
│ id: UUID (PK)                            │
│ project_id: UUID (FK → Project)          │
│ agent_id: UUID (FK → Agent)              │
│ file_path: String                        │
│ file_type: String                        │
│ language: String                         │
│ content_hash: String                     │
│ line_count: Integer                      │
│ operation: Enum(CREATE,MODIFY,DELETE)     │
│ git_commit_sha: String                   │
│ git_branch: String                       │
│ created_at: DateTime                     │
└──────────────────────────────────────────┘
```

### 1.8 TestResult

```
┌──────────────────────────────────────────┐
│             TestResult                   │
├──────────────────────────────────────────┤
│ id: UUID (PK)                            │
│ project_id: UUID (FK → Project)          │
│ test_suite: String                       │
│ test_name: String                        │
│ test_file: String                        │
│ status: TestStatus                       │
│ duration_ms: Integer                     │
│ error_message: Text (nullable)           │
│ stack_trace: Text (nullable)             │
│ framework: String                        │
│ coverage_percent: Decimal (nullable)     │
│ run_number: Integer                      │
│ created_at: DateTime                     │
└──────────────────────────────────────────┘

TestStatus: PASSED | FAILED | SKIPPED | ERROR
```

### 1.9 ExperimentLog

Tracks individual experiments within an ExperimentLoop (Debug, Performance, Security, Improve mode). Inspired by autoresearch's `results.tsv` pattern — each row captures a hypothesis, its measured outcome, and the keep/discard decision.

```
┌──────────────────────────────────────────┐
│           ExperimentLog                  │
├──────────────────────────────────────────┤
│ id: UUID (PK)                            │
│ project_id: UUID (FK → Project)          │
│ pipeline_id: UUID (FK → Pipeline)        │
│ stage: String                            │  # e.g., "S8_DEBUG", "S6_PERF", "IMPROVE"
│ experiment_number: Integer               │  # sequential within the loop session
│ hypothesis: Text                         │  # natural language description of proposed change
│ git_branch: String                       │  # experiment branch name (e.g., "experiment/7")
│ git_commit_sha: String                   │  # commit hash of the applied change
│ metric_name: String                      │  # e.g., "test_pass_rate", "lighthouse_score"
│ metric_before: Decimal                   │  # baseline measurement
│ metric_after: Decimal                    │  # post-experiment measurement
│ metric_delta: Decimal                    │  # metric_after - metric_before
│ regression_checks: JSONB                 │  # {metric_name: {before, after, passed}} for all secondary metrics
│ status: ExperimentStatus                 │  # KEEP, DISCARD, CRASH, TIMEOUT
│ decision_reason: Text                    │  # why the experiment was kept or discarded
│ diff_lines_added: Integer                │  # lines of code added
│ diff_lines_removed: Integer              │  # lines of code removed
│ complexity_delta: Integer (nullable)     │  # change in cyclomatic complexity
│ duration_seconds: Integer                │  # wall-clock time for this experiment
│ token_cost: Integer                      │  # LLM tokens consumed by this experiment
│ created_at: DateTime                     │
└──────────────────────────────────────────┘

ExperimentStatus: KEEP | DISCARD | CRASH | TIMEOUT | REGRESSION
```

### 1.10 SecurityFinding

```
┌──────────────────────────────────────────┐
│          SecurityFinding                 │
├──────────────────────────────────────────┤
│ id: UUID (PK)                            │
│ project_id: UUID (FK → Project)          │
│ scanner: String                          │
│ finding_type: FindingType                │
│ severity: Severity                       │
│ title: String                            │
│ description: Text                        │
│ file_path: String (nullable)             │
│ line_number: Integer (nullable)          │
│ code_snippet: Text (nullable)            │
│ cwe_id: String (nullable)               │
│ cve_id: String (nullable)               │
│ recommendation: Text                     │
│ status: FindingStatus                    │
│ fixed_by_agent_id: UUID (nullable)       │
│ fixed_at: DateTime (nullable)            │
│ created_at: DateTime                     │
└──────────────────────────────────────────┘

FindingType: VULNERABILITY | SECRET | LICENSE_VIOLATION | CODE_SMELL |
             DEPENDENCY_RISK | CONFIG_ISSUE

Severity: CRITICAL | HIGH | MEDIUM | LOW | INFO

FindingStatus: OPEN | IN_PROGRESS | FIXED | ACCEPTED_RISK | FALSE_POSITIVE
```

### 1.11 ReviewComment

```
┌──────────────────────────────────────────┐
│           ReviewComment                  │
├──────────────────────────────────────────┤
│ id: UUID (PK)                            │
│ project_id: UUID (FK → Project)          │
│ agent_id: UUID (FK → Agent)              │
│ file_path: String                        │
│ line_number: Integer                     │
│ comment_type: CommentType                │
│ severity: Severity                       │
│ content: Text                            │
│ suggestion: Text (nullable)              │
│ status: CommentStatus                    │
│ resolved_by_agent_id: UUID (nullable)    │
│ created_at: DateTime                     │
│ resolved_at: DateTime (nullable)         │
└──────────────────────────────────────────┘

CommentType: BUG | STYLE | PERFORMANCE | SECURITY | ARCHITECTURE | SUGGESTION
CommentStatus: OPEN | RESOLVED | DISMISSED
```

### 1.12 Event

```
┌──────────────────────────────────────────┐
│                Event                     │
├──────────────────────────────────────────┤
│ id: UUID (PK)                            │
│ project_id: UUID (FK → Project)          │
│ event_type: EventType                    │
│ source_agent_id: UUID (nullable)         │
│ target_agent_id: UUID (nullable)         │
│ payload: JSON                            │
│ timestamp: DateTime                      │
└──────────────────────────────────────────┘

EventType: AGENT_STARTED | AGENT_COMPLETED | AGENT_FAILED |
           TASK_CREATED | TASK_COMPLETED | TASK_FAILED |
           PHASE_STARTED | PHASE_COMPLETED |
           PIPELINE_STARTED | PIPELINE_COMPLETED |
           BRAINSTORM_MESSAGE | BRAINSTORM_FINALIZED |
           DEPLOYMENT_STARTED | DEPLOYMENT_COMPLETED | DEPLOYMENT_FAILED |
           DEPLOYMENT_ROLLED_BACK |
           COLLABORATION_JOINED | COLLABORATION_LEFT |
           COLLABORATION_CONFLICT | COLLABORATION_RESOLVED |
           GITHUB_PUSH | GITHUB_PR_CREATED | GITHUB_PR_MERGED |
           GITHUB_ISSUE_CREATED | GITHUB_ISSUE_CLOSED |
           GITHUB_WEBHOOK_RECEIVED |
           SKILL_CREATED | SKILL_EXECUTED |
           HOOK_TRIGGERED | HOOK_COMPLETED |
           TOOL_REGISTERED | TOOL_INVOKED |
           PERFORMANCE_REPORT_GENERATED |
           ACCESSIBILITY_REPORT_GENERATED
```

### 1.13 Checkpoint

```
┌──────────────────────────────────────────┐
│             Checkpoint                   │
├──────────────────────────────────────────┤
│ id: UUID (PK)                            │
│ pipeline_id: UUID (FK → Pipeline)        │
│ phase_name: String                       │
│ state_data: JSON                         │
│ git_commit_sha: String                   │
│ created_at: DateTime                     │
└──────────────────────────────────────────┘
```

---

## 2. Extended Data Models (New)

### 2.1 User

```
┌──────────────────────────────────────────┐
│                 User                     │
├──────────────────────────────────────────┤
│ id: UUID (PK)                            │
│ email: String (unique)                   │
│ password_hash: String                    │
│ name: String                             │
│ role: UserRole                           │
│ organization: String (nullable)          │
│ mfa_secret: String (nullable, encrypted) │
│ mfa_enabled: Boolean (default: false)    │
│ preferences: JSON (nullable)             │
│ created_at: DateTime                     │
│ updated_at: DateTime                     │
│ last_login_at: DateTime (nullable)       │
└──────────────────────────────────────────┘

UserRole: ADMIN | USER | VIEWER
```

### 2.2 ApiKey

```
┌──────────────────────────────────────────┐
│               ApiKey                     │
├──────────────────────────────────────────┤
│ id: UUID (PK)                            │
│ user_id: UUID (FK → User)                │
│ name: String                             │
│ key_hash: String                         │
│ key_prefix: String                       │
│ last_used_at: DateTime (nullable)        │
│ expires_at: DateTime (nullable)          │
│ created_at: DateTime                     │
└──────────────────────────────────────────┘
```

### 2.3 AuditLog

```
┌──────────────────────────────────────────┐
│              AuditLog                    │
├──────────────────────────────────────────┤
│ id: UUID (PK)                            │
│ user_id: UUID (FK → User, nullable)      │
│ action: String                           │
│ resource_type: String                    │
│ resource_id: String                      │
│ details: JSON (nullable)                 │
│ ip_address: String (nullable)            │
│ user_agent: String (nullable)            │
│ created_at: DateTime                     │
└──────────────────────────────────────────┘
```

### 2.4 ProjectManagerReport

```
┌──────────────────────────────────────────┐
│        ProjectManagerReport              │
├──────────────────────────────────────────┤
│ id: UUID (PK)                            │
│ project_id: UUID (FK → Project)          │
│ pipeline_id: UUID (FK → Pipeline)        │
│ report_type: ReportType                  │
│ summary: Text                            │
│ blockers: JSON (list)                    │
│ progress_percent: Decimal                │
│ estimated_completion: DateTime (nullable)│
│ recommendations: JSON (list)             │
│ created_at: DateTime                     │
└──────────────────────────────────────────┘

ReportType: STATUS_UPDATE | BLOCKER_ALERT | COMPLETION_SUMMARY | TIMELINE_REVISION
```

### 2.5 DataRetentionPolicy

```
┌──────────────────────────────────────────┐
│        DataRetentionPolicy               │
├──────────────────────────────────────────┤
│ id: UUID (PK)                            │
│ data_type: String                        │
│ retention_days: Integer                  │
│ cleanup_strategy: CleanupStrategy        │
│ last_cleanup_at: DateTime (nullable)     │
│ next_cleanup_at: DateTime                │
│ enabled: Boolean (default: true)         │
│ created_at: DateTime                     │
└──────────────────────────────────────────┘

CleanupStrategy: AUTO_PURGE | AUTO_ARCHIVE | MANUAL | CASCADE_DELETE
```

### 2.7 BrainstormSession

```
┌──────────────────────────────────────────┐
│          BrainstormSession               │
├──────────────────────────────────────────┤
│ id: UUID (PK)                            │
│ project_id: UUID (FK → Project)          │
│ status: BrainstormStatus                 │
│ messages: JSON (list)                    │
│   ├─ role: String (user/agent/system)    │
│   ├─ content: Text                       │
│   └─ timestamp: DateTime                 │
│ refined_requirements: Text (nullable)    │
│ alternatives_explored: JSON (nullable)   │
│ risks_identified: JSON (nullable)        │
│ created_at: DateTime                     │
│ updated_at: DateTime                     │
└──────────────────────────────────────────┘

BrainstormStatus: ACTIVE | PAUSED | FINALIZED
```

### 2.8 Template

```
┌──────────────────────────────────────────┐
│              Template                    │
├──────────────────────────────────────────┤
│ id: UUID (PK)                            │
│ name: String                             │
│ description: Text                        │
│ category: TemplateCategory               │
│ framework: TemplateFramework             │
│ design_system: DesignSystem              │
│ preview_url: String (nullable)           │
│ files: JSON (template file tree)         │
│ tags: JSON (list of strings)             │
│ popularity: Integer (default: 0)         │
│ created_at: DateTime                     │
└──────────────────────────────────────────┘

TemplateCategory: UI | SCAFFOLD | MOBILE

TemplateFramework: REACT | VUE | NEXTJS | FLUTTER | REACT_NATIVE

DesignSystem: MATERIAL | SHADCN | ANTD | TAILWIND | CUSTOM
```

### 2.9 TechStackConfig

```
┌──────────────────────────────────────────┐
│          TechStackConfig                 │
├──────────────────────────────────────────┤
│ id: UUID (PK)                            │
│ project_id: UUID (FK → Project)          │
│ name: String                             │
│ language: TechLanguage                   │
│ frontend_framework: String (nullable)    │
│ backend_framework: String (nullable)     │
│ database: String (nullable)              │
│ hosting_provider: String (nullable)      │
│ ci_cd: String (nullable)                 │
│ additional_tools: JSON (nullable)        │
│ package_manager: String (nullable)       │
│ recommended_by: Enum(ai,user)            │
│ confidence_score: Decimal (nullable)     │
│ created_at: DateTime                     │
└──────────────────────────────────────────┘

TechLanguage: PYTHON | TYPESCRIPT | JAVA | GO | RUST | DART | SWIFT | KOTLIN
```

### 2.10 Deployment

```
┌──────────────────────────────────────────┐
│             Deployment                   │
├──────────────────────────────────────────┤
│ id: UUID (PK)                            │
│ project_id: UUID (FK → Project)          │
│ pipeline_id: UUID (FK → Pipeline)        │
│ provider: DeploymentProvider             │
│ environment: DeploymentEnvironment       │
│ status: DeploymentStatus                 │
│ url: String (nullable)                   │
│ config: JSON                             │
│ logs: Text (nullable)                    │
│ created_at: DateTime                     │
│ completed_at: DateTime (nullable)        │
│ rolled_back_at: DateTime (nullable)      │
└──────────────────────────────────────────┘

DeploymentProvider: AWS | GCP | AZURE | VERCEL | RAILWAY | NETLIFY

DeploymentEnvironment: STAGING | PRODUCTION

DeploymentStatus: PENDING | DEPLOYING | DEPLOYED | FAILED | ROLLED_BACK
```

### 2.11 CollaborationSession

```
┌──────────────────────────────────────────┐
│        CollaborationSession              │
├──────────────────────────────────────────┤
│ id: UUID (PK)                            │
│ project_id: UUID (FK → Project)          │
│ participants: JSON (list)                │
│   ├─ id: String                          │
│   ├─ type: Enum(user,agent)              │
│   ├─ name: String                        │
│   └─ cursor_position: JSON (nullable)    │
│       ├─ file: String                    │
│       ├─ line: Integer                   │
│       └─ column: Integer                 │
│ active_files: JSON (list of strings)     │
│ conflict_resolution_strategy: ConflictStrategy │
│ created_at: DateTime                     │
└──────────────────────────────────────────┘

ConflictStrategy: LAST_WRITE_WINS | MERGE | MANUAL
```

### 2.12 Skill

```
┌──────────────────────────────────────────┐
│               Skill                      │
├──────────────────────────────────────────┤
│ id: UUID (PK)                            │
│ name: String                             │
│ description: Text                        │
│ version: String                          │
│ created_by_agent: AgentType              │
│ target_agents: JSON (list of AgentType)  │
│ code: Text                               │
│ dependencies: JSON (nullable)            │
│ usage_count: Integer (default: 0)        │
│ success_rate: Decimal (default: 0.0)     │
│ created_at: DateTime                     │
│ updated_at: DateTime                     │
└──────────────────────────────────────────┘
```

### 2.13 Hook

```
┌──────────────────────────────────────────┐
│               Hook                       │
├──────────────────────────────────────────┤
│ id: UUID (PK)                            │
│ name: String                             │
│ description: Text                        │
│ event_type: String                       │
│ phase: HookPhase                         │
│ target_phase: HookTargetPhase            │
│ handler_code: Text                       │
│ configuration: JSON (nullable)           │
│ enabled: Boolean (default: true)         │
│ priority: Integer (default: 0)           │
│ created_at: DateTime                     │
└──────────────────────────────────────────┘

HookPhase: PRE | POST

HookTargetPhase: BUILD | TEST | DEPLOY | REVIEW
```

### 2.14 Tool

```
┌──────────────────────────────────────────┐
│               Tool                       │
├──────────────────────────────────────────┤
│ id: UUID (PK)                            │
│ name: String                             │
│ description: Text                        │
│ version: String                          │
│ mcp_server_config: JSON                  │
│ input_schema: JSON                       │
│ output_schema: JSON                      │
│ created_by_agent: AgentType (nullable)   │
│ created_at: DateTime                     │
└──────────────────────────────────────────┘
```

### 2.15 Integration

```
┌──────────────────────────────────────────┐
│            Integration                   │
├──────────────────────────────────────────┤
│ id: UUID (PK)                            │
│ project_id: UUID (FK → Project)          │
│ name: String                             │
│ provider: String                         │
│ category: IntegrationCategory            │
│ configuration: JSON (encrypted)          │
│ status: IntegrationStatus                │
│ created_at: DateTime                     │
└──────────────────────────────────────────┘

IntegrationCategory: PAYMENT | AUTH | EMAIL | STORAGE | ANALYTICS

IntegrationStatus: CONFIGURED | ACTIVE | ERROR
```

### 2.16 MobileAppConfig

```
┌──────────────────────────────────────────┐
│          MobileAppConfig                 │
├──────────────────────────────────────────┤
│ id: UUID (PK)                            │
│ project_id: UUID (FK → Project)          │
│ platforms: MobilePlatform                │
│ framework: MobileFramework               │
│ bundle_id: String                        │
│ app_name: String                         │
│ min_sdk_version: String (nullable)       │
│ target_sdk_version: String (nullable)    │
│ permissions: JSON (list of strings)      │
│ capabilities: JSON (list of strings)     │
│ created_at: DateTime                     │
└──────────────────────────────────────────┘

MobilePlatform: IOS | ANDROID | BOTH

MobileFramework: NATIVE_SWIFT | NATIVE_KOTLIN | REACT_NATIVE | FLUTTER
```

### 2.17 PerformanceReport

```
┌──────────────────────────────────────────┐
│         PerformanceReport                │
├──────────────────────────────────────────┤
│ id: UUID (PK)                            │
│ project_id: UUID (FK → Project)          │
│ pipeline_id: UUID (FK → Pipeline)        │
│ type: PerformanceTestType                │
│ metrics: JSON                            │
│   ├─ response_time_ms: Decimal           │
│   ├─ throughput_rps: Decimal             │
│   ├─ error_rate_percent: Decimal         │
│   ├─ memory_mb: Decimal                  │
│   └─ cpu_percent: Decimal                │
│ score: Decimal (nullable)                │
│ recommendations: JSON (list of strings)  │
│ created_at: DateTime                     │
└──────────────────────────────────────────┘

PerformanceTestType: LOAD_TEST | PROFILING | BENCHMARK | CORE_WEB_VITALS
```

### 2.18 AccessibilityReport

```
┌──────────────────────────────────────────┐
│        AccessibilityReport               │
├──────────────────────────────────────────┤
│ id: UUID (PK)                            │
│ project_id: UUID (FK → Project)          │
│ pipeline_id: UUID (FK → Pipeline)        │
│ wcag_level: WcagLevel                    │
│ violations: JSON (list)                  │
│   ├─ rule_id: String                     │
│   ├─ description: Text                   │
│   ├─ impact: String                      │
│   ├─ element: String                     │
│   └─ fix_suggestion: Text                │
│ warnings: JSON (list)                    │
│ passes: JSON (list)                      │
│ score: Decimal                           │
│ pages_scanned: Integer                   │
│ created_at: DateTime                     │
└──────────────────────────────────────────┘

WcagLevel: A | AA | AAA
```

### 2.19 GitHubIntegration

```
┌──────────────────────────────────────────┐
│         GitHubIntegration                │
├──────────────────────────────────────────┤
│ id: UUID (PK)                            │
│ project_id: UUID (FK → Project)          │
│ repo_owner: String                       │
│ repo_name: String                        │
│ default_branch: String (default: "main") │
│ github_token: String (encrypted)         │
│ auto_pr: Boolean (default: false)        │
│ auto_issues: Boolean (default: false)    │
│ actions_enabled: Boolean (default: false)│
│ last_sync_at: DateTime (nullable)        │
│ created_at: DateTime                     │
└──────────────────────────────────────────┘
```

---

## 3. Entity Relationship Diagram

```
┌──────────────┐  1:N  ┌──────────┐
│     User     │──────▶│  ApiKey  │
└──────────────┘       └──────────┘
  │          │
  │ 1:N      │ 1:N
  ▼          ▼
┌──────────┐ ┌────────────────┐
│ AuditLog │ │    Project     │
└──────────┘ └────────────────┘
               │  (user_id FK → User)
               │
┌────────────────┐  1:1  ┌──────────────┐   1:N   ┌───────────────┐
│    Project     │──────▶│   Pipeline   │────────▶│ PipelinePhase │
└────────────────┘       └──────────────┘         └───────────────┘
  │  │  │  │  │               │                          │
  │  │  │  │  │               │ 1:N                      │ 1:N
  │  │  │  │  │               ▼                          ▼
  │  │  │  │  │         ┌────────────┐             ┌──────────┐
  │  │  │  │  │         │ Checkpoint │             │   Task   │
  │  │  │  │  │         └────────────┘             └──────────┘
  │  │  │  │  │                                         │
  │  │  │  │  │  1:N                                    │
  │  │  │  │  ├────────▶┌──────────┐                    │
  │  │  │  │  │         │  Agent   │                    │
  │  │  │  │  │         └──────────┘                    │
  │  │  │  │  │              │                          │
  │  │  │  │  │              │ 1:N                      │
  │  │  │  │  │              ▼                          │
  │  │  │  │  │        ┌────────────────┐               │
  │  │  │  │  │        │ AgentExecution │◀──────────────┘
  │  │  │  │  │        └────────────────┘          N:1
  │  │  │  │  │
  │  │  │  │  │
  │  │  │  │  │ 1:N     ┌───────────────────┐
  │  │  │  │  └────────▶│ CodeArtifact      │
  │  │  │  │            └───────────────────┘
  │  │  │  │  1:N       ┌───────────────────┐
  │  │  │  └───────────▶│ TestResult        │
  │  │  │               └───────────────────┘
  │  │  │     1:N       ┌───────────────────┐
  │  │  └──────────────▶│ SecurityFinding   │
  │  │                  └───────────────────┘
  │  │        1:N       ┌───────────────────┐
  │  └─────────────────▶│ ReviewComment     │
  │                     └───────────────────┘
  │           1:N       ┌───────────────────┐
  ├────────────────────▶│ Event             │
  │                     └───────────────────┘
  │
  │  ┌──────────────────────────────────────────────────────────────┐
  │  │              Extended Model Relationships                   │
  │  └──────────────────────────────────────────────────────────────┘
  │
  │           1:N       ┌───────────────────┐
  ├────────────────────▶│ BrainstormSession │
  │                     └───────────────────┘
  │           N:1       ┌───────────────────┐
  ├────────────────────▶│ TechStackConfig   │
  │                     └───────────────────┘
  │           N:1       ┌───────────────────┐
  ├────────────────────▶│ Template          │ (shared across projects)
  │                     └───────────────────┘
  │           1:N       ┌───────────────────┐
  ├────────────────────▶│ Deployment        │
  │                     │  └─ FK → Pipeline │
  │                     └───────────────────┘
  │           1:N       ┌─────────────────────┐
  ├────────────────────▶│ CollaborationSession│
  │                     └─────────────────────┘
  │           1:N       ┌───────────────────┐
  ├────────────────────▶│ Integration       │
  │                     └───────────────────┘
  │           1:1       ┌───────────────────┐
  ├────────────────────▶│ MobileAppConfig   │
  │                     └───────────────────┘
  │           1:N       ┌───────────────────┐
  ├────────────────────▶│ PerformanceReport │
  │                     │  └─ FK → Pipeline │
  │                     └───────────────────┘
  │           1:N       ┌─────────────────────┐
  ├────────────────────▶│ AccessibilityReport │
  │                     │  └─ FK → Pipeline   │
  │                     └─────────────────────┘
  │           1:1       ┌───────────────────┐
  ├────────────────────▶│ GitHubIntegration │
  │                     └───────────────────┘
  │           1:N       ┌─────────────────────────┐
  └────────────────────▶│ ProjectManagerReport    │
                        │  └─ FK → Pipeline       │
                        └─────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│              Standalone / Registry Models                        │
└──────────────────────────────────────────────────────────────────┘

┌──────────┐     ┌──────────┐     ┌──────────┐
│  Skill   │     │   Hook   │     │   Tool   │
│          │     │          │     │          │
│ created_ │     │ target_  │     │ mcp_     │
│ by_agent │     │ phase    │     │ server_  │
│ target_  │     │ handler_ │     │ config   │
│ agents   │     │ code     │     │ input/   │
└──────────┘     └──────────┘     │ output_  │
                                  │ schema   │
                                  └──────────┘
```

---

## 4. Configuration Schema

### 4.1 Main Configuration (`configs/default.yaml`)

```yaml
# CodeBot Configuration
version: "2.1"

project:
  workspace_dir: "./workspace"
  max_concurrent_agents: 15
  checkpoint_interval: "phase"  # phase | task | none
  default_project_type: "greenfield"  # greenfield | inflight | brownfield
  human_approval_gates:
    - brainstorming
    - architecture
    - implementation
    - deployment
    - delivery

brainstorming:
  enabled: true
  max_rounds: 10
  auto_finalize_after_minutes: 60
  include_alternatives: true
  include_risk_analysis: true

template_registry:
  enabled: true
  sources:
    - type: local
      path: "./templates"
    - type: remote
      url: "https://templates.codebot.dev/api/v1"
      cache_ttl_hours: 24
  default_design_system: "shadcn"
  default_framework: "nextjs"

tech_stack:
  auto_recommend: true
  confidence_threshold: 0.7
  allowed_languages:
    - python
    - typescript
    - java
    - go
    - rust
    - dart
    - swift
    - kotlin
  allowed_databases:
    - postgresql
    - mysql
    - mongodb
    - redis
    - sqlite
  allowed_hosting_providers:
    - aws
    - gcp
    - azure
    - vercel
    - railway
    - netlify

pipeline:
  default: "full"  # full | quick | review-only
  phases:
    - name: brainstorming
      enabled: true
      timeout_minutes: 60
      requires_approval: true
    - name: tech_stack_selection
      enabled: true
      timeout_minutes: 15
    - name: template_selection
      enabled: true
      timeout_minutes: 10
    - name: planning
      enabled: true
      timeout_minutes: 30
    - name: research
      enabled: true
      timeout_minutes: 20
    - name: architecture
      enabled: true
      timeout_minutes: 30
      requires_approval: true
    - name: design
      enabled: true
      timeout_minutes: 20
    - name: implementation
      enabled: true
      timeout_minutes: 120
      parallel_agents: true
    - name: review
      enabled: true
      timeout_minutes: 30
      parallel_agents: true
    - name: testing
      enabled: true
      timeout_minutes: 30
    - name: debug_fix
      enabled: true
      timeout_minutes: 60
      max_iterations: 5
    - name: documentation
      enabled: true
      timeout_minutes: 20
    - name: deployment
      enabled: true
      timeout_minutes: 30
      requires_approval: true
    - name: delivery
      enabled: true
      timeout_minutes: 15
      requires_approval: true

agents:
  orchestrator:
    provider: anthropic
    model: claude-opus-4
    max_tokens: 8192
    temperature: 0.3
  planner:
    provider: anthropic
    model: claude-sonnet-4
    max_tokens: 4096
    temperature: 0.2
  researcher:
    provider: google
    model: gemini-2.5-pro
    max_tokens: 8192
    temperature: 0.4
  architect:
    provider: anthropic
    model: claude-opus-4
    max_tokens: 8192
    temperature: 0.2
  designer:
    provider: anthropic
    model: claude-sonnet-4
    max_tokens: 4096
    temperature: 0.3
  frontend_dev:
    provider: anthropic
    model: claude-sonnet-4
    cli_agent: claude-code
    max_tokens: 8192
    temperature: 0.1
  backend_dev:
    provider: openai
    model: gpt-4.1
    cli_agent: codex
    max_tokens: 8192
    temperature: 0.1
  middleware_dev:
    provider: anthropic
    model: claude-sonnet-4
    cli_agent: claude-code
    max_tokens: 4096
    temperature: 0.1
  infra_engineer:
    provider: openai
    model: gpt-4.1
    cli_agent: codex
    max_tokens: 4096
    temperature: 0.1
  security_auditor:
    provider: anthropic
    model: claude-opus-4
    max_tokens: 8192
    temperature: 0.1
  code_reviewer:
    provider: anthropic
    model: claude-opus-4
    max_tokens: 8192
    temperature: 0.2
  tester:
    provider: openai
    model: gpt-4.1
    max_tokens: 4096
    temperature: 0.1
  debugger:
    provider: anthropic
    model: claude-opus-4
    cli_agent: claude-code
    max_tokens: 8192
    temperature: 0.2
  doc_writer:
    provider: google
    model: gemini-2.5-flash
    max_tokens: 8192
    temperature: 0.3
  brainstorm_facilitator:
    provider: anthropic
    model: claude-opus-4
    max_tokens: 8192
    temperature: 0.5
  tech_stack_advisor:
    provider: anthropic
    model: claude-sonnet-4
    max_tokens: 4096
    temperature: 0.3
  template_curator:
    provider: anthropic
    model: claude-sonnet-4
    max_tokens: 4096
    temperature: 0.2
  deployer:
    provider: anthropic
    model: claude-sonnet-4
    max_tokens: 4096
    temperature: 0.1
  collaboration_manager:
    provider: anthropic
    model: claude-sonnet-4
    max_tokens: 4096
    temperature: 0.2
  mobile_dev:
    provider: anthropic
    model: claude-sonnet-4
    cli_agent: claude-code
    max_tokens: 8192
    temperature: 0.1
  performance_tester:
    provider: openai
    model: gpt-4.1
    max_tokens: 4096
    temperature: 0.1
  accessibility_auditor:
    provider: anthropic
    model: claude-sonnet-4
    max_tokens: 4096
    temperature: 0.1
  github_integrator:
    provider: anthropic
    model: claude-sonnet-4
    max_tokens: 4096
    temperature: 0.1
  skill_manager:
    provider: anthropic
    model: claude-sonnet-4
    max_tokens: 4096
    temperature: 0.2
  hook_manager:
    provider: anthropic
    model: claude-sonnet-4
    max_tokens: 4096
    temperature: 0.1
  tool_builder:
    provider: anthropic
    model: claude-opus-4
    max_tokens: 8192
    temperature: 0.2
  integration_adapter:
    provider: anthropic
    model: claude-sonnet-4
    max_tokens: 4096
    temperature: 0.1
  i18n_specialist:
    provider: google
    model: gemini-2.5-pro
    max_tokens: 8192
    temperature: 0.2
  api_designer:
    provider: anthropic
    model: claude-opus-4
    max_tokens: 8192
    temperature: 0.2
  project_manager:
    provider: anthropic
    model: claude-sonnet-4
    max_tokens: 4096
    temperature: 0.3

llm:
  providers:
    anthropic:
      api_key_env: ANTHROPIC_API_KEY
      max_retries: 3
      retry_delay_seconds: 5
      rate_limit_rpm: 50
      rate_limit_tpm: 200000
    openai:
      api_key_env: OPENAI_API_KEY
      max_retries: 3
      retry_delay_seconds: 5
      rate_limit_rpm: 60
      rate_limit_tpm: 300000
    google:
      api_key_env: GOOGLE_API_KEY
      max_retries: 3
      retry_delay_seconds: 5
      rate_limit_rpm: 60
      rate_limit_tpm: 400000
  self_hosted:
    ollama:
      enabled: false
      base_url: "http://localhost:11434"
      models:
        - "llama3.1:70b"
        - "codellama:34b"
        - "deepseek-coder:33b"
      max_concurrent: 2
    vllm:
      enabled: false
      base_url: "http://localhost:8000"
      model: "meta-llama/Llama-3.1-70B-Instruct"
      max_concurrent: 4
    localai:
      enabled: false
      base_url: "http://localhost:8080"
      models: []
  routing:
    strategy: task_based  # task_based | cost_optimized | performance_first
    fallback_chain:
      - anthropic
      - openai
      - google
    self_hosted_fallback: false
  budgets:
    max_tokens_per_agent: 500000
    max_cost_per_project_usd: 50.00
    warning_threshold_percent: 80

cli_agents:
  claude_code:
    command: "claude"
    enabled: true
    max_concurrent: 3
  codex:
    command: "codex"
    enabled: true
    max_concurrent: 3
  gemini_cli:
    command: "gemini"
    enabled: true
    max_concurrent: 3

deployment:
  providers:
    vercel:
      enabled: true
      token_env: VERCEL_TOKEN
      default_team: null
    railway:
      enabled: false
      token_env: RAILWAY_TOKEN
    netlify:
      enabled: false
      token_env: NETLIFY_AUTH_TOKEN
    aws:
      enabled: false
      region: "us-east-1"
      credentials_env:
        access_key: AWS_ACCESS_KEY_ID
        secret_key: AWS_SECRET_ACCESS_KEY
    gcp:
      enabled: false
      project_id_env: GCP_PROJECT_ID
      credentials_file_env: GOOGLE_APPLICATION_CREDENTIALS
    azure:
      enabled: false
      subscription_id_env: AZURE_SUBSCRIPTION_ID
      credentials_env:
        tenant_id: AZURE_TENANT_ID
        client_id: AZURE_CLIENT_ID
        client_secret: AZURE_CLIENT_SECRET
  defaults:
    environment: staging
    auto_rollback: true
    health_check_timeout_seconds: 120
    rollback_on_health_check_failure: true

mobile:
  enabled: false
  default_framework: "react-native"
  ios:
    signing_identity_env: IOS_SIGNING_IDENTITY
    provisioning_profile_env: IOS_PROVISIONING_PROFILE
    simulator: "iPhone 15 Pro"
  android:
    sdk_path_env: ANDROID_SDK_ROOT
    keystore_path_env: ANDROID_KEYSTORE_PATH
    keystore_password_env: ANDROID_KEYSTORE_PASSWORD
    emulator: "Pixel_7_API_34"
  build_tools:
    fastlane: true
    eas: false

collaboration:
  enabled: false
  max_participants: 10
  conflict_resolution: "merge"  # last-write-wins | merge | manual
  real_time_sync: true
  cursor_broadcast_interval_ms: 200

skill_registry:
  enabled: true
  auto_learn: true
  max_skills_per_agent: 50
  skill_storage_path: "./workspace/skills"
  share_across_projects: true

hook_registry:
  enabled: true
  max_hooks_per_phase: 10
  hook_timeout_seconds: 60
  hooks_path: "./workspace/hooks"

tool_registry:
  enabled: true
  mcp_servers:
    - name: "filesystem"
      command: "npx"
      args: ["-y", "@modelcontextprotocol/server-filesystem", "./workspace"]
    - name: "github"
      command: "npx"
      args: ["-y", "@modelcontextprotocol/server-github"]
      env:
        GITHUB_TOKEN_ENV: GITHUB_TOKEN
  custom_tools_path: "./workspace/tools"

integration_adapters:
  enabled: true
  supported_categories:
    - payment
    - auth
    - email
    - storage
    - analytics
  adapters:
    stripe:
      category: payment
      api_key_env: STRIPE_SECRET_KEY
    auth0:
      category: auth
      domain_env: AUTH0_DOMAIN
      client_id_env: AUTH0_CLIENT_ID
    sendgrid:
      category: email
      api_key_env: SENDGRID_API_KEY
    s3:
      category: storage
      bucket_env: AWS_S3_BUCKET
    mixpanel:
      category: analytics
      token_env: MIXPANEL_TOKEN

context:
  tiers:
    l0:
      max_tokens: 2000
      includes:
        - project_summary
        - current_task
        - agent_instructions
    l1:
      max_tokens: 10000
      includes:
        - relevant_code_files
        - architecture_docs
        - test_results
    l2:
      max_tokens: 20000
      includes:
        - full_codebase_search
        - external_docs
        - research_results
  vector_store:
    provider: lancedb  # lancedb (dev) | qdrant (prod)
    embedding_model: text-embedding-3-small
    chunk_size: 512
    chunk_overlap: 50
  memory:
    provider: filesystem  # filesystem | openviking
    auto_compress: true
    compression_threshold_tokens: 50000

security:
  sast:
    semgrep:
      enabled: true
      rules: "auto"
    sonarqube:
      enabled: false
      url: "http://localhost:9000"
  dast:
    shannon:
      enabled: false
  dependencies:
    trivy:
      enabled: true
      severity_threshold: HIGH
  secrets:
    gitleaks:
      enabled: true
  licenses:
    scancode:
      enabled: true
      allowed_licenses:
        - MIT
        - Apache-2.0
        - BSD-2-Clause
        - BSD-3-Clause
        - ISC
  quality_gate:
    max_critical: 0
    max_high: 0
    max_medium: 5
    min_coverage_percent: 80

testing:
  frameworks:
    python: pytest
    javascript: vitest
    e2e: playwright
    mobile: detox
  coverage:
    min_line_coverage: 80
    min_branch_coverage: 70
  max_test_retries: 2

performance_testing:
  enabled: true
  tools:
    load_test: k6
    profiling: py-spy
    core_web_vitals: lighthouse
  thresholds:
    response_time_p95_ms: 500
    throughput_min_rps: 100
    error_rate_max_percent: 1.0
    lighthouse_min_score: 90

accessibility:
  enabled: true
  wcag_level: "AA"  # A | AA | AAA
  tools:
    - axe-core
    - pa11y
  scan_on_phases:
    - review
    - testing
  fail_on_violations: true
  ignore_rules: []

i18n:
  enabled: false
  default_locale: "en"
  supported_locales:
    - "en"
    - "es"
    - "fr"
    - "de"
    - "ja"
    - "zh"
  extraction_tool: "i18next-parser"
  auto_translate: false
  translation_provider: "google_translate"  # google_translate | deepl | ai

git:
  worktree:
    pool_size: 5
    cleanup_on_complete: true
  branch_prefix: "codebot/"
  commit_message_prefix: "[CodeBot]"
  auto_merge: false

github:
  enabled: false
  token_env: GITHUB_TOKEN
  auto_pr: false
  auto_issues: false
  actions_enabled: false
  webhook_secret_env: GITHUB_WEBHOOK_SECRET
  pr_template: |
    ## Changes
    {{ description }}

    ## Agent Summary
    - Agents involved: {{ agents }}
    - Total tokens: {{ tokens }}
    - Duration: {{ duration }}

    ---
    *Generated by CodeBot*

server:
  host: "0.0.0.0"
  port: 8000
  workers: 4
  cors_origins:
    - "http://localhost:3000"
    - "http://localhost:5173"

database:
  url: "sqlite:///./workspace/codebot.db"          # dev default
  # url: "postgresql://user:pass@localhost:5432/codebot"  # prod

vector_store:
  provider: lancedb                                 # dev default
  # provider: qdrant                                # prod
  # qdrant_url: "http://localhost:6333"

analytics:
  provider: duckdb
  path: "./workspace/analytics.duckdb"

redis:
  url: "redis://localhost:6379/0"                   # caching & session storage
  # Set to null to disable Redis caching
  # url: null

logging:
  level: INFO
  format: json
  file: "./workspace/logs/codebot.log"

monitoring:
  opentelemetry:
    enabled: false
    endpoint: "http://localhost:4317"
  prometheus:
    enabled: false
    port: 9090
```

---

## 5. Agent Graph Definition Schema

Example of how the expanded SDLC pipeline is defined as a MASFactory-compatible graph with all 29 agents:

```python
# templates/pipelines/standard_sdlc.py

from codebot.graph import RootGraph, Agent, Loop, Switch
from codebot.agents import (
    OrchestratorAgent, PlannerAgent, ResearcherAgent,
    ArchitectAgent, DesignerAgent, FrontendDevAgent,
    BackendDevAgent, MiddlewareDevAgent, InfraEngineerAgent,
    SecurityAuditorAgent, CodeReviewerAgent, TesterAgent,
    DebuggerAgent, DocWriterAgent,
    # New agents (expanded scope)
    BrainstormFacilitatorAgent, TechStackAdvisorAgent,
    TemplateCuratorAgent, DeployerAgent,
    CollaborationManagerAgent, MobileDevAgent,
    PerformanceTesterAgent, AccessibilityAuditorAgent,
    GitHubIntegratorAgent, SkillManagerAgent,
    HookManagerAgent, ToolBuilderAgent,
    IntegrationAdapterAgent, I18nSpecialistAgent,
    ApiDesignerAgent
)

def create_sdlc_pipeline(project_config: dict) -> RootGraph:
    """Create the expanded SDLC pipeline graph with 29 agents."""

    graph = RootGraph(
        name="sdlc_pipeline_v2",
        nodes=[
            # Phase 1: Brainstorming
            ("brainstorm_facilitator", BrainstormFacilitatorAgent()),

            # Phase 2: Tech Stack & Template Selection
            ("tech_stack_advisor", TechStackAdvisorAgent()),
            ("template_curator", TemplateCuratorAgent()),

            # Phase 3: Planning
            ("orchestrator", OrchestratorAgent()),
            ("planner", PlannerAgent()),

            # Phase 4: Research
            ("researcher", ResearcherAgent()),

            # Phase 5: Architecture
            ("architect", ArchitectAgent()),
            ("api_designer", ApiDesignerAgent()),

            # Phase 6: Design
            ("designer", DesignerAgent()),

            # Phase 7: Implementation (parallel)
            ("frontend_dev", FrontendDevAgent()),
            ("backend_dev", BackendDevAgent()),
            ("middleware_dev", MiddlewareDevAgent()),
            ("infra_engineer", InfraEngineerAgent()),
            ("mobile_dev", MobileDevAgent()),
            ("i18n_specialist", I18nSpecialistAgent()),
            ("integration_adapter", IntegrationAdapterAgent()),

            # Phase 8: Review (parallel)
            ("security_auditor", SecurityAuditorAgent()),
            ("code_reviewer", CodeReviewerAgent()),
            ("accessibility_auditor", AccessibilityAuditorAgent()),
            ("performance_tester", PerformanceTesterAgent()),

            # Phase 9: Testing
            ("tester", TesterAgent()),

            # Phase 10: Debug/Fix (loop)
            ("debugger", DebuggerAgent()),

            # Phase 11: Documentation
            ("doc_writer", DocWriterAgent()),

            # Phase 12: Deployment
            ("deployer", DeployerAgent()),
            ("github_integrator", GitHubIntegratorAgent()),

            # Support agents (available across phases)
            ("collaboration_manager", CollaborationManagerAgent()),
            ("skill_manager", SkillManagerAgent()),
            ("hook_manager", HookManagerAgent()),
            ("tool_builder", ToolBuilderAgent()),
        ],
        edges=[
            # Brainstorming flow
            ("entry", "brainstorm_facilitator", {"prd": "requirements"}),

            # Tech stack & template selection
            ("brainstorm_facilitator", "tech_stack_advisor", {
                "refined_requirements": "requirements",
                "risks": "risk_analysis"
            }),
            ("tech_stack_advisor", "template_curator", {
                "tech_stack": "tech_decisions"
            }),

            # Planning flow
            ("template_curator", "orchestrator", {
                "template": "selected_template",
                "tech_stack": "tech_decisions"
            }),
            ("orchestrator", "planner", {"parsed_requirements": "requirements"}),

            # Research flow
            ("planner", "researcher", {
                "plan": "project_plan",
                "tech_stack": "tech_decisions"
            }),

            # Architecture flow
            ("researcher", "architect", {"research": "research_report"}),
            ("planner", "architect", {"plan": "project_plan"}),
            ("architect", "api_designer", {"architecture": "architecture_doc"}),

            # Design flow
            ("architect", "designer", {"architecture": "architecture_doc"}),
            ("api_designer", "designer", {"api_spec": "openapi_spec"}),

            # Implementation flow (fan-out)
            ("designer", "frontend_dev", {
                "design": "design_spec",
                "architecture": "arch_doc"
            }),
            ("architect", "backend_dev", {
                "architecture": "arch_doc",
                "api_spec": "openapi_spec"
            }),
            ("architect", "middleware_dev", {"architecture": "arch_doc"}),
            ("architect", "infra_engineer", {"architecture": "arch_doc"}),
            ("designer", "mobile_dev", {
                "design": "design_spec",
                "architecture": "arch_doc"
            }),
            ("frontend_dev", "i18n_specialist", {"code": "frontend_code"}),
            ("mobile_dev", "i18n_specialist", {"code": "mobile_code"}),
            ("backend_dev", "integration_adapter", {
                "code": "backend_code",
                "integrations": "integration_config"
            }),

            # Review flow (fan-in then fan-out)
            ("frontend_dev", "code_reviewer", {"code": "frontend_code"}),
            ("backend_dev", "code_reviewer", {"code": "backend_code"}),
            ("middleware_dev", "code_reviewer", {"code": "middleware_code"}),
            ("infra_engineer", "code_reviewer", {"code": "infra_code"}),
            ("mobile_dev", "code_reviewer", {"code": "mobile_code"}),
            ("i18n_specialist", "code_reviewer", {"code": "i18n_code"}),
            ("integration_adapter", "code_reviewer", {"code": "integration_code"}),

            ("frontend_dev", "security_auditor", {"code": "frontend_code"}),
            ("backend_dev", "security_auditor", {"code": "backend_code"}),
            ("middleware_dev", "security_auditor", {"code": "middleware_code"}),
            ("infra_engineer", "security_auditor", {"code": "infra_code"}),
            ("mobile_dev", "security_auditor", {"code": "mobile_code"}),

            ("frontend_dev", "accessibility_auditor", {"code": "frontend_code"}),
            ("mobile_dev", "accessibility_auditor", {"code": "mobile_code"}),

            ("frontend_dev", "performance_tester", {"code": "frontend_code"}),
            ("backend_dev", "performance_tester", {"code": "backend_code"}),
            ("mobile_dev", "performance_tester", {"code": "mobile_code"}),

            # Testing flow
            ("code_reviewer", "tester", {"review": "review_report"}),
            ("security_auditor", "tester", {"security": "security_report"}),
            ("accessibility_auditor", "tester", {
                "accessibility": "a11y_report"
            }),
            ("performance_tester", "tester", {
                "performance": "perf_report"
            }),

            # Debug loop
            ("tester", "debugger", {"test_results": "test_report"}),
            ("security_auditor", "debugger", {"findings": "security_findings"}),
            ("code_reviewer", "debugger", {"comments": "review_comments"}),
            ("accessibility_auditor", "debugger", {
                "violations": "a11y_violations"
            }),

            # Documentation
            ("debugger", "doc_writer", {"codebase": "final_code"}),

            # Deployment
            ("doc_writer", "deployer", {"deliverables": "deploy_package"}),
            ("doc_writer", "github_integrator", {
                "deliverables": "final_package"
            }),

            # Hook manager triggers (cross-cutting)
            ("hook_manager", "deployer", {"hooks": "deployment_hooks"}),
            ("hook_manager", "tester", {"hooks": "test_hooks"}),

            # Exit
            ("deployer", "exit", {"deployment": "deployment_result"}),
            ("github_integrator", "exit", {"github": "github_result"}),
        ]
    )

    return graph
```

---

## 6. Message Schemas

### 6.1 Inter-Agent Message

```json
{
  "id": "msg-uuid",
  "type": "task_handoff | result | error | clarification | approval_request",
  "source_agent": "planner",
  "target_agent": "architect",
  "timestamp": "2026-03-18T01:00:00Z",
  "payload": {
    "task_id": "task-uuid",
    "data": { },
    "context": {
      "l0": { },
      "l1_refs": ["file1.py", "schema.sql"],
      "l2_query": "database migration patterns"
    }
  },
  "metadata": {
    "tokens_used": 1500,
    "model": "claude-sonnet-4",
    "duration_ms": 3200
  }
}
```

### 6.2 WebSocket Event

```json
{
  "event": "agent.progress",
  "project_id": "project-uuid",
  "agent_id": "agent-uuid",
  "data": {
    "agent_type": "backend_dev",
    "status": "running",
    "current_task": "Implementing user authentication API",
    "progress_percent": 45,
    "files_modified": ["src/auth/routes.py", "src/auth/models.py"],
    "tokens_used": 5000,
    "cost_usd": 0.15
  },
  "timestamp": "2026-03-18T01:15:00Z"
}
```

### 6.3 Brainstorming Message

```json
{
  "event": "brainstorm.message",
  "project_id": "project-uuid",
  "session_id": "session-uuid",
  "data": {
    "role": "agent",
    "agent_type": "brainstorm_facilitator",
    "content": "Have you considered using WebSocket for real-time updates instead of polling?",
    "alternatives": [
      {
        "option": "Server-Sent Events",
        "pros": ["Simpler", "HTTP-based"],
        "cons": ["Unidirectional"]
      },
      {
        "option": "WebSocket",
        "pros": ["Bidirectional", "Low latency"],
        "cons": ["Connection management complexity"]
      }
    ],
    "risks": [
      {
        "description": "WebSocket connections may be dropped by proxies",
        "mitigation": "Implement reconnection logic with exponential backoff",
        "severity": "medium"
      }
    ]
  },
  "timestamp": "2026-03-18T00:30:00Z"
}
```

### 6.4 Brainstorming Finalized

```json
{
  "event": "brainstorm.finalized",
  "project_id": "project-uuid",
  "session_id": "session-uuid",
  "data": {
    "refined_requirements": "Full refined PRD text...",
    "total_messages": 15,
    "alternatives_explored": 8,
    "risks_identified": 5,
    "duration_minutes": 25
  },
  "timestamp": "2026-03-18T00:55:00Z"
}
```

### 6.5 Deployment Event

```json
{
  "event": "deployment.status",
  "project_id": "project-uuid",
  "deployment_id": "deploy-uuid",
  "data": {
    "provider": "vercel",
    "environment": "staging",
    "status": "deployed",
    "url": "https://my-app-staging.vercel.app",
    "build_duration_seconds": 45,
    "health_check": {
      "status": "healthy",
      "response_time_ms": 120,
      "checks_passed": 5,
      "checks_total": 5
    },
    "previous_deployment_id": "prev-deploy-uuid",
    "rollback_available": true
  },
  "timestamp": "2026-03-18T02:00:00Z"
}
```

### 6.6 Deployment Rollback Event

```json
{
  "event": "deployment.rolled_back",
  "project_id": "project-uuid",
  "deployment_id": "deploy-uuid",
  "data": {
    "reason": "Health check failed: /api/health returned 503",
    "rolled_back_to": "prev-deploy-uuid",
    "rollback_duration_seconds": 12,
    "initiated_by": "auto"
  },
  "timestamp": "2026-03-18T02:05:00Z"
}
```

### 6.7 Collaboration Event

```json
{
  "event": "collaboration.update",
  "project_id": "project-uuid",
  "session_id": "collab-uuid",
  "data": {
    "action": "cursor_move",
    "participant": {
      "id": "agent-uuid",
      "type": "agent",
      "name": "frontend_dev"
    },
    "cursor_position": {
      "file": "src/components/Dashboard.tsx",
      "line": 42,
      "column": 15
    },
    "active_participants": 3
  },
  "timestamp": "2026-03-18T01:30:00Z"
}
```

### 6.8 Collaboration Conflict Event

```json
{
  "event": "collaboration.conflict",
  "project_id": "project-uuid",
  "session_id": "collab-uuid",
  "data": {
    "file": "src/api/routes.py",
    "conflicting_participants": ["backend_dev", "middleware_dev"],
    "conflict_region": {
      "start_line": 45,
      "end_line": 60
    },
    "resolution_strategy": "merge",
    "resolution_status": "resolved",
    "merged_content_hash": "abc123"
  },
  "timestamp": "2026-03-18T01:35:00Z"
}
```

### 6.9 GitHub Webhook Event

```json
{
  "event": "github.webhook",
  "project_id": "project-uuid",
  "integration_id": "gh-uuid",
  "data": {
    "webhook_type": "push",
    "repository": "owner/repo-name",
    "branch": "codebot/frontend-implementation",
    "commits": [
      {
        "sha": "abc123def456",
        "message": "[CodeBot] Implement Dashboard component",
        "author": "codebot[bot]",
        "files_changed": 5
      }
    ],
    "pr_created": {
      "number": 42,
      "title": "feat: Dashboard implementation",
      "url": "https://github.com/owner/repo/pull/42",
      "labels": ["codebot", "auto-generated"]
    }
  },
  "timestamp": "2026-03-18T01:45:00Z"
}
```

### 6.10 GitHub PR Merged Event

```json
{
  "event": "github.pr_merged",
  "project_id": "project-uuid",
  "integration_id": "gh-uuid",
  "data": {
    "pr_number": 42,
    "title": "feat: Dashboard implementation",
    "merged_by": "user",
    "merge_sha": "def456ghi789",
    "branch": "codebot/frontend-implementation",
    "target_branch": "main",
    "files_changed": 12,
    "additions": 450,
    "deletions": 23
  },
  "timestamp": "2026-03-18T02:10:00Z"
}
```

### 6.11 Skill Lifecycle Event

```json
{
  "event": "skill.created",
  "data": {
    "skill_id": "skill-uuid",
    "name": "react-form-validator",
    "description": "Generates React form validation logic with Zod schemas",
    "version": "1.0.0",
    "created_by_agent": "frontend_dev",
    "target_agents": ["frontend_dev", "mobile_dev"],
    "dependencies": ["zod", "react-hook-form"],
    "code_hash": "sha256:abc123"
  },
  "timestamp": "2026-03-18T01:50:00Z"
}
```

### 6.12 Skill Execution Event

```json
{
  "event": "skill.executed",
  "data": {
    "skill_id": "skill-uuid",
    "name": "react-form-validator",
    "executed_by_agent": "frontend_dev",
    "project_id": "project-uuid",
    "success": true,
    "execution_time_ms": 1200,
    "usage_count": 15,
    "updated_success_rate": 0.93
  },
  "timestamp": "2026-03-18T01:55:00Z"
}
```

### 6.13 Hook Lifecycle Event

```json
{
  "event": "hook.triggered",
  "data": {
    "hook_id": "hook-uuid",
    "name": "pre-deploy-lint",
    "phase": "pre",
    "target_phase": "deploy",
    "project_id": "project-uuid",
    "pipeline_id": "pipeline-uuid",
    "status": "running",
    "priority": 10
  },
  "timestamp": "2026-03-18T01:58:00Z"
}
```

### 6.14 Hook Completed Event

```json
{
  "event": "hook.completed",
  "data": {
    "hook_id": "hook-uuid",
    "name": "pre-deploy-lint",
    "status": "success",
    "execution_time_ms": 3400,
    "output": {
      "lint_errors": 0,
      "lint_warnings": 2,
      "passed": true
    }
  },
  "timestamp": "2026-03-18T01:58:04Z"
}
```

### 6.15 Tool Lifecycle Event

```json
{
  "event": "tool.registered",
  "data": {
    "tool_id": "tool-uuid",
    "name": "database-migration-runner",
    "version": "1.0.0",
    "mcp_server": "custom-db-tools",
    "input_schema": {
      "type": "object",
      "properties": {
        "migration_dir": {"type": "string"},
        "target_version": {"type": "string"}
      }
    },
    "created_by_agent": "infra_engineer"
  },
  "timestamp": "2026-03-18T02:00:00Z"
}
```

### 6.16 Tool Invocation Event

```json
{
  "event": "tool.invoked",
  "data": {
    "tool_id": "tool-uuid",
    "name": "database-migration-runner",
    "invoked_by_agent": "backend_dev",
    "project_id": "project-uuid",
    "input": {
      "migration_dir": "./migrations",
      "target_version": "003"
    },
    "output": {
      "migrations_applied": 2,
      "current_version": "003",
      "status": "success"
    },
    "execution_time_ms": 2100
  },
  "timestamp": "2026-03-18T02:02:00Z"
}
```

### 6.17 Pipeline Checkpoint

```json
{
  "pipeline_id": "pipeline-uuid",
  "phase": "implementation",
  "checkpoint_version": 3,
  "state": {
    "completed_phases": [
      "brainstorming",
      "tech_stack_selection",
      "template_selection",
      "planning",
      "research",
      "architecture",
      "design"
    ],
    "current_phase": "implementation",
    "agent_states": {
      "frontend_dev": {"status": "completed", "worktree": "/worktrees/fe-001"},
      "backend_dev": {"status": "running", "worktree": "/worktrees/be-001"},
      "middleware_dev": {"status": "running", "worktree": "/worktrees/mw-001"},
      "infra_engineer": {"status": "completed", "worktree": "/worktrees/infra-001"},
      "mobile_dev": {"status": "running", "worktree": "/worktrees/mobile-001"},
      "i18n_specialist": {"status": "pending"},
      "integration_adapter": {"status": "pending"}
    },
    "artifacts": {
      "brainstorm_output": "docs/brainstorm-summary.md",
      "tech_stack_config": "configs/tech-stack.yaml",
      "architecture_doc": "docs/architecture.md",
      "openapi_spec": "docs/openapi.yaml",
      "design_spec": "docs/design.md"
    },
    "git_state": {
      "main_branch": "main",
      "feature_branches": [
        "codebot/frontend-implementation",
        "codebot/backend-implementation",
        "codebot/middleware-implementation",
        "codebot/infra-setup",
        "codebot/mobile-implementation"
      ],
      "last_merge_sha": "abc123def456"
    },
    "deployment_state": {
      "staging": null,
      "production": null
    }
  },
  "created_at": "2026-03-18T01:20:00Z"
}
```
