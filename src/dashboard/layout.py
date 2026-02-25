"""Main dashboard layout definition.

Assembles the sidebar, KPI cards, chart placeholders, and filter
stores into a responsive Bootstrap grid.
"""

import dash_bootstrap_components as dbc
from dash import dcc, html

from src.dashboard.components.filters import create_sidebar
from src.dashboard.components.kpi_cards import create_kpi_section


def create_layout() -> dbc.Container:
    """Return the top-level dashboard layout.

    Returns:
        A ``dbc.Container`` wrapping the full page structure.
    """
    return dbc.Container(
        [
            # Client-side stores for cross-filtering state
            dcc.Store(id="selected-region", data=None),
            dcc.Store(id="selected-category", data=None),
            dcc.Store(id="current-role", data="Admin"),
            dbc.Row(
                [
                    # Sidebar
                    dbc.Col(
                        create_sidebar(),
                        width=12,
                        lg=3,
                        className="bg-light p-3",
                        id="sidebar-col",
                    ),
                    # Main content
                    dbc.Col(
                        [
                            html.H1(
                                "BI Dashboard Suite",
                                className="mb-4 mt-3",
                            ),
                            # KPI cards row
                            html.Div(
                                id="kpi-container",
                                children=create_kpi_section(),
                            ),
                            # Charts row 1: region + category
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dcc.Graph(id="region-chart"),
                                        width=12,
                                        lg=6,
                                    ),
                                    dbc.Col(
                                        dcc.Graph(id="category-chart"),
                                        width=12,
                                        lg=6,
                                    ),
                                ],
                                className="mb-4",
                            ),
                            # Charts row 2: time series + drill-down
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dcc.Graph(id="timeseries-chart"),
                                        width=12,
                                        lg=6,
                                    ),
                                    dbc.Col(
                                        dcc.Graph(id="drilldown-chart"),
                                        width=12,
                                        lg=6,
                                    ),
                                ],
                                className="mb-4",
                            ),
                            # Charts row 3: cohort + funnel
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dcc.Graph(id="cohort-chart"),
                                        width=12,
                                        lg=6,
                                    ),
                                    dbc.Col(
                                        dcc.Graph(id="funnel-chart"),
                                        width=12,
                                        lg=6,
                                    ),
                                ],
                                className="mb-4",
                            ),
                        ],
                        width=12,
                        lg=9,
                    ),
                ]
            ),
        ],
        fluid=True,
    )
