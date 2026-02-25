"""Tests for project setup — config and logger modules."""

import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from src.utils.config import Config
from src.utils.logger import setup_logger


class TestConfig:
    """Unit tests for the Config singleton."""

    def setup_method(self) -> None:
        """Reset singleton between tests."""
        Config._instance = None
        Config._config = {}

    def test_loads_yaml(self) -> None:
        cfg = Config()
        assert cfg.get("app.title") == "BI Dashboard Suite"

    def test_nested_key_access(self) -> None:
        cfg = Config()
        assert cfg.get("app.port") == 8050

    def test_default_value(self) -> None:
        cfg = Config()
        assert cfg.get("nonexistent.key", 42) == 42

    def test_top_level_key(self) -> None:
        cfg = Config()
        app = cfg.get("app")
        assert isinstance(app, dict)
        assert "title" in app

    def test_missing_file_returns_defaults(self, tmp_path: Path) -> None:
        with patch("src.utils.config.Path") as mock_path:
            mock_path.return_value.exists.return_value = False
            Config._instance = None
            Config._config = {}
            cfg = Config()
            assert cfg.get("app.title", "fallback") == "fallback"

    def test_reload(self) -> None:
        cfg = Config()
        original = cfg.get("app.port")
        cfg.reload()
        assert cfg.get("app.port") == original


class TestLogger:
    """Unit tests for the logger factory."""

    def test_creates_logger(self) -> None:
        logger = setup_logger("test_logger")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"

    def test_logger_level(self) -> None:
        logger = setup_logger("test_level", logging.DEBUG)
        assert logger.level == logging.DEBUG

    def test_has_handler(self) -> None:
        logger = setup_logger("test_handler")
        assert len(logger.handlers) >= 1

    def test_no_duplicate_handlers(self) -> None:
        name = "test_no_dup"
        setup_logger(name)
        setup_logger(name)
        logger = logging.getLogger(name)
        assert len(logger.handlers) == 1


class TestProjectStructure:
    """Verify the expected directory structure exists."""

    @pytest.mark.parametrize(
        "path",
        [
            "src/",
            "src/data/",
            "src/utils/",
            "src/dashboard/",
            "src/dashboard/components/",
            "src/reporting/",
            "configs/",
            "tests/",
            "templates/",
            "assets/",
        ],
    )
    def test_directory_exists(self, path: str) -> None:
        assert Path(path).is_dir(), f"Directory {path} should exist"

    @pytest.mark.parametrize(
        "path",
        [
            "configs/config.yaml",
            "requirements.txt",
            "src/utils/config.py",
            "src/utils/logger.py",
            "src/main.py",
        ],
    )
    def test_file_exists(self, path: str) -> None:
        assert Path(path).is_file(), f"File {path} should exist"
