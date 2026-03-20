"""Unit tests for S6 QA agents: SecurityAuditor, Accessibility, Performance, I18nL10n.

Tests cover:
- Agent type identification and BaseAgent inheritance
- Review logic (pass/fail with valid/invalid output)
- Security gate blocking on critical findings
- Distinct state_updates keys for parallel execution (QA-07)
- YAML config loading
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import pytest
import yaml
from agent_sdk.agents.base import AgentInput, AgentOutput, BaseAgent, PRAResult
from agent_sdk.models.enums import AgentType

from codebot.agents.accessibility import AccessibilityAgent
from codebot.agents.i18n_l10n import I18nL10nAgent
from codebot.agents.performance import PerformanceAgent
from codebot.agents.security_auditor import SecurityAuditorAgent

PROJECT_ROOT = Path(__file__).resolve().parents[3]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def security_agent() -> SecurityAuditorAgent:
    """Create a SecurityAuditorAgent instance."""
    return SecurityAuditorAgent()


@pytest.fixture
def accessibility_agent() -> AccessibilityAgent:
    """Create an AccessibilityAgent instance."""
    return AccessibilityAgent()


@pytest.fixture
def performance_agent() -> PerformanceAgent:
    """Create a PerformanceAgent instance."""
    return PerformanceAgent()


@pytest.fixture
def i18n_agent() -> I18nL10nAgent:
    """Create an I18nL10nAgent instance."""
    return I18nL10nAgent()


@pytest.fixture
def agent_input() -> AgentInput:
    """Create a standard AgentInput with dev outputs in shared state."""
    return AgentInput(
        task_id=uuid.uuid4(),
        shared_state={
            "backend_dev_output": {"files": ["main.py"]},
            "frontend_dev_output": {"files": ["App.tsx"]},
            "mobile_dev_output": {"files": ["index.tsx"]},
            "designer_output": {"theme": "dark"},
            "architect_output": {"pattern": "MVC"},
            "security_rules": {"block_on_critical": True},
        },
        context_tiers={},
    )


# ---------------------------------------------------------------------------
# SecurityAuditorAgent
# ---------------------------------------------------------------------------


class TestSecurityAuditorAgentType:
    """SecurityAuditorAgent has correct type and inheritance."""

    def test_security_auditor_agent_type(self, security_agent: SecurityAuditorAgent) -> None:
        """agent_type is SECURITY_AUDITOR."""
        assert security_agent.agent_type == AgentType.SECURITY_AUDITOR

    def test_security_auditor_extends_base_agent(self, security_agent: SecurityAuditorAgent) -> None:
        """SecurityAuditorAgent is a subclass of BaseAgent."""
        assert isinstance(security_agent, BaseAgent)


class TestSecurityAuditorReview:
    """SecurityAuditorAgent.review() validates output and enforces gate."""

    async def test_security_auditor_review_passes_with_valid_output(
        self, security_agent: SecurityAuditorAgent
    ) -> None:
        """review() returns review_passed=True when gate_passed is True."""
        pra_result = PRAResult(
            is_complete=True,
            data={
                "semgrep_findings": [],
                "trivy_findings": [],
                "gitleaks_findings": [],
                "severity_summary": {"critical": 0, "high": 0, "medium": 2, "low": 5},
                "gate_passed": True,
            },
        )
        output = await security_agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is True

    async def test_security_auditor_review_fails_with_invalid_output(
        self, security_agent: SecurityAuditorAgent
    ) -> None:
        """review() returns review_passed=False when required keys missing."""
        pra_result = PRAResult(
            is_complete=True,
            data={},
        )
        output = await security_agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is False

    async def test_security_auditor_gate_blocks_on_critical(
        self, security_agent: SecurityAuditorAgent
    ) -> None:
        """review() returns review_passed=False when gate_passed is False."""
        pra_result = PRAResult(
            is_complete=True,
            data={
                "semgrep_findings": [{"rule_id": "sql-injection", "severity": "critical"}],
                "trivy_findings": [],
                "gitleaks_findings": [],
                "severity_summary": {"critical": 1, "high": 0, "medium": 0, "low": 0},
                "gate_passed": False,
            },
        )
        output = await security_agent.review(pra_result)
        assert output.review_passed is False

    async def test_security_auditor_gate_passes_when_clean(
        self, security_agent: SecurityAuditorAgent
    ) -> None:
        """review() returns review_passed=True when no critical/high findings."""
        pra_result = PRAResult(
            is_complete=True,
            data={
                "semgrep_findings": [],
                "trivy_findings": [],
                "gitleaks_findings": [],
                "severity_summary": {"critical": 0, "high": 0, "medium": 2, "low": 5},
                "gate_passed": True,
            },
        )
        output = await security_agent.review(pra_result)
        assert output.review_passed is True


class TestSecurityAuditorTools:
    """SecurityAuditorAgent has expected tools."""

    def test_tools_include_semgrep_scan(self, security_agent: SecurityAuditorAgent) -> None:
        """tools list includes semgrep_scan."""
        assert "semgrep_scan" in security_agent.tools

    def test_tools_include_trivy_scan(self, security_agent: SecurityAuditorAgent) -> None:
        """tools list includes trivy_scan."""
        assert "trivy_scan" in security_agent.tools

    def test_tools_include_gitleaks_scan(self, security_agent: SecurityAuditorAgent) -> None:
        """tools list includes gitleaks_scan."""
        assert "gitleaks_scan" in security_agent.tools


# ---------------------------------------------------------------------------
# AccessibilityAgent
# ---------------------------------------------------------------------------


class TestAccessibilityAgentType:
    """AccessibilityAgent has correct type and inheritance."""

    def test_accessibility_agent_type(self, accessibility_agent: AccessibilityAgent) -> None:
        """agent_type is ACCESSIBILITY_AUDITOR."""
        assert accessibility_agent.agent_type == AgentType.ACCESSIBILITY_AUDITOR

    def test_accessibility_extends_base_agent(self, accessibility_agent: AccessibilityAgent) -> None:
        """AccessibilityAgent is a subclass of BaseAgent."""
        assert isinstance(accessibility_agent, BaseAgent)


class TestAccessibilityReview:
    """AccessibilityAgent.review() validates output."""

    async def test_accessibility_review_passes_with_valid_output(
        self, accessibility_agent: AccessibilityAgent
    ) -> None:
        """review() returns review_passed=True when required keys present."""
        pra_result = PRAResult(
            is_complete=True,
            data={
                "wcag_violations": [],
                "lighthouse_score": 95.0,
                "color_contrast_issues": [],
                "aria_issues": [],
                "recommendations": [],
            },
        )
        output = await accessibility_agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is True

    async def test_accessibility_review_fails_with_invalid_output(
        self, accessibility_agent: AccessibilityAgent
    ) -> None:
        """review() returns review_passed=False when required keys missing."""
        pra_result = PRAResult(
            is_complete=True,
            data={},
        )
        output = await accessibility_agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is False


class TestAccessibilityTools:
    """AccessibilityAgent has expected tools."""

    def test_tools_include_axe_core(self, accessibility_agent: AccessibilityAgent) -> None:
        """tools list includes axe_core."""
        assert "axe_core" in accessibility_agent.tools


# ---------------------------------------------------------------------------
# PerformanceAgent
# ---------------------------------------------------------------------------


class TestPerformanceAgentType:
    """PerformanceAgent has correct type and inheritance."""

    def test_performance_agent_type(self, performance_agent: PerformanceAgent) -> None:
        """agent_type is PERFORMANCE_TESTER."""
        assert performance_agent.agent_type == AgentType.PERFORMANCE_TESTER

    def test_performance_extends_base_agent(self, performance_agent: PerformanceAgent) -> None:
        """PerformanceAgent is a subclass of BaseAgent."""
        assert isinstance(performance_agent, BaseAgent)


class TestPerformanceReview:
    """PerformanceAgent.review() validates output."""

    async def test_performance_review_passes_with_valid_output(
        self, performance_agent: PerformanceAgent
    ) -> None:
        """review() returns review_passed=True when required keys present."""
        pra_result = PRAResult(
            is_complete=True,
            data={
                "bottlenecks": [],
                "optimization_suggestions": [{"category": "general", "description": "optimize"}],
            },
        )
        output = await performance_agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is True

    async def test_performance_review_fails_with_invalid_output(
        self, performance_agent: PerformanceAgent
    ) -> None:
        """review() returns review_passed=False when required keys missing."""
        pra_result = PRAResult(
            is_complete=True,
            data={},
        )
        output = await performance_agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is False


# ---------------------------------------------------------------------------
# I18nL10nAgent
# ---------------------------------------------------------------------------


class TestI18nAgentType:
    """I18nL10nAgent has correct type and inheritance."""

    def test_i18n_agent_type(self, i18n_agent: I18nL10nAgent) -> None:
        """agent_type is I18N_SPECIALIST."""
        assert i18n_agent.agent_type == AgentType.I18N_SPECIALIST

    def test_i18n_extends_base_agent(self, i18n_agent: I18nL10nAgent) -> None:
        """I18nL10nAgent is a subclass of BaseAgent."""
        assert isinstance(i18n_agent, BaseAgent)


class TestI18nReview:
    """I18nL10nAgent.review() validates output."""

    async def test_i18n_review_passes_with_valid_output(
        self, i18n_agent: I18nL10nAgent
    ) -> None:
        """review() returns review_passed=True when required keys present."""
        pra_result = PRAResult(
            is_complete=True,
            data={
                "hardcoded_strings": [],
                "completeness_score": 95.0,
            },
        )
        output = await i18n_agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is True

    async def test_i18n_review_fails_with_invalid_output(
        self, i18n_agent: I18nL10nAgent
    ) -> None:
        """review() returns review_passed=False when required keys missing."""
        pra_result = PRAResult(
            is_complete=True,
            data={},
        )
        output = await i18n_agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is False


# ---------------------------------------------------------------------------
# Cross-agent: distinct state_updates keys (QA-07)
# ---------------------------------------------------------------------------


class TestAllS6AgentsDistinctStateKeys:
    """All S6 QA agents write to different state_updates keys."""

    async def test_all_s6_agents_write_different_state_keys(
        self,
        security_agent: SecurityAuditorAgent,
        accessibility_agent: AccessibilityAgent,
        performance_agent: PerformanceAgent,
        i18n_agent: I18nL10nAgent,
    ) -> None:
        """Each S6 agent writes to a unique state_updates key."""
        valid_pra = PRAResult(
            is_complete=True,
            data={
                "semgrep_findings": [],
                "trivy_findings": [],
                "gitleaks_findings": [],
                "severity_summary": {"critical": 0, "high": 0, "medium": 0, "low": 0},
                "gate_passed": True,
                "wcag_violations": [],
                "lighthouse_score": 100.0,
                "bottlenecks": [],
                "optimization_suggestions": [{"desc": "x"}],
                "hardcoded_strings": [],
                "completeness_score": 100.0,
            },
        )

        sec_output = await security_agent.review(valid_pra)
        acc_output = await accessibility_agent.review(valid_pra)
        perf_output = await performance_agent.review(valid_pra)
        i18n_output = await i18n_agent.review(valid_pra)

        keys = set()
        keys.update(sec_output.state_updates.keys())
        keys.update(acc_output.state_updates.keys())
        keys.update(perf_output.state_updates.keys())
        keys.update(i18n_output.state_updates.keys())

        expected = {
            "security_auditor_output",
            "accessibility_output",
            "performance_output",
            "i18n_output",
        }
        assert keys == expected


# ---------------------------------------------------------------------------
# YAML config loading
# ---------------------------------------------------------------------------


class TestYAMLConfigsLoad:
    """YAML configs load and validate for all 4 QA agents."""

    def test_security_auditor_yaml_loads(self) -> None:
        """security_auditor.yaml parses and has correct agent_type."""
        config_path = PROJECT_ROOT / "configs" / "agents" / "security_auditor.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        assert config["security_auditor"]["agent_type"] == "SECURITY_AUDITOR"

    def test_accessibility_yaml_loads(self) -> None:
        """accessibility.yaml parses and has correct agent_type."""
        config_path = PROJECT_ROOT / "configs" / "agents" / "accessibility.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        assert config["accessibility"]["agent_type"] == "ACCESSIBILITY_AUDITOR"

    def test_performance_yaml_loads(self) -> None:
        """performance.yaml parses and has correct agent_type."""
        config_path = PROJECT_ROOT / "configs" / "agents" / "performance.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        assert config["performance"]["agent_type"] == "PERFORMANCE_TESTER"

    def test_i18n_l10n_yaml_loads(self) -> None:
        """i18n_l10n.yaml parses and has correct agent_type."""
        config_path = PROJECT_ROOT / "configs" / "agents" / "i18n_l10n.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        assert config["i18n_l10n"]["agent_type"] == "I18N_SPECIALIST"
