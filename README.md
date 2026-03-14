# Drogas AQA Dashboard

Professional Streamlit dashboard for tracking the automation progress of manual test cases for the **Drogas** website.

Data is fetched directly from **TestRail** via API using a Test Plan ID. The plan contains **4 runs** with configurations combining device type and country:

| Run Config   | Device  | Country   |
|-------------|---------|-----------|
| desktop LV  | Desktop | Latvia    |
| desktop LT  | Desktop | Lithuania |
| mobile LV   | Mobile  | Latvia    |
| mobile LT   | Mobile  | Lithuania |

## Features

- **KPI Summary** — total tests, automated count, coverage %, backlog, blocked, in-progress
- **Automation Progress** — segmented progress bar + gauge chart
- **Status Distribution** — donut chart (execution status) + bar chart (automation categories)
- **Country & Device Comparison** — coverage by country, by device, heatmap, grouped breakdowns
- **Interactive Filters** — country, device, execution status, automation category, assignee
- **Drill-Down Tables** — full test case list with clickable TestRail and Jira links, backlog summary, blocked cases
- **Auto-Refresh** — fresh data loaded on every app open; manual refresh button; Streamlit caching for performance

## Project Structure

```
drogas/
├── app.py                          # Streamlit entry point
├── config.py                       # Settings, colours, field mappings
├── api/
│   └── testrail_client.py          # TestRail REST API client
├── data/
│   ├── data_loader.py              # Fetch + assemble data from TestRail
│   └── data_processing.py          # Enrichment, KPI computation
├── dashboard/
│   ├── layout.py                   # Page layout, section assembly
│   ├── charts.py                   # Plotly chart components
│   ├── tables.py                   # Data table components
│   └── filters.py                  # Sidebar filter components
├── utils/
│   └── helpers.py                  # Shared utilities
├── .streamlit/
│   └── config.toml                 # Streamlit theme
├── .env.example                    # Credential template
├── requirements.txt
└── README.md
```

## Setup

### 1. Clone and install

```bash
cd drogas
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
pip install -r requirements.txt
```

### 2. Configure credentials

```bash
cp .env.example .env
```

Edit `.env` and fill in your TestRail credentials:

```
TESTRAIL_URL=https://elabaswatson.testrail.io
TESTRAIL_USER=your_email@domain.com
TESTRAIL_API_KEY=your_testrail_api_key
TESTRAIL_PLAN_ID=63084
```

> **Note:** Generate a TestRail API key from *My Settings → API Keys* in TestRail.

### 3. Run

```bash
streamlit run app.py
```

The dashboard opens at `http://localhost:8501`.

## Architecture

```
TestRail API
    │
    ├── get_plan/{id}       → plan entries + runs (4 configs)
    ├── get_tests/{run_id}  → tests per run (paginated)
    ├── get_statuses        → status ID → label mapping
    ├── get_case_fields     → custom dropdown value mappings
    └── get_users           → user ID → name mapping
    │
    ▼
Data Loader (data_loader.py)
    │  normalize + flatten into DataFrame
    ▼
Data Processing (data_processing.py)
    │  enrich: automation_category, jira_link, case_id_display
    ▼
Dashboard (layout.py → charts.py, tables.py, filters.py)
    │  Streamlit + Plotly rendering
    ▼
Browser
```

## Automation Lifecycle Statuses

| Status              | Category       | Colour  |
|---------------------|---------------|---------|
| Passed              | Automated     | Green   |
| Passed with Issue   | Automated     | Lt Green|
| Passed (stubbed)    | Automated     | Yellow  |
| Blocked             | Blocked       | Orange  |
| Failed / Failed (*) | Failed        | Red     |
| Not Applicable      | Not Applicable| Grey    |
| To Do / No-Run      | Backlog       | Purple  |

## Configuration

All configurable values live in `config.py`:

- **Custom field names** — if your TestRail instance uses different system names, update `CUSTOM_FIELDS`
- **Status groupings** — edit `AUTOMATED_STATUSES`, `BLOCKED_STATUSES`, etc.
- **Colours** — `STATUS_COLORS` and `CATEGORY_COLORS`
- **Cache TTL** — `CACHE_TTL_SECONDS` (default 300s)
