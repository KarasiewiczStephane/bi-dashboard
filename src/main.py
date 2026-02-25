"""Entry point for the BI Dashboard application."""

from src.utils.config import config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def main() -> None:
    """Launch the Dash dashboard server."""
    from src.dashboard.app import create_app

    app = create_app()
    host = config.get("app.host", "0.0.0.0")
    port = config.get("app.port", 8050)
    debug = config.get("app.debug", False)

    logger.info("Starting BI Dashboard on %s:%s", host, port)
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()
