---
skill: codebot-security-pipeline
title: CodeBot Security & Quality Pipeline
description: >
  How to work with CodeBot's security and quality pipeline — scanning generated
  code for vulnerabilities, secrets, license issues, and quality problems.
tags:
  - security
  - sast
  - dast
  - dependency-scanning
  - secrets-detection
  - license-compliance
  - quality-gate
  - codebot
language: python
python_version: "3.12+"
---

# CodeBot Security & Quality Pipeline

## Overview

The security pipeline lives in `apps/server/src/codebot/security/` and runs as
part of **Stage S6 (Quality Assurance)**. It executes in parallel with the Code
Reviewer, Accessibility Agent, i18n Agent, and Performance Agent. The Security
Auditor agent at `apps/server/src/codebot/agents/security_auditor.py`
coordinates high-level decisions while the pipeline handles scan execution.

### Key Files

| File | Purpose |
|------|---------|
| `orchestrator.py` | Security scan orchestrator — builds and runs the scan graph |
| `sast.py` | SAST integration (Semgrep + SonarQube) |
| `dast.py` | DAST integration (OWASP ZAP) |
| `dependency.py` | Dependency vulnerability scanning (Trivy + OpenSCA) |
| `secrets.py` | Secret detection (Gitleaks) |
| `license.py` | License compliance (ScanCode / FOSSology / ORT) |
| `report.py` | Security report generation and formatting |
| `gate.py` | Security quality gate — pass/fail decisions |

All paths are relative to `apps/server/src/codebot/security/`.

### Tools

- **SAST:** Semgrep, Bandit (Python-specific), SonarQube
- **DAST:** OWASP ZAP (primary), Playwright-based security tests
- **Dependencies:** Trivy, OpenSCA
- **Secrets:** Gitleaks
- **License:** ScanCode, FOSSology, ORT (OSS Review Toolkit)

---

## 1. Security Pipeline Architecture

The pipeline uses the **ComposedGraph** pattern. `security_scan_pipeline()`
fans out four scan categories in parallel, merges results, then evaluates the
quality gate.

```
orchestrator
    |
    +---> SAST scan --------+
    +---> DAST scan --------+---> merge_results ---> GATE
    +---> Dependency scan --+
    +---> Secrets scan -----+
```

### Orchestrator Pattern

```python
# apps/server/src/codebot/security/orchestrator.py

from langgraph.graph import StateGraph

async def security_scan_pipeline(state: SecurityState) -> SecurityState:
    """Fan-out parallel scans, merge, evaluate gate."""
    graph = StateGraph(SecurityState)

    graph.add_node("sast", run_sast_scan)
    graph.add_node("dast", run_dast_scan)
    graph.add_node("dependency", run_dependency_scan)
    graph.add_node("secrets", run_secrets_scan)
    graph.add_node("merge", merge_scan_results)
    graph.add_node("gate", evaluate_security_gate)

    # Fan-out from START to all scanners
    graph.add_edge(START, "sast")
    graph.add_edge(START, "dast")
    graph.add_edge(START, "dependency")
    graph.add_edge(START, "secrets")

    # Fan-in to merge
    graph.add_edge("sast", "merge")
    graph.add_edge("dast", "merge")
    graph.add_edge("dependency", "merge")
    graph.add_edge("secrets", "merge")

    # Merge to gate
    graph.add_edge("merge", "gate")

    return graph.compile()
```

### State Schema

```python
class SecurityState(TypedDict):
    code_artifact: CodeArtifact
    scan_results: list[ScanFinding]
    sast_results: list[ScanFinding]
    dast_results: list[ScanFinding]
    dependency_results: list[ScanFinding]
    secrets_results: list[ScanFinding]
    license_results: list[LicenseFinding]
    gate_passed: bool
    gate_report: SecurityReport
```

---

## 2. Adding a New Security Scanner

To add a new scanner integration:

1. **Create the scanner module** in `apps/server/src/codebot/security/`:

```python
# apps/server/src/codebot/security/new_scanner.py

from codebot.security.base import BaseScanner, ScanFinding, Severity

class NewScanner(BaseScanner):
    """Integration with NewTool."""

    async def scan(self, artifact: CodeArtifact) -> list[ScanFinding]:
        result = await self._run_tool(
            cmd=["newtool", "scan", "--format", "json", artifact.path],
            timeout=300,
        )
        return self._parse_output(result.stdout)

    def _parse_output(self, raw: str) -> list[ScanFinding]:
        data = json.loads(raw)
        return [
            ScanFinding(
                scanner="newtool",
                severity=self._map_severity(item["level"]),
                title=item["rule_id"],
                description=item["message"],
                file=item["file"],
                line=item.get("line"),
                cwe=item.get("cwe"),
            )
            for item in data["findings"]
        ]
```

