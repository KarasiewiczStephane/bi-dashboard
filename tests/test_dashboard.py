"""Tests for Dash application layout and components."""

import dash_bootstrap_components as dbc
from dash import html

from src.dashboard.app import create_app
from src.dashboard.components.kpi_cards import (
    _format_number,
    create_kpi_section,
    make_kpi_card,
)
from src.dashboard.layout import create_layout


class TestCreateApp:
    """Verify application factory."""

    def test_returns_dash_instance(self) -> None:
        app = create_app()
        assert app is not None
        assert app.title == "BI Dashboard Suite"

    def test_layout_set(self) -> None:
        app = create_app()
        assert app.layout is not None


class TestLayout:
    """Verify overall layout structure."""

    def test_returns_container(self) -> None:
        layout = create_layout()
        assert isinstance(layout, dbc.Container)

    def test_contains_stores(self) -> None:
        layout = create_layout()
        store_ids = []
        for child in layout.children:
            if hasattr(child, "id"):
                store_ids.append(child.id)
        assert "selected-region" in store_ids


class TestKPICards:
    """Verify KPI card rendering."""

    def test_format_number_millions(self) -> None:
        assert _format_number(1_500_000, "$") == "$1.5M"

    def test_format_number_thousands(self) -> None:
        assert _format_number(45_300, "$") == "$45.3K"

    def test_format_number_small(self) -> None:
        assert _format_number(750, "$") == "$750"

    def test_make_kpi_card(self) -> None:
        card = make_kpi_card("Revenue", "$1.5M", change_pct=12.5)
        assert isinstance(card, dbc.Card)

    def test_make_kpi_card_negative_change(self) -> None:
        card = make_kpi_card("Revenue", "$1.0M", change_pct=-5.0)
        assert isinstance(card, dbc.Card)

    def test_create_kpi_section_defaults(self) -> None:
        section = create_kpi_section()
        assert isinstance(section, dbc.Row)
        assert len(section.children) == 4

    def test_create_kpi_section_with_data(self) -> None:
        kpis = {
            "total_revenue": 1_000_000,
            "revenue_change_pct": 10.0,
            "customer_count": 5000,
            "new_customers": 200,
            "avg_order_value": 50.0,
            "transaction_count": 20000,
        }
        section = create_kpi_section(kpis)
        assert isinstance(section, dbc.Row)


class TestFilters:
    """Verify sidebar filter rendering."""

    def test_sidebar_renders(self) -> None:
        from src.dashboard.components.filters import create_sidebar

        sidebar = create_sidebar()
        assert isinstance(sidebar, html.Div)
