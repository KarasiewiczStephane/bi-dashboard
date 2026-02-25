"""Tests for mobile-responsive layout features."""

from pathlib import Path

import dash_bootstrap_components as dbc

from src.dashboard.layout import create_layout


class TestResponsiveLayout:
    """Verify responsive grid breakpoints in the layout."""

    def test_sidebar_has_lg_breakpoint(self) -> None:
        layout = create_layout()
        row = layout.children[3]  # Row with sidebar + main
        sidebar_col = row.children[0]
        assert sidebar_col.lg == 3
        assert sidebar_col.width == 12  # full width on mobile

    def test_chart_cols_stack_on_mobile(self) -> None:
        layout = create_layout()
        row = layout.children[3]
        main_col = row.children[1]
        chart_rows = [c for c in main_col.children if isinstance(c, dbc.Row)]
        for chart_row in chart_rows:
            for col in chart_row.children:
                assert col.width == 12  # full width on mobile

    def test_assets_css_exists(self) -> None:
        assert Path("assets/styles.css").is_file()

    def test_css_has_media_queries(self) -> None:
        css = Path("assets/styles.css").read_text()
        assert "@media" in css
        assert "max-width" in css
