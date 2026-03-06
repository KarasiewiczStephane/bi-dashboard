# BI Dashboard Suite

> Part of my Data Science Portfolio — [KarasiewiczStephane](https://github.com/KarasiewiczStephane)

## Quick Start

```bash
# 1. Install dependencies
make install

# 2. Generate synthetic data (~100k transactions in DuckDB)
make generate-data

# 3. Launch the dashboard
make dashboard
```

Open [http://localhost:8050](http://localhost:8050) in your browser.

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
│              agg_cohort                         │
└────────────────────────────────────────────────┘
```

Data flows bottom-up: the **synthetic data generator** (`src/data/generator.py`) populates dimension and fact tables in DuckDB, pre-computed aggregation tables speed up common queries, the **query layer** (`src/data/queries.py`) exposes typed Python methods, and **Dash callbacks** wire everything to the UI.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Plotly Dash, Dash Bootstrap Components |
| Charting | Plotly.js (bar, line, heatmap, funnel) |
| Database | DuckDB (in-process OLAP) |
| Reports | ReportLab (PDF), Jinja2 templates, CSV via pandas |
| Config | PyYAML, python-dotenv |
| Linting | Ruff |
| Container | Docker (Python 3.11-slim) |

## Setup

### Prerequisites

- Python 3.11+
- pip

### Install

```bash
git clone git@github.com:KarasiewiczStephane/bi-dashboard.git
cd bi-dashboard
make install
```

### Generate sample data

```bash
make generate-data
```

This runs `python -m src.data.generator`, which creates `data/bi_dashboard.duckdb` with:

- **dim_time** — daily calendar from 2022-01-01 to 2024-12-31
- **dim_product** — 50 synthetic products across 5 categories
- **dim_customer** — 5 000 customers with signup dates and segments
- **fact_sales** — ~100 000 transactions with Q4 seasonality
- **agg_daily_region / agg_daily_category / agg_cohort** — pre-computed rollups

The transaction count is configurable in `configs/config.yaml` under `data.transactions_count`.

### Run the dashboard

```bash
make dashboard   # or: make run
```

Opens a Dash server on [http://localhost:8050](http://localhost:8050). Host, port, and debug mode are set in `configs/config.yaml`.

### Docker

```bash
make docker-build
make docker-run          # exposes port 8050
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
├── configs/
│   └── config.yaml          # App, data, reporting, logging config
├── src/
│   ├── main.py              # Entry point (launches Dash server)
│   ├── data/
│   │   ├── database.py      # DuckDB connection, schema & aggregations
│   │   ├── generator.py     # Synthetic data generator (run standalone)
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
│       ├── config.py        # Config singleton (YAML + env overrides)
│       └── logger.py        # Structured logging setup
├── data/                    # Generated DuckDB file (gitignored)
├── Dockerfile
├── Makefile
├── requirements.txt
├── pyproject.toml
└── .env.example             # Environment variable reference
```

## Makefile Targets

| Target | Command | Description |
|--------|---------|-------------|
| `make install` | `pip install -r requirements.txt` | Install Python dependencies |
| `make generate-data` | `python -m src.data.generator` | Create synthetic DuckDB database |
| `make dashboard` | `python -m src.main` | Launch the Dash dashboard |
| `make run` | `python -m src.main` | Alias for `make dashboard` |
| `make test` | `pytest tests/ -v --tb=short --cov=src` | Run tests with coverage |
| `make lint` | `ruff check` + `ruff format` | Lint and format code |
| `make clean` | Remove `__pycache__` and `.pyc` | Clean build artifacts |
| `make docker-build` | `docker build` | Build Docker image |
| `make docker-run` | `docker run -p 8050:8050` | Run container |

## Configuration

All tuneable values live in `configs/config.yaml`. Environment variable overrides via `.env` (see `.env.example`).

## License

MIT