2. **Register in the orchestrator** — add a node and edges in
   `orchestrator.py`:

```python
graph.add_node("new_scanner", run_new_scanner)
graph.add_edge(START, "new_scanner")
graph.add_edge("new_scanner", "merge")
```

3. **Update merge logic** in the `merge_scan_results` node to include the new
   results key.

4. **Add tests** in `apps/server/src/codebot/testing/` (see section 10).

5. **Update the gate** if the scanner introduces a new finding category.

---

## 3. SAST Integration (Semgrep + SonarQube)

File: `apps/server/src/codebot/security/sast.py`

### Semgrep

- Runs with `--config auto` plus custom rule sets
- Custom rules go in `apps/server/src/codebot/security/rules/semgrep/`
- Output format: `--json`

```python
class SemgrepScanner(BaseScanner):
    async def scan(self, artifact: CodeArtifact) -> list[ScanFinding]:
        cmd = [
            "semgrep", "scan",
            "--config", "auto",
            "--config", str(self.custom_rules_dir),
            "--json",
            "--no-git-ignore",
            artifact.path,
        ]
        result = await self._run_tool(cmd=cmd, timeout=600)
        return self._parse_semgrep_json(result.stdout)
```

### Bandit (Python-Specific SAST)

- Runs Python-specific security checks (hardcoded passwords, shell injection, etc.)
- Complements Semgrep with deeper Python-specific analysis
- Output format: `--format json`

```python
class BanditScanner(BaseScanner):
    async def scan(self, artifact: CodeArtifact) -> list[ScanFinding]:
        cmd = [
            "bandit", "-r",
            "--format", "json",
            "--severity-level", "medium",
            artifact.path,
        ]
        result = await self._run_tool(cmd=cmd, timeout=300)
        return self._parse_bandit_json(result.stdout)
```

### SonarQube

- Uses `sonar-scanner` CLI with project-specific profiles
- Quality profiles configure which rules are active and at what severity
- Results fetched via SonarQube Web API after scan completes

### Adding Custom Semgrep Rules

Place YAML rule files in the rules directory:

```yaml
# rules/semgrep/no-hardcoded-tokens.yaml
rules:
  - id: no-hardcoded-tokens
    patterns:
      - pattern: $VAR = "sk-..."
    message: "Hardcoded API token detected"
    severity: ERROR
    languages: [python, javascript, typescript]
    metadata:
      cwe: ["CWE-798"]
```

---

## 4. Dependency Vulnerability Scanning

File: `apps/server/src/codebot/security/dependency.py`

### Trivy

Primary scanner for container images and filesystem dependencies.

```python
class TrivyScanner(BaseScanner):
    async def scan(self, artifact: CodeArtifact) -> list[ScanFinding]:
        cmd = [
            "trivy", "fs",
            "--format", "json",
            "--severity", "CRITICAL,HIGH,MEDIUM",
            "--exit-code", "0",  # Don't fail — gate handles pass/fail
            artifact.path,
        ]
        result = await self._run_tool(cmd=cmd, timeout=300)
        return self._parse_trivy_json(result.stdout)
```

### OpenSCA

Secondary scanner for deeper SCA (Software Composition Analysis). Covers
ecosystems that Trivy may miss.

### Key Patterns

- Always parse JSON output — never screen-scrape text output.
- Map CVE IDs and CVSS scores to the standard `ScanFinding` model.
- Set `exit-code 0` on scanner CLI — let the quality gate make pass/fail
  decisions, not the scanner process exit code.

---

## 5. Secret Detection (Gitleaks)

File: `apps/server/src/codebot/security/secrets.py`

```python
class GitleaksScanner(BaseScanner):
    async def scan(self, artifact: CodeArtifact) -> list[ScanFinding]:
        cmd = [
            "gitleaks", "detect",
            "--source", artifact.path,
            "--report-format", "json",
            "--report-path", str(self.report_path),
            "--no-git",
            "--exit-code", "0",
        ]
        await self._run_tool(cmd=cmd, timeout=120)
        return self._parse_gitleaks_report(self.report_path)
```

### Configuration

- Custom Gitleaks config: `.gitleaks.toml` at repo root or passed via
  `--config`.
