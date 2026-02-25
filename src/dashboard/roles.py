"""Role-based access simulation.

Defines three roles — Admin, Manager, Viewer — with different
permissions controlling which dashboard elements are visible and
which interactions are allowed.
"""

from typing import Any

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

ROLE_PERMISSIONS: dict[str, dict[str, Any]] = {
    "Admin": {
        "view_all_regions": True,
        "drilldown_enabled": True,
        "export_enabled": True,
        "visible_kpis": [
            "total_revenue",
            "customer_count",
            "avg_order_value",
            "transaction_count",
        ],
        "assigned_region": None,
    },
    "Manager": {
        "view_all_regions": False,
        "drilldown_enabled": True,
        "export_enabled": True,
        "visible_kpis": [
            "total_revenue",
            "customer_count",
            "avg_order_value",
            "transaction_count",
        ],
        "assigned_region": "North",  # simulated assignment
    },
    "Viewer": {
        "view_all_regions": True,
        "drilldown_enabled": False,
        "export_enabled": False,
        "visible_kpis": [
            "total_revenue",
            "transaction_count",
        ],
    },
}


def get_permissions(role: str) -> dict[str, Any]:
    """Return the permission set for a given role.

    Args:
        role: One of ``"Admin"``, ``"Manager"``, ``"Viewer"``.

    Returns:
        Dict with permission flags and constraints.
    """
    perms = ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS["Viewer"])
    logger.info("Loaded permissions for role: %s", role)
    return perms


def filter_kpis(kpis: dict[str, Any], role: str) -> dict[str, Any]:
    """Remove KPI keys the role is not allowed to see.

    Args:
        kpis: Full KPI dict from ``QueryLayer.get_kpis``.
        role: Current user role.

    Returns:
        Filtered KPI dict.
    """
    perms = get_permissions(role)
    visible = set(perms["visible_kpis"])
    return {k: v for k, v in kpis.items() if k in visible or k.endswith("_pct")}
