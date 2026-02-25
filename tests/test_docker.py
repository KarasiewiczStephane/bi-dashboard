"""Tests for Docker configuration."""

from pathlib import Path


class TestDockerConfiguration:
    """Verify Docker-related files are valid."""

    def test_dockerfile_exists(self) -> None:
        assert Path("Dockerfile").is_file()

    def test_dockerignore_exists(self) -> None:
        assert Path(".dockerignore").is_file()

    def test_dockerfile_exposes_port(self) -> None:
        content = Path("Dockerfile").read_text()
        assert "EXPOSE 8050" in content

    def test_dockerfile_copies_assets(self) -> None:
        content = Path("Dockerfile").read_text()
        assert "COPY assets/" in content
        assert "COPY templates/" in content

    def test_dockerfile_healthcheck(self) -> None:
        content = Path("Dockerfile").read_text()
        assert "HEALTHCHECK" in content

    def test_dockerignore_excludes_venv(self) -> None:
        content = Path(".dockerignore").read_text()
        assert ".venv/" in content
