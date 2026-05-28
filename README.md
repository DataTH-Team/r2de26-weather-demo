# R2DE26 Weather Demo

Cursor demo for **CH1 Live** (Data Ingestion & SQL) — showcase AI agent orchestration at three levels using a standalone Bangkok weather ETL pipeline.

**Repo:** [DataTH-Team/r2de26-weather-demo](https://github.com/DataTH-Team/r2de26-weather-demo)

## What this demo shows

Students just finished CH1 (ingest data from an API, transform, query with SQL). This demo shows how Cursor helps a Data Engineer do that work — at three levels of control:

| Level | Cursor feature | What it does | DE analogy |
|-------|----------------|--------------|------------|
| **1 — Prompt** | Chat | Ask in plain language; AI writes and runs code ad hoc | One-off on-call query |
| **2 — Rules** | `.cursor/rules/` | Guardrails — folder layout, timezone, no secrets, minimal diffs | Team coding standards / data contracts |
| **3 — Skills** | `.cursor/skills/` | Step-by-step runbook the agent follows every time | Scheduled pipeline / SOP |

**Story:** Analytics asks for Bangkok weather for the last 7 days. You build a mini pipeline: Open-Meteo API → raw JSON → SQLite → SQL validation & summary.

## Quick start

```bash
git clone git@github.com:DataTH-Team/r2de26-weather-demo.git
cd r2de26-weather-demo/demo

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python src/run_pipeline.py
```

Expected output: raw JSON saved, SQLite loaded, validation passed, Thai KPI summary printed.

## Project layout

```
demo/
├── .cursor/
│   ├── rules/de-pipeline.mdc      # Level 2 — guardrails
│   └── skills/ingest-weather/     # Level 3 — runbook
├── src/
│   ├── fetch_weather.py           # Extract: Open-Meteo → raw JSON
│   ├── load_sqlite.py             # Load: JSON rows → SQLite
│   └── run_pipeline.py            # Orchestrator
├── sql/
│   ├── validate.sql               # Data quality checks
│   └── summary.sql                # 7-day summary query
├── data/
│   ├── raw/                       # Append-only raw layer (JSON)
│   └── weather.db                 # SQLite (gitignored, created on run)
└── requirements.txt
```

## Live demo script (~8 min)

Open the `demo/` folder in Cursor (File → Open Folder).

### Level 1 — Prompt (~2 min)

Start from an empty `src/` (or hide existing files during live). Prompt:

> ช่วยเขียน Python ดึงอุณหภูมิสูงสุด/ต่ำสุด 7 วันล่าสุดของ Bangkok จาก Open-Meteo API แล้วบอกว่าวันไหนร้อนที่สุด

**Point:** Fast answer, but no standard structure — output varies each time.

### Level 2 — Rules (~2–3 min)

Reveal `.cursor/rules/de-pipeline.mdc`. Test guardrails:

- **Negative:** ask to delete files in `data/raw/` or hardcode paths → AI should refuse
- **Positive:** ask to refactor into `src/`, `sql/`, `data/raw/` with Bangkok timezone → AI follows conventions

**Point:** AI stays within team boundaries — like lint rules for an agent.

### Level 3 — Skills (~3 min)

Reveal `.cursor/skills/ingest-weather/SKILL.md`. Prompt:

> refresh weather pipeline แล้วสรุป KPI ให้ทีม analytics (ภาษาไทย)

Or invoke the skill by name: `/ingest-weather`

**Point:** One command runs the full SOP — fetch, validate, report — every time.

## API reference

Open-Meteo forecast (no API key required):

```
https://api.open-meteo.com/v1/forecast
  ?latitude=13.7563
  &longitude=100.5018
  &daily=temperature_2m_max,temperature_2m_min
  &timezone=Asia/Bangkok
  &past_days=6
  &forecast_days=1
```

## Homework for students

1. Pick a public API and create your own empty-folder pipeline
2. Write 3 Rules (timezone, folder structure, no secrets in code)
3. Write a 5-step Skill for a task you repeat daily
4. Compare Level 1 vs Level 3: diff size, output consistency, repeatability

## License

Demo material for [Road to Data Engineer 3.0](https://r2de26.datath.com) — DataTH
