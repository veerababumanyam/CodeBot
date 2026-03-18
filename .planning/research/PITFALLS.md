# Domain Pitfalls

**Domain:** Autonomous multi-agent SDLC platform (graph-centric, 30 agents, multi-LLM)
**Researched:** 2026-03-18
**Overall Confidence:** HIGH (academic research + production reports + official documentation)

---

## Critical Pitfalls

Mistakes that cause rewrites, architectural dead ends, or fundamental system failures.

---

### Pitfall 1: Error Cascading Across Agent Chain (The Weakest Link Problem)

**What goes wrong:** A single agent produces flawed output (wrong architecture decision, hallucinated dependency, incorrect code pattern) and downstream agents inherit and amplify the error. In a 30-agent pipeline spanning S0-S9, one bad decision in S3 (Architecture) can cascade through S4 (Planning), S5 (Implementation), S6 (QA), and S7 (Testing) before anyone notices. Research shows multi-agent systems have 41%-86.7% failure rates, with error cascading being the primary amplifier.

**Why it happens:** Agents trust upstream outputs by default. Unlike human teams that question suspicious inputs, LLM agents rarely ask for clarification. A slightly off-target task decomposition from a planning agent results in irrelevant implementation, which feeds broken code to QA, which generates tests for the wrong behavior.

**Consequences:**
- Complete pipeline re-execution from the point of corruption
- Wasted tokens and compute (potentially thousands of dollars in LLM costs)
- Generated code that "looks correct" but violates architectural invariants
- Silent quality degradation that passes automated checks

**Prevention:**
- Implement validation gates between every pipeline stage (S0-S9), not just at the end
- Each gate should verify structural correctness (schema validation), semantic correctness (does the output match the input requirements), and consistency (does it align with prior stage outputs)
- Use a "Challenger" pattern: designated verification agents that question outputs before they propagate (research shows this recovers up to 96% of lost performance)
- Maintain an immutable audit trail of all inter-agent messages for debugging cascades
- Implement rollback capabilities: when a gate fails, the system should be able to revert to the last known-good checkpoint

**Detection (warning signs):**
- QA agents flagging issues that should have been caught in architecture/planning
- Tests that pass individually but fail at integration
- Agent outputs that contradict the original PRD without explanation
- Increasing token consumption per stage (agents compensating for bad upstream inputs)

**Phase mapping:** Address in Phase 1 (Agent Graph Engine) by building validation gates into the graph execution model itself. Every edge in the DAG should optionally carry a validation function.

**Confidence:** HIGH - Based on MAST taxonomy (NeurIPS 2025, arXiv:2503.13657) analyzing 150 failure traces across 7 multi-agent systems.

---

### Pitfall 2: Dual Orchestration Complexity (LangGraph + Temporal)

**What goes wrong:** Running two orchestration frameworks (LangGraph for agent graph logic, Temporal for durable workflow execution) creates a "two masters" problem. State lives in two places. Retry logic bleeds into agent logic. Observability is split. Serialization boundaries between Temporal activities and LangGraph StateGraphs add friction at every handoff.

**Why it happens:** LangGraph excels at "given this state, what should the agent do next?" while Temporal excels at "did this complete, and if not, what do we do about it?" The temptation is to use both for their strengths, but the integration boundary is where complexity explodes.

**Consequences:**
- State synchronization bugs: Temporal's workflow state and LangGraph's graph state can diverge
- Split observability: Temporal Web UI shows workflow execution but LangGraph's internal node transitions require separate logging/tracing
- Serialization overhead: all data crossing the Temporal activity boundary must be serializable, limiting what LangGraph nodes can pass
- Sandbox violations: Temporal's deterministic execution model requires explicit passthrough configuration for non-deterministic libraries
- Developers must understand two frameworks' constraints simultaneously
- Debugging requires correlating events across two separate systems

**Prevention:**
- Define a clear boundary: Temporal owns durability, retry, and cross-stage orchestration (S0 through S9 transitions). LangGraph owns intra-stage agent graph execution (what happens within S5, for example)
- Never let retry logic cross the boundary — Temporal retries activities, LangGraph handles internal node retries
- Use a unified trace ID that propagates through both systems
- State schemas must use only serializable types at activity boundaries — design this constraint into the data model from day one
- Evaluate whether LangGraph 1.0's built-in durable execution (released October 2025) reduces the need for Temporal at all

