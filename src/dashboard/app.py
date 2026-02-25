"""Dash application factory.

Creates and configures the main Dash application with Bootstrap
styling and callback registration.
"""

import dash_bootstrap_components as dbc
from dash import Dash

from src.utils.config import config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def create_app() -> Dash:
    """Build and return the configured Dash application.

    Returns:
        A fully initialised ``Dash`` instance with layout and callbacks.
    """
    app = Dash(
        __name__,
        external_stylesheets=[
            dbc.themes.BOOTSTRAP,
            dbc.icons.FONT_AWESOME,
        ],
        suppress_callback_exceptions=True,
        title=config.get("app.title", "BI Dashboard"),
    )

    from src.dashboard.layout import create_layout

    app.layout = create_layout()

    logger.info("Dash application created")
    return app
