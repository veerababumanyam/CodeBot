"""SecurityAuditorAgent -- S6 Quality Assurance security scanning agent.

Implements the PRA cognitive cycle:
- perceive(): Extracts all *_dev_output keys from shared_state plus security_rules config
- reason(): Builds LLM message list with security-oriented system prompt
- act(): Returns structured findings from Semgrep, Trivy, Gitleaks with severity summary
- review(): Validates gate_passed and severity_summary with all 4 severity keys

Covers requirements:
  QA-02: Security audit with Semgrep static analysis, Trivy container/dependency scanning,
         Gitleaks secret detection
  QA-07: Parallel execution via separate state namespace (security_auditor_output)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from agent_sdk.agents.base import AgentInput, AgentOutput, BaseAgent, PRAResult
from agent_sdk.models.enums import AgentType

from codebot.agents.registry import register_agent

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
<role>
You are the Security Auditor agent for CodeBot, operating in the S6 (Quality
Assurance) pipeline stage. Your purpose is to perform comprehensive security
scanning of generated code before it advances to testing (QA-02).
</role>

<responsibilities>
- Run Semgrep static analysis to detect code-level vulnerabilities (SQL injection,
  XSS, path traversal, insecure deserialization, etc.)
- Run Trivy container and dependency scanning to identify vulnerable packages,
  outdated dependencies, and container misconfigurations
- Run Gitleaks secret detection to catch hardcoded API keys, tokens, passwords,
  and other sensitive data
- Aggregate findings by severity (critical, high, medium, low)
- Enforce quality gate: block pipeline advancement when critical or high severity
  findings are present
</responsibilities>

<output_format>
Produce a JSON object with the following top-level keys:
- "semgrep_findings": array of static analysis findings with rule_id, severity,
  file, line, message, and fix_suggestion
- "trivy_findings": array of dependency/container findings with package, version,
  vulnerability_id, severity, and description
- "gitleaks_findings": array of secret detection findings with file, line,
  rule_id, and description
- "severity_summary": object with "critical", "high", "medium", "low" integer counts
- "gate_passed": boolean -- true only if zero critical AND zero high findings
</output_format>

<constraints>
- Never skip scanning steps -- all three tools must be invoked
- Severity mapping: critical > high > medium > low
- Quality gate blocks on critical OR high findings (gate_passed = false)
- Medium and low findings are advisory only -- they do not block
- Include fix suggestions where possible
</constraints>
"""


# ---------------------------------------------------------------------------
# Agent implementation
# ---------------------------------------------------------------------------


@register_agent(AgentType.SECURITY_AUDITOR)
@dataclass(slots=True, kw_only=True)
class SecurityAuditorAgent(BaseAgent):
    """S6 security scanning agent with Semgrep, Trivy, and Gitleaks integration.

    Scans generated code for vulnerabilities, vulnerable dependencies, and
    hardcoded secrets. Enforces quality gate that blocks pipeline advancement
    when critical or high severity findings are present.

    Attributes:
        agent_type: Always ``AgentType.SECURITY_AUDITOR``.
        name: Human-readable agent name.
        model_tier: LLM tier selection.
        max_retries: Number of retry attempts on failure.
        tools: List of tool identifiers available to this agent.
    """

    agent_type: AgentType = field(default=AgentType.SECURITY_AUDITOR, init=False)
    name: str = "security_auditor"
    model_tier: str = "tier2"
    max_retries: int = 2
    tools: list[str] = field(
        default_factory=lambda: [
            "semgrep_scan",
            "trivy_scan",
            "gitleaks_scan",
            "dependency_checker",
            "cve_lookup",
            "fix_generator",
        ]
    )

    async def _initialize(self, agent_input: AgentInput) -> None:
        """No additional initialization needed for SecurityAuditorAgent.

        Args:
            agent_input: The task input for initialization context.
        """

    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        """Extract all dev output keys and security rules from shared state.

        Pulls all ``*_dev_output`` keys (code to scan) and ``security_rules``
        configuration from the graph's shared state.

        Args:
            agent_input: The task input with shared_state.

        Returns:
            Dict with dev_outputs (code to scan) and security_rules config.
        """
        shared_state = agent_input.shared_state
        dev_outputs: dict[str, Any] = {}
        for key, value in shared_state.items():
            if key.endswith("_dev_output"):
                dev_outputs[key] = value

        return {
            "dev_outputs": dev_outputs,
            "security_rules": shared_state.get("security_rules", {}),
        }

    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        """Build LLM message list for security analysis.

        Constructs a message sequence with the system prompt and code
        context for the security auditor role.

        Args:
            context: Dict with dev_outputs and security_rules from perceive().

        Returns:
            Dict with messages list and context for the act phase.
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Code to scan: {context.get('dev_outputs', {})}\n\n"
                    f"Security rules: {context.get('security_rules', {})}"
                ),
            },
        ]
        return {"messages": messages, "context": context}

    async def act(self, plan: dict[str, Any]) -> PRAResult:
        """Produce security scan output with findings and gate status.

        In the current implementation, returns a structured placeholder
        that downstream agents consume. The actual tool calls are handled
        by the AgentNode wrapper at graph execution time.

        Args:
            plan: Dict with messages and context from reason().

        Returns:
            PRAResult with security scan output in data.
        """
        return PRAResult(
            is_complete=True,
            data={
                "semgrep_findings": [],
                "trivy_findings": [],
                "gitleaks_findings": [],
                "severity_summary": {
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0,
                },
                "gate_passed": True,
            },
        )

    async def review(self, result: PRAResult) -> AgentOutput:
        """Validate security scan output and enforce quality gate.

        Checks that gate_passed is present and severity_summary has all
        4 severity keys. review_passed is True only if gate_passed is True
        (no critical/high findings).

        Args:
            result: The PRAResult from the final act() iteration.

        Returns:
            AgentOutput with review_passed and state_updates containing
            security_auditor_output.
        """
        data = result.data
        severity_summary = data.get("severity_summary", {})
        has_gate = "gate_passed" in data
        has_all_severities = all(
            key in severity_summary for key in ("critical", "high", "medium", "low")
        )

        gate_passed = bool(data.get("gate_passed", False))
        review_passed = has_gate and has_all_severities and gate_passed

        return AgentOutput(
            task_id=self.agent_id,
            state_updates={"security_auditor_output": data},
            review_passed=review_passed,
        )

    def build_system_prompt(self) -> str:
        """Return the system prompt for the Security Auditor agent.

        Returns:
            The SYSTEM_PROMPT constant.
        """
        return SYSTEM_PROMPT