**Detection (warning signs):**
- Developers frequently confused about "where does this state live?"
- Bug reports that require checking both Temporal UI and LangGraph logs
- Retry storms where both systems try to recover the same failure
- Increasing time spent debugging framework integration vs. business logic

**Phase mapping:** Address in Phase 1 (Graph Engine) with a clear architectural decision document. Prototype the integration boundary before building the full pipeline. Consider starting with LangGraph-only and adding Temporal later only if durability requirements demand it.

**Confidence:** HIGH - Based on production reports from Grid Dynamics migration case study and Temporal team's own guidance.

---

### Pitfall 3: Context Window Exhaustion in Multi-Step Agent Workflows

**What goes wrong:** Agents burn through context windows fast. A 50-step workflow with 20K tokens per LLM call equals 1M tokens total. In CodeBot's pipeline, each stage may involve multiple agent calls, tool outputs, code generation, and review cycles. Context silently overflows — the agent continues working with partial context and produces confident but incorrect results. Research on "context rot" shows that model accuracy degrades as context length grows, even within the window limit.

**Why it happens:** Context accumulates across every LLM call. Tool outputs (code files, test results, security scan reports) are verbose. The "lost in the middle" effect means critical information placed in the middle of long contexts is underweighted by the model. Bigger context windows are not a silver bullet — performance degrades with length.

**Consequences:**
- Agents "forget" earlier requirements mid-workflow
- Generated code contradicts architectural decisions from earlier stages
- Security requirements silently dropped from context
- Massive token costs from oversized contexts that don't even improve quality
- Silent failures: no error is thrown, the agent just produces worse output

**Prevention:**
- Implement the 3-tier context system (L0/L1/L2) rigorously, not as an afterthought
- L0: only truly essential context (project config, current task spec) — hard limit at ~4K tokens
- L1: phase-scoped context with automatic summarization of completed phases
- L2: on-demand retrieval via vector store — never pre-load "just in case"
- Set explicit token budgets per agent call; measure and enforce them
- Compress tool outputs before adding to context (e.g., summarize security scan results, show only failing test names)
- Place critical information (requirements, constraints) at the beginning and end of prompts, never only in the middle
- Implement context observability: track token usage per agent call, alert when approaching limits

**Detection (warning signs):**
- Agents producing outputs that contradict earlier stage decisions
- Rising token costs per pipeline execution over time
- Agent asking questions that were answered earlier in the pipeline
- Code reviews catching requirement violations that agents should have known about

**Phase mapping:** Address in Phase 1 (Context Management). The 3-tier system is not a "nice to have" — it is load-bearing architecture. Build and test it before implementing any agents.

**Confidence:** HIGH - Based on Anthropic's context engineering guidance, Factory.ai research, and Hong et al. (2025) context rot measurements across 18 LLMs.

---

### Pitfall 4: AI-Generated Code Security Vulnerabilities and Hallucinated Dependencies

**What goes wrong:** AI models generate code with security vulnerabilities 48-62% of the time. Agents hallucinate non-existent package names (~20% of code samples), creating "slopsquatting" attack vectors where malicious actors register those names. Agents choose insecure coding patterns (string-concatenated SQL, missing input validation, hardcoded secrets) 45% of the time because those patterns are prevalent in training data. "Architectural drift" — subtle design changes that break security invariants without violating syntax — evades both static analysis and human review.

**Why it happens:** LLMs learn by pattern matching against training data. If unsafe patterns appear frequently in the training set, the model reproduces them. Agents don't understand the risk model behind code — they can miss guardrails like validation, access checks, and output encoding. In a 30-agent system, the volume of generated code makes thorough human review impractical.

**Consequences:**
- Vulnerable code reaching production (injection, XSS, SSRF, path traversal)
- Malicious dependencies injected through hallucinated package names
- Security invariants violated without any syntax error
- False confidence: code "looks correct" and passes basic tests but is exploitable
- Supply chain attacks through the development pipeline itself

