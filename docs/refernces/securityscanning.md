Stage 1: Agentic Static Analysis

Shannon Pro transforms the codebase into a Code Property Graph (CPG) combining the AST, control flow graph, and program dependence graph. It then runs five analysis capabilities:

Data Flow Analysis (SAST): Identifies sources (user input, API requests) and sinks (SQL queries, command execution), then traces paths between them. At each node, an LLM evaluates whether the specific sanitization applied is sufficient for the specific vulnerability in context, rather than relying on a hard-coded allowlist of safe functions.
Point Issue Detection (SAST): LLM-based detection of single-location vulnerabilities: weak cryptography, hardcoded credentials, insecure configuration, missing security headers, weak RNG, disabled certificate validation, and overly permissive CORS.
Business Logic Security Testing (SAST): LLM agents analyze the codebase to discover application-specific invariants (e.g., "document access must verify organizational ownership"), generate targeted fuzzers to violate those invariants, and synthesize full PoC exploits. This catches authorization failures and domain-specific logic errors that pattern-based scanners cannot detect.
SCA with Reachability Analysis: Goes beyond flagging CVEs by tracing whether the vulnerable function is actually reachable from application entry points via the CPG. Unreachable vulnerabilities are deprioritized.
Secrets Detection: Combines regex pattern matching with LLM-based detection (for dynamically constructed credentials, custom formats, obfuscated tokens) and performs liveness validation against the corresponding service using read-only API calls.
Stage 2: Autonomous Dynamic Penetration Testing

The same multi-agent pentest pipeline as Shannon Lite (reconnaissance, parallel vulnerability analysis, parallel exploitation, reporting), enhanced with static findings injected into the exploitation queue. Static findings are mapped to Shannon's five attack domains (Injection, XSS, SSRF, Auth, Authz), and exploit agents attempt real proof-of-concept attacks against the running application for each finding.

Static-Dynamic Correlation

This is the core differentiator. A data flow vulnerability identified in static analysis (e.g., unsanitized input reaching a SQL query) is not reported as a theoretical risk. It is fed to the corresponding exploit agent, which attempts to exploit it against the live application. Confirmed exploits are traced back to the exact source code location, giving developers both proof of exploitability and the line of code to fix.

Deployment Model

Shannon Pro supports a self-hosted runner model (similar to GitHub Actions self-hosted runners). The data plane, which handles code access and all LLM API calls, runs entirely within the customer's infrastructure using the customer's own API keys. Source code never leaves the customer's network. The Keygraph control plane handles job orchestration, scan scheduling, and the reporting UI, receiving only aggregate findings.

Capability	
Licensing	AGPL-3.0	Commercial
Static Analysis	Code review prompting	Full agentic SAST, SCA, secrets, business logic testing
Dynamic Testing	Autonomous AI pentesting	Autonomous AI pentesting with static-dynamic correlation
Analysis Engine	Code review prompting	CPG-based data flow with LLM reasoning at every node
Business Logic	None	Automated invariant discovery, fuzzer generation, exploit synthesis
CI/CD Integration	Manual / CLI	Native CI/CD, GitHub PR scanning
Deployment	CLI	Managed cloud or self-hosted runner
Boundary Analysis	None	Automatic service boundary detection with team routing

OS packages and software dependencies in use (SBOM)
Known vulnerabilities (CVEs)
IaC issues and misconfigurations
Sensitive information and secrets
Software licenses
