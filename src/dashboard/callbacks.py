"""Dash callbacks for cross-filtering, drill-down, and KPI updates.

All interactive behaviour is wired here — filter changes propagate
to every chart and KPI card through shared ``dcc.Store`` state.
Role-based access restricts visibility based on the selected role.
"""

from datetime import date, datetime
from typing import Any, Optional

from dash import Dash, Input, Output, State, no_update

from src.dashboard.components.charts import (
    _empty_figure,
    build_category_chart,
    build_cohort_heatmap,
    build_drilldown_chart,
    build_funnel_chart,
    build_region_chart,
    build_timeseries_chart,
)
from src.dashboard.components.kpi_cards import create_kpi_section
from src.dashboard.roles import filter_kpis, get_permissions
from src.data.queries import QueryLayer
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def _parse_date(value: Any) -> date:
    """Coerce a string or datetime to a ``date``.

    Args:
        value: Date-like input.

    Returns:
        A ``date`` object.
    """
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return datetime.fromisoformat(str(value).split("T")[0]).date()


def register_callbacks(app: Dash, ql: Optional[QueryLayer] = None) -> None:
    """Attach all dashboard callbacks to *app*.

    Args:
        app: The Dash application instance.
        ql: Optional QueryLayer; defaults to the module singleton.
    """
    if ql is None:
        ql = QueryLayer()

    # ------------------------------------------------------------------
    # Main callback: update KPIs + all charts on filter change
    # ------------------------------------------------------------------
    @app.callback(
        [
            Output("kpi-container", "children"),
            Output("region-chart", "figure"),
            Output("category-chart", "figure"),
            Output("timeseries-chart", "figure"),
            Output("cohort-chart", "figure"),
            Output("funnel-chart", "figure"),
        ],
        [
            Input("date-range", "start_date"),
            Input("date-range", "end_date"),
            Input("period-selector", "value"),
            Input("region-filter", "value"),
            Input("role-selector", "value"),
        ],
    )
    def update_dashboard(
        start: Any,
        end: Any,
        period: str,
        region: Optional[str],
        role: str,
    ) -> tuple:
        """Refresh every chart and KPI section when filters change."""
        try:
            start_dt = _parse_date(start)
            end_dt = _parse_date(end)
        except (ValueError, TypeError):
            return (no_update,) * 6

        perms = get_permissions(role)

        # Manager sees only their assigned region
        if not perms["view_all_regions"] and perms.get("assigned_region"):
            region = perms["assigned_region"]

        kpis = ql.get_kpis(start_dt, end_dt, region=region)
        filtered_kpis = filter_kpis(kpis, role)
        kpi_section = create_kpi_section(filtered_kpis)

        region_df = ql.get_revenue_by_region(start_dt, end_dt)
        region_fig = build_region_chart(region_df)

        cat_df = ql.get_revenue_by_category(start_dt, end_dt, region=region)
        cat_fig = build_category_chart(cat_df)

        ts_df = ql.get_revenue_time_series(
            start_dt, end_dt, granularity=period, region=region
        )
        ts_fig = build_timeseries_chart(ts_df, period)

        cohort_df = ql.get_cohort_data(start_dt, end_dt)
        cohort_fig = build_cohort_heatmap(cohort_df)

        funnel = ql.get_funnel_data(start_dt, end_dt)
        funnel_fig = build_funnel_chart(funnel)

        return (
            kpi_section,
            region_fig,
            cat_fig,
            ts_fig,
            cohort_fig,
            funnel_fig,
        )

    # ------------------------------------------------------------------
    # Drill-down: click category bar → show product breakdown
    # ------------------------------------------------------------------
    @app.callback(
        Output("drilldown-chart", "figure"),
        [
            Input("category-chart", "clickData"),
            Input("date-range", "start_date"),
            Input("date-range", "end_date"),
            Input("role-selector", "value"),
        ],
    )
    def update_drilldown(
        click_data: Any,
        start: Any,
        end: Any,
        role: str,
    ) -> Any:
        """Show product-level detail when a category bar is clicked."""
        perms = get_permissions(role)
        if not perms["drilldown_enabled"]:
            return _empty_figure("Drill-down disabled for your role")

        if click_data is None:
            return no_update

        try:
            start_dt = _parse_date(start)
            end_dt = _parse_date(end)
            category = click_data["points"][0].get("x") or click_data["points"][0].get(
                "label", ""
            )
        except (ValueError, TypeError, KeyError, IndexError):
            return no_update

        if not category:
            return no_update

        df = ql.get_revenue_by_product(start_dt, end_dt, category)
        return build_drilldown_chart(df, category)

    # ------------------------------------------------------------------
    # Cross-filter: click region bar → set region filter
    # ------------------------------------------------------------------
    @app.callback(
        Output("region-filter", "value"),
        Input("region-chart", "clickData"),
        State("region-filter", "value"),
    )
    def cross_filter_region(click_data: Any, current: Optional[str]) -> Any:
        """Toggle the region filter when a region bar is clicked."""
        if click_data is None:
            return no_update

        try:
            clicked = click_data["points"][0].get("y") or click_data["points"][0].get(
                "label", ""
            )
        except (KeyError, IndexError):
            return no_update

        if clicked == current:
            return None
        return clicked

    # ------------------------------------------------------------------
    # Role change → update store and disable export buttons
    # ------------------------------------------------------------------
    @app.callback(
        [
            Output("current-role", "data"),
            Output("export-pdf-btn", "disabled"),
            Output("export-csv-btn", "disabled"),
        ],
        Input("role-selector", "value"),
    )
    def update_role(role: str) -> tuple:
        """Store the selected role and toggle export button state."""
        perms = get_permissions(role)
        disabled = not perms["export_enabled"]
        return role, disabled, disabled
