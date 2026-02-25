"""Entry point for the BI Dashboard application."""

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def main() -> None:
    """Launch the dashboard application."""
    logger.info("Starting BI Dashboard Suite")


if __name__ == "__main__":
    main()