**Prevention:**
- Security scanning (Semgrep, Trivy, Gitleaks) must run after EVERY code generation step, not just at the S6 quality gate
- Implement a dependency allowlist: only packages from a curated registry can be imported; hallucinated packages are rejected immediately
- Use Semgrep custom rules tailored to CodeBot's patterns (e.g., enforce parameterized queries, require input validation on all API endpoints)
- The S8 (Debug & Fix) loop must include security-specific debugging, not just functional debugging
- Static analysis alone is insufficient — add property-based testing for security invariants (e.g., "no user input reaches SQL without parameterization")
- Human review gates at S6 should specifically target architectural drift, not just line-level bugs

**Detection (warning signs):**
- Semgrep/Trivy finding HIGH/CRITICAL issues in agent-generated code regularly
- Dependency resolution failures from non-existent packages
- Security scan results showing patterns the agent was supposed to avoid
- Test suites that pass but miss edge cases around input validation

**Phase mapping:** Address in Phase 1 (Security Pipeline foundation) and enforce throughout S5-S8. The security scanning infrastructure must be ready before any code generation agent runs.

**Confidence:** HIGH - Based on multiple peer-reviewed studies (Endor Labs, CSA, OWASP Agentic AI Top 10), IDEsaster disclosure (30+ CVEs in AI coding tools), and slopsquatting research.

---

### Pitfall 5: Git Worktree Isolation Is Incomplete

**What goes wrong:** Git worktrees isolate the filesystem but NOT the runtime environment. Two agents running in parallel worktrees share the same ports, databases, Docker daemon, and cache directories. Agent A modifying database state while Agent B reads it creates race conditions. Port conflicts (3000, 5432, 8080) cause silent failures. Disk usage explodes: a 2GB codebase can consume 10GB in 20 minutes of active worktree creation.

**Why it happens:** Worktrees were designed for human developers switching between branches, not for parallel autonomous agents. The ecosystem (IDEs, devcontainers, build tools) has inconsistent worktree support. There is no tool that connects worktree code isolation with full environment isolation.

**Consequences:**
- Race conditions in shared databases/caches corrupting test results
- Port conflicts causing agent failures that look like application bugs
- Disk space exhaustion on CI/CD machines or developer workstations
- Merge conflicts when parallel agents touch overlapping files
- Agent context confusion: agents modify wrong files or reference stale state
- Build artifact pollution across worktrees sharing the same Docker daemon

**Prevention:**
- Per-worktree database instances: use Docker Compose profiles with worktree-indexed container names (e.g., `codebot-db-worktree-{hash}`)
- Dynamic port allocation: assign port ranges per worktree, never use hardcoded defaults
- Implement a worktree lifecycle manager: automatic creation, health monitoring, cleanup after agent completion
- Design agents to work on non-overlapping file sets when possible (the task decomposition in S4 must account for file-level dependencies)
- Set disk quotas and implement automatic cleanup of stale worktrees and build artifacts
- Run integration tests in isolated Docker networks per worktree

**Detection (warning signs):**
- Intermittent test failures that don't reproduce in isolation
- "Address already in use" errors during parallel agent execution
- Disk space alerts during pipeline runs
- Merge conflicts that shouldn't exist given the task decomposition
- Agents reporting "file not found" for files that exist in another worktree

**Phase mapping:** Address in Phase 1 (Agent Isolation infrastructure). This is the foundation that all parallel execution in S3, S5, and S6 depends on.

**Confidence:** HIGH - Based on extensive community reporting (Nx Blog, Upsun DevCenter, ccswarm project) and documented production issues.

---

## Moderate Pitfalls

Issues that cause significant rework, degraded performance, or poor user experience, but are recoverable without architectural rewrites.

---

### Pitfall 6: LLM Provider Abstraction Layer Becomes the Bottleneck

**What goes wrong:** The multi-LLM abstraction layer (using LiteLLM or similar) introduces latency overhead that compounds in agent loops. Memory leaks appear under sustained load. Database logging slows API requests when volume exceeds ~1M records. Routing strategies that work in testing (usage-based, cost-optimized) degrade in production. The abstraction layer itself becomes a single point of failure.

