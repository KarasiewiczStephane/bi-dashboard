"""Sidebar filter components.

Provides the date-range picker, period selector, role dropdown,
and region/category filter controls.
"""

from datetime import date

import dash_bootstrap_components as dbc
from dash import dcc, html


def create_sidebar() -> html.Div:
    """Build the sidebar with all filter controls.

    Returns:
        An ``html.Div`` containing the sidebar content.
    """
    return html.Div(
        [
            html.H4("Filters", className="mb-3"),
            # Role selector
            html.Label("Role", className="fw-bold"),
            dcc.Dropdown(
                id="role-selector",
                options=[
                    {"label": "Admin", "value": "Admin"},
                    {"label": "Manager", "value": "Manager"},
                    {"label": "Viewer", "value": "Viewer"},
                ],
                value="Admin",
                clearable=False,
                className="mb-3",
            ),
            # Date range picker
            html.Label("Date Range", className="fw-bold"),
            dcc.DatePickerRange(
                id="date-range",
                start_date=date(2022, 1, 1),
                end_date=date(2024, 12, 31),
                min_date_allowed=date(2022, 1, 1),
                max_date_allowed=date(2024, 12, 31),
                className="mb-3",
            ),
            # Period granularity selector
            html.Label("Period", className="fw-bold"),
            dcc.Dropdown(
                id="period-selector",
                options=[
                    {"label": "Daily", "value": "day"},
                    {"label": "Weekly", "value": "week"},
                    {"label": "Monthly", "value": "month"},
                    {"label": "Quarterly", "value": "quarter"},
                    {"label": "Yearly", "value": "year"},
                ],
                value="month",
                clearable=False,
                className="mb-3",
            ),
            # Region filter
            html.Label("Region", className="fw-bold"),
            dcc.Dropdown(
                id="region-filter",
                options=[
                    {"label": r, "value": r}
                    for r in [
                        "North",
                        "South",
                        "East",
                        "West",
                        "Central",
                    ]
                ],
                value=None,
                placeholder="All Regions",
                className="mb-3",
            ),
            # Export buttons
            html.Hr(),
            dbc.Button(
                [html.I(className="fas fa-file-pdf me-2"), "Export PDF"],
                id="export-pdf-btn",
                color="danger",
                className="w-100 mb-2",
            ),
            dbc.Button(
                [html.I(className="fas fa-file-csv me-2"), "Export CSV"],
                id="export-csv-btn",
                color="success",
                className="w-100 mb-2",
            ),
            dcc.Download(id="download-pdf"),
            dcc.Download(id="download-csv"),
        ]
    )
