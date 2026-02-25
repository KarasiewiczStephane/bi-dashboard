# BI Dashboard Suite

> Part of my Data Science Portfolio — [KarasiewiczStephane](https://github.com/KarasiewiczStephane)

## Overview

An interactive business intelligence dashboard built with **Plotly Dash** and **DuckDB**. It generates synthetic retail data, runs analytical queries against an embedded analytical database, and renders live KPI cards, drill-down charts, cohort heatmaps, and funnel visualisations — all inside a responsive single-page app.

Key capabilities:

- **KPI cards** with period-over-period change badges
- **Cross-filtering** — click a region bar to filter every other chart
- **Drill-down** — click a category to see its product breakdown
- **Role-based access** — Admin / Manager / Viewer roles control visible metrics, regions, and export permissions
- **PDF & CSV export** — download reports directly from the dashboard
- **Mobile-responsive** layout with collapsible sidebar

## Architecture

```
┌────────────────────────────────────────────────┐
│               Plotly Dash Frontend              │
│  ┌──────────┐ ┌──────────┐ ┌────────────────┐ │
│  │ KPI Cards│ │ Charts   │ │ Sidebar Filters│ │
│  └──────────┘ └──────────┘ └────────────────┘ │
├────────────────────────────────────────────────┤
│            Callbacks / Role Engine              │
├────────────────────────────────────────────────┤
│               SQL Query Layer                   │
├────────────────────────────────────────────────┤
│              DuckDB (embedded)                  │
│   dim_time ─ dim_product ─ dim_customer         │
│              fact_sales                         │
│   agg_daily_region ─ agg_daily_category         │
└────────────────────────────────────────────────┘
```

Data flows bottom-up: the **synthetic data generator** populates dimension and fact tables in DuckDB, pre-computed aggregation tables speed up common queries, the **query layer** exposes typed Python methods, and **Dash callbacks** wire everything to the UI.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Plotly Dash, Dash Bootstrap Components |
| Charting | Plotly.js (bar, line, heatmap, funnel) |
| Database | DuckDB (in-process OLAP) |
| Reports | ReportLab (PDF), CSV via pandas |
| Config | PyYAML, python-dotenv |
| Testing | pytest, pytest-cov (85 %+ coverage) |
| Linting | ruff, pre-commit |
| CI/CD | GitHub Actions (lint → test → docker) |
| Container | Docker (Python 3.11-slim) |

## Setup

### Prerequisites

- Python 3.11+
- pip

### Install

```bash
git clone git@github.com:KarasiewiczStephane/bi-dashboard.git
cd bi-dashboard
pip install -r requirements.txt
```

### Generate sample data

```bash
make generate-data
```

This creates `data/bi_dashboard.duckdb` with ~100 000 synthetic transactions spanning 2022-2024.

### Run the dashboard

```bash
make run
```

Open [http://localhost:8050](http://localhost:8050) in your browser.

### Docker

```bash
make docker-build
make docker-run
```

## Usage

### Role simulation

Select a role from the sidebar dropdown:

| Role | Regions | Drill-down | Export | KPI visibility |
|------|---------|-----------|--------|---------------|
| Admin | All | Yes | Yes | Full |
| Manager | Assigned only | Yes | Yes | Full |
| Viewer | All (read-only) | No | No | Limited |

### Cross-filtering

Click any bar on the **Revenue by Region** chart. All other charts and KPI cards update to reflect that region. Click the same bar again to clear the filter.

### Drill-down

Click a bar on the **Revenue by Category** chart to see the top products within that category.

### Exports

- **Download CSV** — exports a sales summary (KPIs, region breakdown, category breakdown).
- **Download PDF** — generates a formatted weekly report with tables.

## Project Structure

```
bi-dashboard/
├── assets/                  # CSS (responsive styles)
├── configs/
│   └── config.yaml          # App, data, reporting, logging config
├── src/
│   ├── main.py              # Entry point
│   ├── data/
│   │   ├── database.py      # DuckDB connection & schema
│   │   ├── generator.py     # Synthetic data generator
│   │   └── queries.py       # SQL query layer
│   ├── dashboard/
│   │   ├── app.py           # Dash app factory
│   │   ├── layout.py        # Page layout
│   │   ├── callbacks.py     # Interactivity & cross-filtering
│   │   ├── roles.py         # Role-based access control
│   │   └── components/
│   │       ├── charts.py    # Chart builders
│   │       ├── filters.py   # Sidebar filters
│   │       └── kpi_cards.py # KPI card components
│   ├── reporting/
│   │   ├── csv_export.py    # CSV exporter
│   │   └── pdf_generator.py # PDF report generator
│   └── utils/
│       ├── config.py        # Config singleton (YAML)
│       └── logger.py        # Structured logging setup
├── templates/               # Report HTML templates
├── tests/                   # Unit + integration tests
├── .github/workflows/
│   └── ci.yml               # GitHub Actions pipeline
├── Dockerfile
├── Makefile
├── requirements.txt
└── pyproject.toml
```

## Development

```bash
# Lint & format
make lint

# Run tests with coverage
make test

# Pre-commit hooks (auto-installed)
pre-commit install
pre-commit run --all-files
```

### Configuration

All tuneable values live in `configs/config.yaml`. Environment overrides via `.env` (see `.env.example`).

## License

MIT
