"""Configuration management module.

Provides a singleton Config class that loads settings from a YAML file
and supports dot-notation key access for nested values.
"""

from pathlib import Path
from typing import Any

import yaml


class Config:
    """Singleton configuration manager backed by a YAML file.

    Loads ``configs/config.yaml`` on first instantiation and caches the
    parsed dictionary for the lifetime of the process.

    Example::

        from src.utils.config import config

        port = config.get("app.port", 8050)
    """

    _instance: "Config | None" = None
    _config: dict[str, Any] = {}

    def __new__(cls) -> "Config":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self) -> None:
        """Read and parse the YAML configuration file."""
        config_path = Path("configs/config.yaml")
        if config_path.exists():
            with open(config_path) as fh:
                self._config = yaml.safe_load(fh) or {}

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value using dot-separated keys.

        Args:
            key: Dot-separated path (e.g. ``"app.port"``).
            default: Fallback returned when the key is missing.

        Returns:
            The resolved value, or *default* if not found.
        """
        value: Any = self._config
        for part in key.split("."):
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return default
        return value if value is not None else default

    def reload(self) -> None:
        """Re-read the YAML file (useful in tests)."""
        self._load_config()


config = Config()
