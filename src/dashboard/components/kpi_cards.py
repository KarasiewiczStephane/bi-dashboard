"""KPI card components with conditional formatting.

Renders revenue, customer count, average order value, and growth
metrics as Bootstrap cards with colour-coded change indicators.
"""

from typing import Any

import dash_bootstrap_components as dbc
from dash import html


def _format_number(value: float, prefix: str = "") -> str:
    """Human-friendly number formatting (e.g. 1.2M, 45.3K).

    Args:
        value: Raw numeric value.
        prefix: Currency or unit prefix.

    Returns:
        Formatted string.
    """
    if abs(value) >= 1_000_000:
        return f"{prefix}{value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"{prefix}{value / 1_000:.1f}K"
    return f"{prefix}{value:,.0f}"


def _change_badge(pct: float) -> dbc.Badge:
    """Return a coloured badge showing the percentage change.

    Args:
        pct: Percentage change value.

    Returns:
        A ``dbc.Badge`` component coloured green (positive) or red.
    """
    colour = "success" if pct >= 0 else "danger"
    arrow = "\u25b2" if pct >= 0 else "\u25bc"
    return dbc.Badge(
        f"{arrow} {abs(pct):.1f}%",
        color=colour,
        className="ms-2",
    )


def make_kpi_card(
    title: str,
    value: str,
    change_pct: float | None = None,
    subtitle: str = "",
) -> dbc.Card:
    """Build a single KPI card.

    Args:
        title: Card heading.
        value: Formatted primary metric string.
        change_pct: Optional period-over-period change percentage.
        subtitle: Extra detail line beneath the value.

    Returns:
        A ``dbc.Card`` component.
    """
    body_children: list[Any] = [
        html.H6(title, className="text-muted"),
        html.H3(
            [
                value,
                _change_badge(change_pct) if change_pct is not None else "",
            ]
        ),
    ]
    if subtitle:
        body_children.append(html.Small(subtitle, className="text-muted"))

    return dbc.Card(
        dbc.CardBody(body_children),
        className="shadow-sm",
    )


def create_kpi_section(
    kpis: dict[str, Any] | None = None,
) -> dbc.Row:
    """Build the full KPI card row.

    Args:
        kpis: Optional pre-computed KPI dict (keys match QueryLayer output).
              If ``None``, placeholder cards are rendered.

    Returns:
        A ``dbc.Row`` of KPI cards.
    """
    if kpis is None:
        kpis = {
            "total_revenue": 0,
            "revenue_change_pct": 0,
            "customer_count": 0,
            "new_customers": 0,
            "avg_order_value": 0,
            "transaction_count": 0,
        }

    cards = [
        dbc.Col(
            make_kpi_card(
                "Total Revenue",
                _format_number(kpis.get("total_revenue", 0), "$"),
                kpis.get("revenue_change_pct"),
            ),
            width=12,
            sm=6,
            lg=3,
            className="mb-3",
        ),
        dbc.Col(
            make_kpi_card(
                "Customers",
                _format_number(kpis.get("customer_count", 0)),
                subtitle=f"{kpis.get('new_customers', 0)} new",
            ),
            width=12,
            sm=6,
            lg=3,
            className="mb-3",
        ),
        dbc.Col(
            make_kpi_card(
                "Avg Order Value",
                _format_number(kpis.get("avg_order_value", 0), "$"),
            ),
            width=12,
            sm=6,
            lg=3,
            className="mb-3",
        ),
        dbc.Col(
            make_kpi_card(
                "Transactions",
                _format_number(kpis.get("transaction_count", 0)),
            ),
            width=12,
            sm=6,
            lg=3,
            className="mb-3",
        ),
    ]

    return dbc.Row(cards, className="mb-4")
