"""PDF report generator.

Builds a weekly summary PDF with KPI metrics, revenue tables,
and embedded chart images using ReportLab.
"""

import io
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from src.data.queries import QueryLayer
from src.utils.config import config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class PDFReportGenerator:
    """Generate PDF reports from dashboard data.

    Args:
        query_layer: Optional QueryLayer instance.
    """

    def __init__(self, query_layer: Optional[QueryLayer] = None) -> None:
        self._ql = query_layer or QueryLayer()
        self._output_dir = Path(config.get("reporting.output_dir", "reports/"))
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def generate_weekly_report(
        self,
        end_date: Optional[date] = None,
        region: Optional[str] = None,
    ) -> Path:
        """Create a weekly summary PDF.

        Args:
            end_date: Report end date (defaults to today).
            region: Optional region filter.

        Returns:
            Path to the generated PDF file.
        """
        end_dt = end_date or date.today()
        start_dt = end_dt - timedelta(days=6)

        filename = f"weekly_report_{start_dt}_{end_dt}.pdf"
        filepath = self._output_dir / filename

        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=A4,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        elements = self._build_elements(start_dt, end_dt, region)
        doc.build(elements)

        logger.info("PDF report generated: %s", filepath)
        return filepath

    def generate_to_buffer(
        self,
        start_date: date,
        end_date: date,
        region: Optional[str] = None,
    ) -> bytes:
        """Render a report into an in-memory buffer.

        Args:
            start_date: Report start date.
            end_date: Report end date.
            region: Optional region filter.

        Returns:
            Raw PDF bytes.
        """
        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=A4,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )
        elements = self._build_elements(start_date, end_date, region)
        doc.build(elements)
        return buf.getvalue()

    def _build_elements(
        self,
        start_date: date,
        end_date: date,
        region: Optional[str],
    ) -> list[Any]:
        """Assemble the Platypus flowables for the report.

        Args:
            start_date: Report start date.
            end_date: Report end date.
            region: Optional region filter.

        Returns:
            List of ReportLab flowables.
        """
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Title"],
            fontSize=20,
            spaceAfter=20,
        )
        heading_style = ParagraphStyle(
            "ReportHeading",
            parent=styles["Heading2"],
            spaceAfter=10,
        )

        elements: list[Any] = []

        # Title
        region_label = f" — {region}" if region else ""
        elements.append(
            Paragraph(
                f"Weekly Report{region_label}",
                title_style,
            )
        )
        elements.append(
            Paragraph(
                f"Period: {start_date} to {end_date}",
                styles["Normal"],
            )
        )
        elements.append(Spacer(1, 20))

        # KPI section
        elements.append(Paragraph("Key Metrics", heading_style))
        kpis = self._ql.get_kpis(start_date, end_date, region=region)
        kpi_data = [
            ["Metric", "Value"],
            ["Total Revenue", f"${kpis['total_revenue']:,.2f}"],
            ["Revenue Change", f"{kpis['revenue_change_pct']}%"],
            ["Customers", str(kpis["customer_count"])],
            ["New Customers", str(kpis["new_customers"])],
            ["Avg Order Value", f"${kpis['avg_order_value']:,.2f}"],
            ["Transactions", str(kpis["transaction_count"])],
        ]
        kpi_table = Table(kpi_data, colWidths=[2.5 * inch, 2.5 * inch])
        kpi_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ALIGN", (1, 1), (1, -1), "RIGHT"),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor("#D9E2F3")],
                    ),
                ]
            )
        )
        elements.append(kpi_table)
        elements.append(Spacer(1, 20))

        # Revenue by region
        elements.append(Paragraph("Revenue by Region", heading_style))
        region_df = self._ql.get_revenue_by_region(start_date, end_date)
        if not region_df.empty:
            region_data = [["Region", "Revenue", "Transactions"]]
            for _, row in region_df.iterrows():
                region_data.append(
                    [
                        str(row["region"]),
                        f"${float(row['revenue']):,.2f}",
                        str(int(row["transaction_count"])),
                    ]
                )
            region_table = Table(
                region_data,
                colWidths=[2 * inch, 2 * inch, 1.5 * inch],
            )
            region_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                    ]
                )
            )
            elements.append(region_table)

        return elements
