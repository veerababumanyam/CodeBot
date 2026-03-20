"""Unit tests for AllowlistValidator."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from codebot.security.models import AllowlistConfig
from codebot.security.scanners.allowlist import AllowlistValidator


@pytest.fixture
def config() -> AllowlistConfig:
    return AllowlistConfig(
        python_packages={"fastapi", "pydantic", "requests"},
        npm_packages={"react", "vite", "typescript"},
    )


@pytest.fixture
def validator(config: AllowlistConfig) -> AllowlistValidator:
    return AllowlistValidator(config=config)


class TestAllowlistValidatorRequirements:
    @pytest.mark.asyncio
    async def test_allows_listed_packages(
        self, validator: AllowlistValidator, tmp_path: Path
    ) -> None:
        """Known packages produce no violations."""
        req = tmp_path / "requirements.txt"
        req.write_text("fastapi==0.115.0\npydantic>=2.9.0\nrequests~=2.31\n")
        violations = await validator.validate_requirements(str(req))
        assert violations == []

    @pytest.mark.asyncio
    async def test_rejects_unknown_packages(
        self, validator: AllowlistValidator, tmp_path: Path
    ) -> None:
        """Unknown packages are flagged."""
        req = tmp_path / "requirements.txt"
        req.write_text("fastapi==0.115.0\nmalicious-pkg>=1.0\n")
        violations = await validator.validate_requirements(str(req))
        assert len(violations) == 1
        assert "malicious-pkg" in violations[0]

    @pytest.mark.asyncio
    async def test_skips_comments_and_blanks(
        self, validator: AllowlistValidator, tmp_path: Path
    ) -> None:
        """Comments and blank lines are ignored."""
        req = tmp_path / "requirements.txt"
        req.write_text("# this is a comment\n\nfastapi==0.115.0\n")
        violations = await validator.validate_requirements(str(req))
        assert violations == []

    @pytest.mark.asyncio
    async def test_skips_flags(
        self, validator: AllowlistValidator, tmp_path: Path
    ) -> None:
        """Lines starting with -r or -- are skipped."""
        req = tmp_path / "requirements.txt"
        req.write_text("-r base.txt\n--index-url https://pypi.org/simple\nfastapi\n")
        violations = await validator.validate_requirements(str(req))
        assert violations == []

    @pytest.mark.asyncio
    async def test_handles_extras(
        self, validator: AllowlistValidator, tmp_path: Path
    ) -> None:
        """Packages with extras like fastapi[all] are recognized."""
        req = tmp_path / "requirements.txt"
        req.write_text("fastapi[all]>=0.115.0\n")
        violations = await validator.validate_requirements(str(req))
        assert violations == []

    @pytest.mark.asyncio
    async def test_case_insensitive(
        self, validator: AllowlistValidator, tmp_path: Path
    ) -> None:
        """Package matching is case insensitive."""
        req = tmp_path / "requirements.txt"
        req.write_text("FastAPI==0.115.0\nPyDantic>=2.9\n")
        violations = await validator.validate_requirements(str(req))
        assert violations == []


class TestAllowlistValidatorPackageJson:
    @pytest.mark.asyncio
    async def test_allows_listed_npm_packages(
        self, validator: AllowlistValidator, tmp_path: Path
    ) -> None:
        """Known npm packages produce no violations."""
        pkg = tmp_path / "package.json"
        pkg.write_text(
            json.dumps(
                {
                    "dependencies": {"react": "^18.2.0", "vite": "^5.0.0"},
                    "devDependencies": {"typescript": "^5.5.0"},
                }
            )
        )
        violations = await validator.validate_package_json(str(pkg))
        assert violations == []

    @pytest.mark.asyncio
    async def test_rejects_unknown_npm_packages(
        self, validator: AllowlistValidator, tmp_path: Path
    ) -> None:
        """Unknown npm packages are flagged."""
        pkg = tmp_path / "package.json"
        pkg.write_text(
            json.dumps(
                {
                    "dependencies": {"react": "^18.2.0", "evil-pkg": "^1.0.0"},
                }
            )
        )
        violations = await validator.validate_package_json(str(pkg))
        assert len(violations) == 1
        assert "evil-pkg" in violations[0]

    @pytest.mark.asyncio
    async def test_missing_sections(
        self, validator: AllowlistValidator, tmp_path: Path
    ) -> None:
        """Package.json without dependencies/devDependencies is fine."""
        pkg = tmp_path / "package.json"
        pkg.write_text(json.dumps({"name": "test", "version": "1.0.0"}))
        violations = await validator.validate_package_json(str(pkg))
        assert violations == []


class TestExtractPackageName:
    def test_simple_package(self, validator: AllowlistValidator) -> None:
        assert validator._extract_package_name("fastapi") == "fastapi"

    def test_with_version_eq(self, validator: AllowlistValidator) -> None:
        assert validator._extract_package_name("fastapi==0.115.0") == "fastapi"

    def test_with_version_gte(self, validator: AllowlistValidator) -> None:
        assert validator._extract_package_name("pydantic>=2.9.0") == "pydantic"

    def test_with_extras(self, validator: AllowlistValidator) -> None:
        assert validator._extract_package_name("fastapi[all]>=0.115.0") == "fastapi"

    def test_with_env_marker(self, validator: AllowlistValidator) -> None:
        assert (
            validator._extract_package_name('requests; python_version >= "3.12"')
            == "requests"
        )

    def test_comment_returns_none(self, validator: AllowlistValidator) -> None:
        assert validator._extract_package_name("# comment") is None

    def test_blank_returns_none(self, validator: AllowlistValidator) -> None:
        assert validator._extract_package_name("") is None

    def test_flag_returns_none(self, validator: AllowlistValidator) -> None:
        assert validator._extract_package_name("-r base.txt") is None
        assert validator._extract_package_name("--index-url https://x") is None
