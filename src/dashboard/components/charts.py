"""Chart builder functions for the dashboard.

Each function returns a Plotly ``Figure`` ready to be injected
into a ``dcc.Graph`` component.
"""

from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def build_region_chart(df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart of revenue by region.

    Args:
        df: DataFrame with columns ``region`` and ``revenue``.

    Returns:
        A Plotly ``Figure``.
    """
    if df.empty:
        return _empty_figure("No region data available")

    fig = px.bar(
        df,
        x="revenue",
        y="region",
        orientation="h",
        title="Revenue by Region",
        color="revenue",
        color_continuous_scale="Blues",
    )
    fig.update_layout(
        showlegend=False,
        coloraxis_showscale=False,
        margin=dict(l=20, r=20, t=40, b=20),
        yaxis_title="",
        xaxis_title="Revenue ($)",
    )
    return fig


def build_category_chart(df: pd.DataFrame) -> go.Figure:
    """Vertical bar chart of revenue by product category.

    Args:
        df: DataFrame with columns ``category`` and ``revenue``.

    Returns:
        A Plotly ``Figure``.
    """
    if df.empty:
        return _empty_figure("No category data available")

    fig = px.bar(
        df,
        x="category",
        y="revenue",
        title="Revenue by Category",
        color="category",
    )
    fig.update_layout(
        showlegend=False,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_title="",
        yaxis_title="Revenue ($)",
    )
    return fig


def build_timeseries_chart(df: pd.DataFrame, granularity: str = "month") -> go.Figure:
    """Line chart of revenue over time.

    Args:
        df: DataFrame with columns ``period`` and ``revenue``.
        granularity: Label for x-axis context.

    Returns:
        A Plotly ``Figure``.
    """
    if df.empty:
        return _empty_figure("No time-series data available")

    fig = px.line(
        df,
        x="period",
        y="revenue",
        title=f"Revenue Trend ({granularity.title()})",
        markers=True,
    )
    fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_title="",
        yaxis_title="Revenue ($)",
    )
    return fig


def build_drilldown_chart(df: pd.DataFrame, category: str) -> go.Figure:
    """Bar chart of top products within a category.

    Args:
        df: DataFrame with columns ``name`` and ``revenue``.
        category: The category being drilled into.

    Returns:
        A Plotly ``Figure``.
    """
    if df.empty:
        return _empty_figure(f"No products for {category}")

    top = df.head(10)
    fig = px.bar(
        top,
        x="revenue",
        y="name",
        orientation="h",
        title=f"Top Products — {category}",
        color="revenue",
        color_continuous_scale="Oranges",
    )
    fig.update_layout(
        showlegend=False,
        coloraxis_showscale=False,
        margin=dict(l=20, r=20, t=40, b=20),
        yaxis_title="",
        xaxis_title="Revenue ($)",
    )
    return fig


def build_cohort_heatmap(df: pd.DataFrame) -> go.Figure:
    """Heatmap of cohort retention (signup month vs activity month).

    Args:
        df: DataFrame with columns ``cohort_month``, ``activity_month``,
            and ``active_customers``.

    Returns:
        A Plotly ``Figure``.
    """
    if df.empty:
        return _empty_figure("No cohort data available")

    pivot = df.pivot_table(
        index="cohort_month",
        columns="activity_month",
        values="active_customers",
        aggfunc="sum",
    ).fillna(0)

    fig = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=[str(c)[:7] for c in pivot.columns],
            y=[str(r)[:7] for r in pivot.index],
            colorscale="YlOrRd",
        )
    )
    fig.update_layout(
        title="Customer Cohort Retention",
        xaxis_title="Activity Month",
        yaxis_title="Signup Cohort",
        margin=dict(l=20, r=20, t=40, b=20),
    )
    return fig


def build_funnel_chart(funnel_data: list[dict[str, Any]]) -> go.Figure:
    """Funnel chart showing awareness → purchase pipeline.

    Args:
        funnel_data: List of dicts with keys ``stage`` and ``count``.

    Returns:
        A Plotly ``Figure``.
    """
    if not funnel_data:
        return _empty_figure("No funnel data available")

    fig = go.Figure(
        go.Funnel(
            y=[d["stage"] for d in funnel_data],
            x=[d["count"] for d in funnel_data],
        )
    )
    fig.update_layout(
        title="Sales Funnel",
        margin=dict(l=20, r=20, t=40, b=20),
    )
    return fig


def _empty_figure(message: str) -> go.Figure:
    """Return a blank figure with a centred annotation.

    Args:
        message: Text to display.

    Returns:
        A Plotly ``Figure`` with no data.
    """
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=14, color="grey"),
    )
    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        margin=dict(l=20, r=20, t=40, b=20),
    )
    return fig