- Allowlists for known-safe patterns (test fixtures, examples) go in the
  config's `[allowlist]` section.
- Secrets findings are always **CRITICAL** severity — they must be resolved
  before the gate can pass unless explicitly overridden.

---

## 6. License Compliance Scanning

File: `apps/server/src/codebot/security/license.py`

Tools: ScanCode, FOSSology, ORT (OSS Review Toolkit).

### License Policy

Define allowed/denied licenses in configuration:

```python
LICENSE_POLICY = {
    "allowed": ["MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC"],
    "restricted": ["GPL-2.0", "GPL-3.0", "AGPL-3.0"],
    "review_required": ["LGPL-2.1", "MPL-2.0", "EPL-1.0"],
}
```

### Integration Pattern

```python
class LicenseScanner(BaseScanner):
    async def scan(self, artifact: CodeArtifact) -> list[LicenseFinding]:
        # Primary: ScanCode for license identification
        licenses = await self._run_scancode(artifact)
        # Evaluate against policy
        return self._evaluate_policy(licenses)
```

- `LicenseFinding` includes: package name, detected license SPDX ID, policy
  status (allowed / restricted / review_required / unknown).
- Restricted licenses produce HIGH severity findings.
- Unknown licenses produce MEDIUM severity and require manual review.

---

## 7. DAST Integration (OWASP ZAP)

File: `apps/server/src/codebot/security/dast.py`

### OWASP ZAP (Primary DAST in S6)

OWASP ZAP runs against generated web components/endpoints to find runtime
vulnerabilities. It serves as both the S6 DAST scanner and the S7 penetration
testing tool.

```python
class ZAPScanner(BaseScanner):
    async def scan(self, artifact: CodeArtifact) -> list[ScanFinding]:
        # Start ephemeral server for the artifact
        async with artifact.serve() as url:
            cmd = [
                "zap-cli", "quick-scan",
                "--self-contained",
                "--start-options", "-config api.disablekey=true",
                "-o", "json",
                url,
            ]
            result = await self._run_tool(cmd=cmd, timeout=600)
            return self._parse_zap_json(result.stdout)
```

### ZAP Coverage

- **S6 (QA):** Active scan for OWASP Top 10, XSS, SQL injection, CSRF
- **S7 (Testing):** Full penetration test suite with authentication/authorization testing
- **Playwright integration:** Security-focused browser tests complement ZAP scans

---

## 8. Security Report Generation

File: `apps/server/src/codebot/security/report.py`

The report generator takes merged scan results and produces structured output.

```python
class SecurityReportGenerator:
    async def generate(
        self,
        findings: list[ScanFinding],
        license_findings: list[LicenseFinding],
        gate_result: GateResult,
    ) -> SecurityReport:
        return SecurityReport(
            summary=self._build_summary(findings),
            findings_by_severity=self._group_by_severity(findings),
            license_issues=license_findings,
            gate_passed=gate_result.passed,
            gate_details=gate_result.details,
            recommendations=await self._generate_recommendations(findings),
        )
```

### Report Sections

1. **Executive summary** — total findings by severity, gate pass/fail
2. **SAST findings** — static analysis issues with file/line references
3. **Dependency vulnerabilities** — CVEs with CVSS scores and fix versions
4. **Secret detections** — redacted secret locations
5. **License compliance** — policy violations
6. **DAST findings** — runtime vulnerabilities
7. **Recommendations** — AI-generated fix suggestions per finding
8. **Gate decision** — pass/fail with reasoning

---

## 9. Quality Gate Configuration

File: `apps/server/src/codebot/security/gate.py`

The GATE node evaluates merged scan results against configurable thresholds.

### Default Thresholds

```python
DEFAULT_GATE_CONFIG = GateConfig(
    max_critical=0,       # Zero critical findings allowed
    max_high=0,           # Zero high findings allowed
    max_medium=5,         # Up to 5 medium findings
    max_low=20,           # Up to 20 low findings
    block_on_secrets=True,         # Any secret = fail
    block_on_restricted_license=True,  # Restricted license = fail
)
```

### Gate Evaluation

```python
class SecurityGate:
    async def evaluate(
        self,
        findings: list[ScanFinding],
        config: GateConfig,
    ) -> GateResult:
        counts = Counter(f.severity for f in findings)
        violations: list[str] = []

        if counts[Severity.CRITICAL] > config.max_critical:
            violations.append(
                f"Critical findings: {counts[Severity.CRITICAL]} "
                f"(max {config.max_critical})"
            )
        # ... similar for HIGH, MEDIUM, LOW

        if config.block_on_secrets and any(
            f.scanner == "gitleaks" for f in findings
        ):
            violations.append("Secret detected in generated code")

        return GateResult(
            passed=len(violations) == 0,
            violations=violations,
            counts=dict(counts),
        )
```

