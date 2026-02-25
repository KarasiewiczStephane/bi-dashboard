"""Tests for CI configuration."""

from pathlib import Path

import yaml


class TestCIConfiguration:
    """Verify GitHub Actions CI workflow is valid."""

    def test_ci_file_exists(self) -> None:
        assert Path(".github/workflows/ci.yml").is_file()

    def test_ci_is_valid_yaml(self) -> None:
        content = Path(".github/workflows/ci.yml").read_text()
        parsed = yaml.safe_load(content)
        assert isinstance(parsed, dict)

    def test_ci_has_jobs(self) -> None:
        content = Path(".github/workflows/ci.yml").read_text()
        parsed = yaml.safe_load(content)
        assert "jobs" in parsed
        assert "lint" in parsed["jobs"]
        assert "test" in parsed["jobs"]

    def test_ci_triggers_on_push(self) -> None:
        content = Path(".github/workflows/ci.yml").read_text()
        parsed = yaml.safe_load(content)
        # YAML parses `on` as True; use parsed[True] or check raw content
        triggers = parsed.get("on") or parsed.get(True, {})
        assert "push" in triggers

    def test_ci_uses_python_311(self) -> None:
        content = Path(".github/workflows/ci.yml").read_text()
        assert "3.11" in content
