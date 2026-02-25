"""Tests for chart builder functions."""

import pandas as pd
import plotly.graph_objects as go

from src.dashboard.components.charts import (
    _empty_figure,
    build_category_chart,
    build_cohort_heatmap,
    build_drilldown_chart,
    build_funnel_chart,
    build_region_chart,
    build_timeseries_chart,
)


class TestRegionChart:
    """Revenue-by-region bar chart."""

    def test_returns_figure(self) -> None:
        df = pd.DataFrame({"region": ["North", "South"], "revenue": [100, 200]})
        fig = build_region_chart(df)
        assert isinstance(fig, go.Figure)

    def test_empty_df(self) -> None:
        fig = build_region_chart(pd.DataFrame())
        assert isinstance(fig, go.Figure)


class TestCategoryChart:
    """Revenue-by-category bar chart."""

    def test_returns_figure(self) -> None:
        df = pd.DataFrame({"category": ["Electronics", "Food"], "revenue": [300, 150]})
        fig = build_category_chart(df)
        assert isinstance(fig, go.Figure)

    def test_empty_df(self) -> None:
        fig = build_category_chart(pd.DataFrame())
        assert isinstance(fig, go.Figure)


class TestTimeseriesChart:
    """Revenue time series line chart."""

    def test_returns_figure(self) -> None:
        df = pd.DataFrame(
            {
                "period": pd.date_range("2023-01-01", periods=3, freq="ME"),
                "revenue": [1000, 1100, 1200],
            }
        )
        fig = build_timeseries_chart(df, "month")
        assert isinstance(fig, go.Figure)

    def test_empty_df(self) -> None:
        fig = build_timeseries_chart(pd.DataFrame())
        assert isinstance(fig, go.Figure)


class TestDrilldownChart:
    """Product drill-down chart."""

    def test_returns_figure(self) -> None:
        df = pd.DataFrame({"name": ["Prod A", "Prod B"], "revenue": [500, 300]})
        fig = build_drilldown_chart(df, "Electronics")
        assert isinstance(fig, go.Figure)

    def test_empty_df(self) -> None:
        fig = build_drilldown_chart(pd.DataFrame(), "Electronics")
        assert isinstance(fig, go.Figure)


class TestCohortHeatmap:
    """Cohort retention heatmap."""

    def test_returns_figure(self) -> None:
        df = pd.DataFrame(
            {
                "cohort_month": ["2023-01", "2023-01", "2023-02"],
                "activity_month": ["2023-01", "2023-02", "2023-02"],
                "active_customers": [100, 80, 50],
            }
        )
        fig = build_cohort_heatmap(df)
        assert isinstance(fig, go.Figure)

    def test_empty_df(self) -> None:
        fig = build_cohort_heatmap(pd.DataFrame())
        assert isinstance(fig, go.Figure)


class TestFunnelChart:
    """Sales funnel chart."""

    def test_returns_figure(self) -> None:
        data = [
            {"stage": "Awareness", "count": 1000},
            {"stage": "Purchase", "count": 200},
        ]
        fig = build_funnel_chart(data)
        assert isinstance(fig, go.Figure)

    def test_empty_data(self) -> None:
        fig = build_funnel_chart([])
        assert isinstance(fig, go.Figure)


class TestEmptyFigure:
    """Utility empty figure builder."""

    def test_returns_figure(self) -> None:
        fig = _empty_figure("Test message")
        assert isinstance(fig, go.Figure)