### Override Policies

- **Per-finding suppression:** Annotate with `# nosec <rule-id>` and a
  justification. Suppressions are tracked in the report.
- **Threshold override:** Pass a custom `GateConfig` to relax thresholds for
  specific pipelines (e.g., prototype/POC mode).
- **Break-glass:** An admin override flag that logs a warning but allows the
  gate to pass. Requires audit trail entry.

---

## 10. Testing Security Integrations

Tests live in `apps/server/src/codebot/testing/`.

### Unit Tests

Mock the scanner CLI output and verify parsing:

```python
# test_sast.py

import pytest
from codebot.security.sast import SemgrepScanner

@pytest.fixture
def semgrep_output() -> str:
    return Path("fixtures/semgrep_output.json").read_text()

async def test_parse_semgrep_findings(semgrep_output: str) -> None:
    scanner = SemgrepScanner()
    findings = scanner._parse_semgrep_json(semgrep_output)
    assert len(findings) == 3
    assert findings[0].severity == Severity.HIGH
    assert findings[0].cwe == "CWE-89"
```

### Integration Tests

Run actual scanners against known-vulnerable fixtures:

```python
@pytest.mark.integration
async def test_gitleaks_detects_aws_key() -> None:
    scanner = GitleaksScanner()
    artifact = CodeArtifact(path="fixtures/vulnerable/hardcoded_key.py")
    findings = await scanner.scan(artifact)
    assert any("AWS" in f.title for f in findings)
```

### Gate Tests

```python
async def test_gate_fails_on_critical() -> None:
    findings = [ScanFinding(severity=Severity.CRITICAL, ...)]
    gate = SecurityGate()
    result = await gate.evaluate(findings, DEFAULT_GATE_CONFIG)
    assert result.passed is False
    assert "Critical findings" in result.violations[0]
```

### Pipeline End-to-End Tests

```python
@pytest.mark.e2e
async def test_full_security_pipeline() -> None:
    pipeline = security_scan_pipeline()
    state = SecurityState(code_artifact=load_fixture("sample_app"))
    result = await pipeline.ainvoke(state)
    assert "gate_passed" in result
    assert isinstance(result["gate_report"], SecurityReport)
```

---

## Code Style & Conventions

- **Python 3.12+** — use modern syntax (`type` aliases, `match` statements).
- **Async-first** — all scanner `scan()` methods are `async`.
- **Strict mypy** — no `Any` types, full type annotations on all public APIs.
- **Ruff** — formatter and linter. Run `ruff check` and `ruff format` before
  committing.
- **Error handling** — scanner failures should not crash the pipeline. Catch
  exceptions, log them, and return an empty findings list with a warning in the
  report.
- **Timeouts** — every external tool call must have a timeout. Use
  `BaseScanner._run_tool(timeout=...)`.

---

## Common Tasks Quick Reference

| Task | Where to look |
|------|--------------|
| Add a Semgrep rule | `security/rules/semgrep/*.yaml` |
| Change gate thresholds | `security/gate.py` — `DEFAULT_GATE_CONFIG` |
| Add a new scanner | New file in `security/`, register in `orchestrator.py` |
| Suppress a finding | `# nosec <rule-id>` with justification comment |
| Debug scan failures | Check scanner logs; `_run_tool` captures stderr |
| Update license policy | `security/license.py` — `LICENSE_POLICY` dict |
| Add DAST target config | `security/dast.py` — `ShannonScanner` config |
| View security reports | `security/report.py` — `SecurityReportGenerator` |

## Documentation Lookup (Context7)

Before implementing security pipeline features, use Context7 to fetch current docs:

```
mcp__plugin_context7_context7__resolve-library-id("Semgrep")
mcp__plugin_context7_context7__query-docs(id, "rules configuration Python CLI output format")

mcp__plugin_context7_context7__resolve-library-id("Trivy")
mcp__plugin_context7_context7__query-docs(id, "vulnerability scanning container image configuration")

mcp__plugin_context7_context7__resolve-library-id("Gitleaks")
mcp__plugin_context7_context7__query-docs(id, "configuration rules allowlist baseline")
```

Security tool CLI interfaces and rule formats change between versions. Always verify against Context7.