**Why it happens:** LLM gateways add serialization, logging, routing logic, and retry handling to every call. In a 30-agent system making hundreds of LLM calls per pipeline execution, even 50ms overhead per call adds up to seconds of latency. The gateway's database accumulates logs rapidly and isn't designed for the write volume of an agent orchestrator.

**Prevention:**
- Benchmark the gateway under realistic load (30 concurrent agents, mixed providers) before committing to it
- Implement log rotation/archival from day one — don't let the logging database grow unbounded
- Use direct provider SDKs for the hot path (implementation agents in S5 making rapid iterative calls) and route through the gateway only for cross-cutting concerns (cost tracking, fallback)
- Test fallback chains with real failure modes: 429 rate limits, 5xx outages, slow responses
- Monitor gateway memory and restart workers on a schedule (LiteLLM's own production guidance recommends worker recycling)
- Have a "gateway bypass" capability for when the abstraction layer itself is the problem

**Detection (warning signs):**
- Increasing p99 latency on LLM calls over days/weeks without model changes
- Memory usage of the gateway process growing linearly over time
- LLM API errors that don't match the actual provider status
- Agents waiting on LLM responses longer than the model's inherent latency

**Phase mapping:** Address in Phase 2 (Multi-LLM Layer). Build with a bypass mechanism from the start.

**Confidence:** HIGH - Based on LiteLLM GitHub issues, production reports, and benchmark comparisons with alternatives like Bifrost (11us overhead).

---

### Pitfall 7: NATS JetStream Message Ordering Breaks Under Load

**What goes wrong:** While NATS JetStream guarantees message ordering within a stream at the publishing level, consumer-level ordering is NOT enforced during message redelivery. If a consumer NACKs a message, subsequent messages may be delivered and processed before the retried message arrives. The only mitigation (`max_ack_pending=1`) kills throughput. Deduplication windows default to 2 minutes — retries beyond that window allow duplicates.

**Why it happens:** JetStream is designed for high-throughput at-least-once delivery, not strict ordering with exactly-once semantics. The agent event bus requires both: agents must process events in order (architecture decisions before implementation) and must not process duplicate events (avoid double-execution of expensive LLM calls).

**Prevention:**
- Design consumers to be idempotent: processing the same event twice should produce the same result
- Use event sequence numbers in the application layer, not just JetStream's built-in ordering
- For pipeline stage transitions (S0 to S1, S1 to S2, etc.), use a synchronous acknowledgment pattern rather than fire-and-forget
- Set deduplication windows based on actual retry behavior, not the 2-minute default
- Monitor consumer lag and NACK rates as early indicators of ordering issues
- Consider using NATS request-reply for synchronous inter-stage communication and JetStream only for async event logging/replay

**Detection (warning signs):**
- Agents executing out of expected pipeline order
- Duplicate agent executions for the same task
- Consumer lag growing in JetStream dashboards
- Unexplained state inconsistencies between agents that should have the same view of the world

**Phase mapping:** Already partially addressed (NATS event bus exists with integration tests). Validate ordering guarantees under concurrent load in Phase 1.

**Confidence:** HIGH - Based on NATS GitHub discussions (#7106 strict ordering proposal, #6909 production resource issues) and official documentation.

---

### Pitfall 8: Real-Time Dashboard Renders Itself to Death

**What goes wrong:** A dashboard monitoring 30 agents with real-time graph visualization (React Flow), live logs (xterm.js), and code diffs (Monaco Editor) generates hundreds of WebSocket events per second. Each event triggers a React re-render. Without careful optimization, the browser tab freezes, memory grows unbounded, and the dashboard becomes unusable precisely when the user needs it most (during complex pipeline runs).

**Why it happens:** React's default behavior re-renders on every state change. Socket.IO delivers events as fast as the server sends them. React Flow's graph layout is expensive to recompute. Monaco Editor and xterm.js have their own rendering pipelines that conflict with React's virtual DOM. Unbounded log buffers and event histories consume memory linearly.

**Prevention:**
- Batch WebSocket updates: buffer events in a ref, flush to state at 100ms intervals (humans can't perceive sub-100ms updates)
- Implement back-pressure: the server should throttle event rate based on client acknowledgment
- Use React.memo aggressively on React Flow nodes and edges — only re-render on actual data changes
- Virtualize all lists: agent logs, event streams, file trees (render only visible rows)
- Cap buffer sizes: keep only the last N log lines, last N events per agent
- Offload aggregation to the server: send computed metrics (agent status summaries) instead of raw events
- Use Web Workers for data transformation (aggregating agent metrics, filtering events)
- Profile with React DevTools before launch: identify components that re-render > 16ms

**Detection (warning signs):**
- Dashboard becoming sluggish during active pipeline runs (especially S5 parallel implementation)
- Browser memory growing linearly during long pipeline executions
- Users reporting "frozen" dashboard that recovers when pipeline completes
- React DevTools showing unnecessary re-renders on graph visualization components

**Phase mapping:** Address in Phase 3 (Dashboard). Build the event batching and back-pressure infrastructure before adding real-time visualizations.

**Confidence:** HIGH - Based on React performance optimization guides, WebSocket dashboard production patterns, and React Flow documentation.

---

### Pitfall 9: Temporal Workflow Determinism Violations

**What goes wrong:** Temporal workflows must be deterministic — they are replayed to recover state after failures. Any non-deterministic operation (random numbers, current time, network calls, reading environment variables) inside a workflow causes replay failures. Adding new activities or changing workflow logic after deployment can break running workflows.

**Why it happens:** Developers accustomed to normal Python/async programming use non-deterministic operations without thinking. Temporal's replay model is fundamentally different from typical request-response architectures. The constraint is subtle and easy to violate.

**Prevention:**
- All business logic (LLM calls, file operations, database queries) must live in Activities, never in Workflows
- Workflows should only contain orchestration: sequence activities, handle signals, manage timers
- Use Temporal's versioning APIs for workflow logic changes deployed while workflows are running
- Implement a Temporal linter/test that detects non-deterministic operations in workflow code
- Use structured input/output (single Pydantic model in, single Pydantic model out) for all activities
- Model expected errors as activity return values, not exceptions — workflow failure should indicate a bug in orchestration, not a business error

**Detection (warning signs):**
- `NonDeterminismError` in Temporal worker logs
- Workflows that fail on replay but succeed on first execution
- Flaky workflow tests that pass intermittently
- Developers putting LLM calls directly in workflow code

**Phase mapping:** Address in Phase 1 (Temporal integration). Establish and enforce the workflow/activity boundary pattern before any agent workflows are built.

**Confidence:** HIGH - Based on Temporal official documentation, community best practices, and production case studies.

---

### Pitfall 10: Vector Store Code Retrieval Returns Irrelevant Context

**What goes wrong:** Pure vector similarity search for code retrieval misses architectural context. A query for "authentication middleware" might return a string-similar but functionally unrelated function. Code chunks created by naive splitting (fixed token size) break logical units — half a function, class definition without methods. The "lost in the middle" effect compounds: even when the right code is retrieved, it may be buried among irrelevant chunks.

**Why it happens:** Code is fundamentally different from natural language documents. Functions have dependencies, classes have inheritance hierarchies, modules have import relationships. Embedding similarity captures surface-level semantics but misses structural relationships. Naive chunking destroys the logical boundaries that give code its meaning.

**Prevention:**
- Use Tree-sitter AST-based chunking exclusively — never chunk code by token count or line count
- Implement a hybrid retrieval strategy: vector similarity + dependency graph traversal (research shows graph-based ranking is up to 10x more token-efficient)
- Build a code dependency graph alongside the vector store: function calls, imports, inheritance
- Use Tree-sitter to extract definitions and references, then build a PageRank-weighted relevance model (Aider's approach)
- Implement incremental indexing: reindex only changed files, not the entire codebase
- Test retrieval quality with ground-truth benchmarks: can the system find the right code for known queries?

**Detection (warning signs):**
- Agents generating code that duplicates existing functionality (retrieval missed existing implementation)
- Context management pulling in irrelevant files that waste token budget
- Agents asking "where is X defined?" when it's in the indexed codebase
- Retrieval results that are syntactically similar but semantically wrong

**Phase mapping:** Address in Phase 2 (Context Management system). The vector store is part of the L2 retrieval tier and must be tested with real codebase queries.

**Confidence:** HIGH - Based on CAST paper, Aider's implementation, CocoIndex benchmarks, and the archiving of GitHub's Stack Graphs.

---

## Minor Pitfalls

Issues that cause friction, delay, or suboptimal outcomes but are fixable without significant rework.

---

### Pitfall 11: Security Scan False Positive Fatigue

**What goes wrong:** Running Semgrep, Trivy, Gitleaks, and SonarQube on every pipeline execution generates hundreds of findings, many of which are false positives. Developers and agents learn to ignore scan results, defeating the purpose of the security pipeline. Quality gates that block on any finding become blockers; gates that allow anything become meaningless.

**Prevention:**
- Tune severity thresholds: block pipeline on CRITICAL and HIGH only
- Create project-specific Semgrep rules that reduce false positives for CodeBot's patterns
- Implement a finding triage workflow: new findings require classification (true positive, false positive, acceptable risk)
- Use Semgrep's cross-file analysis to reduce false positive rate by ~25%
- Maintain a suppression file for known false positives, reviewed periodically
- Track false positive rates as a metric — if they exceed 30%, the rules need tuning

**Detection (warning signs):**
- Agents or developers routinely suppressing findings without review
- Quality gate pass rates suspiciously high (nobody is finding anything) or suspiciously low (everything is blocked)
- Security scan step becoming the longest phase in the pipeline

**Phase mapping:** Address in Phase 2 (Security Pipeline). Start with a minimal, high-confidence rule set and expand.

**Confidence:** MEDIUM - Based on general DevSecOps best practices and Semgrep's documented false positive reduction capabilities.

---

### Pitfall 12: CRDT Collaboration Complexity Exceeds Value

**What goes wrong:** Implementing real-time collaboration with Yjs CRDTs requires building WebSocket lifecycle management, offline sync, presence indicators, cursor tracking, and dealing with tombstone growth (documents grow indefinitely as deleted content leaves metadata). The development effort is substantial and the resulting infrastructure requires distributed systems expertise to operate.

**Prevention:**
- Defer CRDT collaboration to a later milestone — it is not required for the core SDLC pipeline
- If implemented, start with a managed solution or Yjs with a proven provider (y-websocket) rather than building custom infrastructure
- Set document size limits and implement periodic compaction to manage tombstone growth
- Scope collaboration to specific features (e.g., shared code review view) rather than "everything is collaborative"

**Detection (warning signs):**
- CRDT infrastructure consuming more development time than core agent features
- Document sizes growing over time even when content is deleted
- WebSocket connection management bugs dominating the bug tracker

**Phase mapping:** Defer to Phase 4+ (Dashboard enhancements). The core pipeline does not require real-time collaboration.

**Confidence:** MEDIUM - Based on Yjs documentation, Velt's production guide, and community reports of integration complexity.

---

### Pitfall 13: Agent Role Drift and Specification Ambiguity

**What goes wrong:** Agents "disobey" their assigned roles. A subordinate agent makes executive decisions. A code generation agent starts making architecture choices. Agents get stuck in loops, repeating completed steps. The MAST taxonomy identifies these as the most common single-agent failures in multi-agent systems.

**Prevention:**
- Define explicit role boundaries in each agent's system prompt using a "responsibility matrix"
- Use structured output schemas (JSON/Pydantic) that force agents to declare intent, inputs, and expected outputs
- Implement a role-drift detector: compare agent outputs against expected output schemas and flag deviations
- Set maximum step counts per agent to prevent infinite loops
- Use the hierarchical supervisor pattern: the orchestrator agent reviews subordinate outputs for role compliance

**Detection (warning signs):**
- Agent outputs containing information outside their designated scope
- Agents producing duplicate work that another agent already completed
- Step repetition: the same tool call appearing multiple times in agent traces
- Orchestrator overriding agent decisions frequently

**Phase mapping:** Address in Phase 1 (Agent Framework) by building role enforcement into BaseAgent.

**Confidence:** HIGH - Based on MAST taxonomy (NeurIPS 2025) identifying specification failures as the largest category of multi-agent breakdowns.

---

### Pitfall 14: LangGraph API Instability and Abstraction Depth

**What goes wrong:** LangGraph's API has been evolving rapidly. Tutorials break after updates. Customizing agent behavior requires digging through multiple abstraction layers. The steep learning curve (2-4 weeks to productivity) applies to each team member.

**Prevention:**
- Pin LangGraph to a specific version and don't upgrade without testing
- Build a thin wrapper around LangGraph's APIs: isolate your code from direct LangGraph imports so that API changes require updates in one place
- Prefer LangGraph's low-level graph primitives (StateGraph, nodes, edges) over high-level abstractions
- Use LangGraph 1.0+ (released October 2025) which stabilized the core API
- Maintain an internal "LangGraph patterns" document with tested, working code examples

**Detection (warning signs):**
- Import errors or deprecation warnings after LangGraph updates
- Developer time spent debugging framework behavior rather than business logic
- Workarounds accumulating in the codebase for LangGraph limitations

**Phase mapping:** Address in Phase 1 (Graph Engine). Pin version, create wrapper, document patterns.

**Confidence:** HIGH - Based on ZenML LangGraph alternatives analysis, community reports, and LangGraph 1.0 release notes.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Agent Graph Engine (Phase 1) | Dual orchestration complexity (LangGraph + Temporal) | Define clear boundaries; prototype integration first |
| Agent Graph Engine (Phase 1) | Validation gates missing between stages | Build gates into the graph execution model, not as afterthoughts |
| Agent Framework (Phase 1) | Agent role drift and specification ambiguity | Role enforcement in BaseAgent; structured output schemas |
| Agent Isolation (Phase 1) | Git worktree runtime isolation gaps | Per-worktree Docker Compose profiles, dynamic port allocation |
| Context Management (Phase 1-2) | Context window exhaustion | Implement L0/L1/L2 rigorously; token budgets per call |
| Context Management (Phase 2) | Poor code retrieval quality | Tree-sitter AST chunking + dependency graph hybrid |
| Multi-LLM Layer (Phase 2) | Gateway becoming bottleneck | Benchmark under load; build bypass mechanism |
| NATS Event Bus (Phase 1) | Message ordering breaks under redelivery | Idempotent consumers; application-layer sequence numbers |
| Security Pipeline (Phase 2) | False positive fatigue | Start minimal; tune thresholds; track false positive rates |
| Dashboard (Phase 3) | Re-render storms from WebSocket events | Event batching, back-pressure, virtualization |
| Code Generation (Phase 2+) | AI-generated security vulnerabilities | Scan after every generation step; dependency allowlist |
| Collaboration (Phase 4+) | CRDT complexity exceeding value | Defer; scope narrowly; use managed solutions |

---

## Sources

### Academic Research
- [Why Do Multi-Agent LLM Systems Fail? (MAST Taxonomy, NeurIPS 2025)](https://arxiv.org/abs/2503.13657) - arXiv:2503.13657
- [Why Do Multi-Agent LLM Systems Fail? (Galileo analysis)](https://galileo.ai/blog/multi-agent-llm-systems-fail)
- [Why Multi-Agent LLM Systems Fail (Orq.ai)](https://orq.ai/blog/why-do-multi-agent-llm-systems-fail)

### LangGraph & Orchestration
- [LangGraph 1.0 Release (October 2025)](https://medium.com/@romerorico.hugo/langgraph-1-0-released-no-breaking-changes-all-the-hard-won-lessons-8939d500ca7c)
- [LangGraph Architecture Guide 2025 (Latenode)](https://latenode.com/blog/ai-frameworks-technical-infrastructure/langgraph-multi-agent-orchestration/langgraph-ai-framework-2025-complete-architecture-guide-multi-agent-orchestration-analysis)
- [8 LangGraph Alternatives (ZenML)](https://www.zenml.io/blog/langgraph-alternatives)
- [Temporal + LangGraph Integration (DeepWiki)](https://deepwiki.com/domainio/temporal-langgraph-poc/2.1-temporal-and-langgraph-integration)

### Temporal
- [Good Practices for Temporal Workflows](https://raphaelbeamonte.com/posts/good-practices-for-writing-temporal-workflows-and-activities/)
- [How Many Activities in a Temporal Workflow](https://temporal.io/blog/how-many-activities-should-i-use-in-my-temporal-workflow)
- [Temporal Error Handling Guide](https://temporal.io/blog/error-handling-in-distributed-systems)

### Context Management
- [The Context Window Problem (Factory.ai)](https://factory.ai/news/context-window-problem)
- [Effective Context Engineering for AI Agents (Anthropic)](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Context Window Management Strategies (Maxim)](https://www.getmaxim.ai/articles/context-window-management-strategies-for-long-context-ai-agents-and-chatbots/)

### Git Worktrees
- [Git Worktrees for Parallel AI Agents (Upsun)](https://devcenter.upsun.com/posts/git-worktrees-for-parallel-ai-coding-agents/)
- [Git Worktrees and AI Agents (Nx Blog)](https://nx.dev/blog/git-worktrees-ai-agents)
- [ccswarm: Multi-agent Orchestration with Git Worktrees](https://github.com/nwiizo/ccswarm)

### LLM Provider Abstraction
- [LiteLLM Routing & Load Balancing Docs](https://docs.litellm.ai/docs/routing-load-balancing)
- [Top LiteLLM Alternatives 2025 (Maxim)](https://www.getmaxim.ai/articles/top-5-litellm-alternatives-in-2025/)
- [LLM Gateway Comparison 2025 (Agenta)](https://agenta.ai/blog/top-llm-gateways)

### Security
- [AI-Generated Code Vulnerabilities (Endor Labs)](https://www.endorlabs.com/learn/the-most-common-security-vulnerabilities-in-ai-generated-code)
- [OWASP Agentic AI Top 10 (Legit Security)](https://www.legitsecurity.com/blog/from-chatbot-to-code-threat-owasps-agentic-ai-top-10-and-the-specialized-risks-of-coding-agents)
- [Slopsquatting Threat (DevOps.com)](https://devops.com/ai-generated-code-packages-can-lead-to-slopsquatting-threat-2/)
- [IDEsaster: 30+ Flaws in AI Coding Tools](https://thehackernews.com/2025/12/researchers-uncover-30-flaws-in-ai.html)

### NATS JetStream
- [JetStream Strict Ordering Proposal (GitHub #7106)](https://github.com/nats-io/nats-server/issues/7106)
- [JetStream Production Resource Issue (GitHub #6909)](https://github.com/nats-io/nats-server/issues/6909)
- [JetStream Model Deep Dive (NATS Docs)](https://docs.nats.io/using-nats/developer/develop_jetstream/model_deep_dive)

### Dashboard & Real-Time UI
- [React Performance Optimization 2025 (DEV Community)](https://dev.to/alex_bobes/react-performance-optimization-15-best-practices-for-2025-17l9)
- [WebSockets vs SSE for Real-Time Streaming](https://medium.com/@sulmanahmed135/websockets-vs-server-sent-events-sse-a-practical-guide-for-real-time-data-streaming-in-modern-c57037a5a589)

### Code Retrieval & Indexing
- [Building RAG on Codebases (LanceDB)](https://lancedb.com/blog/building-rag-on-codebases-part-1/)
- [CodeRAG with Dependency Graph (Tree-sitter)](https://medium.com/@shsax/how-i-built-coderag-with-dependency-graph-using-tree-sitter-0a71867059ae)
- [Real-Time Codebase Indexing (CocoIndex)](https://cocoindex.io/blogs/index-code-base-for-rag)

### CRDT / Collaboration
- [Yjs Documentation](https://docs.yjs.dev/)
- [Yjs WebSocket Server Guide (Velt)](https://velt.dev/blog/yjs-websocket-server-real-time-collaboration)
- [CRDT Implementation Guide (Velt)](https://velt.dev/blog/crdt-implementation-guide-conflict-free-apps)
