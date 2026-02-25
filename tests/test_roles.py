"""Tests for role-based access simulation."""

from src.dashboard.roles import (
    ROLE_PERMISSIONS,
    filter_kpis,
    get_permissions,
)


class TestGetPermissions:
    """Verify permission lookups."""

    def test_admin_sees_all_regions(self) -> None:
        perms = get_permissions("Admin")
        assert perms["view_all_regions"] is True

    def test_manager_restricted_region(self) -> None:
        perms = get_permissions("Manager")
        assert perms["view_all_regions"] is False
        assert perms["assigned_region"] is not None

    def test_viewer_no_drilldown(self) -> None:
        perms = get_permissions("Viewer")
        assert perms["drilldown_enabled"] is False

    def test_viewer_no_export(self) -> None:
        perms = get_permissions("Viewer")
        assert perms["export_enabled"] is False

    def test_unknown_role_defaults_to_viewer(self) -> None:
        perms = get_permissions("Unknown")
        assert perms["drilldown_enabled"] is False

    def test_admin_export_enabled(self) -> None:
        perms = get_permissions("Admin")
        assert perms["export_enabled"] is True


class TestFilterKPIs:
    """Verify KPI filtering by role."""

    def _make_kpis(self) -> dict:
        return {
            "total_revenue": 100,
            "revenue_change_pct": 5.0,
            "customer_count": 50,
            "new_customers": 10,
            "avg_order_value": 20,
            "transaction_count": 200,
        }

    def test_admin_sees_all(self) -> None:
        kpis = self._make_kpis()
        filtered = filter_kpis(kpis, "Admin")
        assert "total_revenue" in filtered
        assert "customer_count" in filtered
        assert "avg_order_value" in filtered
        assert "transaction_count" in filtered

    def test_viewer_sees_limited(self) -> None:
        kpis = self._make_kpis()
        filtered = filter_kpis(kpis, "Viewer")
        assert "total_revenue" in filtered
        assert "transaction_count" in filtered
        assert "customer_count" not in filtered
        assert "avg_order_value" not in filtered

    def test_pct_fields_always_visible(self) -> None:
        kpis = self._make_kpis()
        filtered = filter_kpis(kpis, "Viewer")
        assert "revenue_change_pct" in filtered


class TestRolePermissions:
    """Verify the permission dictionary structure."""

    def test_all_roles_defined(self) -> None:
        assert "Admin" in ROLE_PERMISSIONS
        assert "Manager" in ROLE_PERMISSIONS
        assert "Viewer" in ROLE_PERMISSIONS

    def test_required_keys(self) -> None:
        for role, perms in ROLE_PERMISSIONS.items():
            assert "view_all_regions" in perms, f"{role} missing key"
            assert "drilldown_enabled" in perms, f"{role} missing key"
            assert "export_enabled" in perms, f"{role} missing key"
            assert "visible_kpis" in perms, f"{role} missing key"
