
# NOAA Ocean Data Pipeline

A dbt + DuckDB pipeline that ingests real-time tide and wind data from the NOAA CO-OPS API, transforms it through a bronze/silver/gold medallion architecture, and produces marine condition metrics — including a noise-corrected tide direction signal derived from raw 6-minute sensor readings.

## What this project demonstrates

- **Medallion architecture** (bronze → silver → gold) implemented in dbt against a DuckDB warehouse
- **Incremental ingestion** from an external REST API using Python, with idempotent upserts based on the latest timestamp already in the warehouse
- **Source vs. ref() modeling discipline** — raw API data declared as a dbt `source`, all downstream transformation built with `ref()` for full lineage
- **Signal processing with window functions** — smoothing noisy sensor data to recover the true underlying tidal trend without destroying legitimate signal (see below)
- **Data quality debugging** — catching and fixing a subtle field-mapping bug where the wrong API field was silently ingested as water level, verified against NOAA's own published tide charts

## Architecture

```
NOAA CO-OPS API
      │
      ▼
Python (incremental fetch) ──▶ Bronze (raw, append-only)
                                     │
                                     ▼  dbt source()
                              Silver (cleaned, typed)
                                     │
                                     ▼  dbt ref()
                               Gold (marine conditions)
```

- **Bronze**: `bronze_water_levels`, `bronze_wind_data` — raw API responses, minimally transformed, loaded incrementally by timestamp
- **Silver**: cleaned, null-filtered, sensibly named views on top of bronze
- **Gold**: `gold_marine_conditions` — tide and wind joined by timestamp, with derived `tide_direction` and `wind_category` classifications

## A technical detail worth calling out: tide direction

Raw tide readings arrive every 6 minutes and are noisy at that resolution — comparing two consecutive readings to determine "rising" vs. "falling" produces a signal that flips direction constantly near high and low tide, even though the true tide is a slow ~6-hour sine wave.

The gold model instead:
1. Applies a moving average to smooth out short-period wave noise
2. Compares the smoothed value to its value several hours prior (a true slope-over-time, not just deviation from a local mean)
3. Applies a small dead-zone threshold around zero to classify near-flat stretches as `steady` rather than flickering between `rising`/`falling`

The result was verified directly against NOAA's own published water level charts for the same station and time window, and lines up closely with the real high/low tide timing.

Wind, by contrast, is left unsmoothed — gusts are a real physical condition, not noise obscuring an underlying trend, so instantaneous readings are more accurate to reality than a smoothed average would be.

## Tech stack

- **dbt** (DuckDB adapter) — transformation and modeling
- **DuckDB** — embedded analytical warehouse
- **Python** — incremental API ingestion (`requests`, `duckdb`)
- **GitHub Actions** — automated production runs
- **NOAA CO-OPS API** — tide (`water_level`) and wind (`wind`) products, station 9411340 (Santa Barbara, CA)

## Repo structure

```
NOAA_Data_Project/
├── models/
│   ├── silver/          # cleaned source data
│   └── gold/             # gold_marine_conditions.sql
├── NOAA_api_calls/
│   ├── fetch_tides.py
│   └── fetch_wind.py
├── dbt_project.yml
└── profiles.yml
```

## Running it locally

```bash
cd NOAA_Data_Project
python NOAA_api_calls/fetch_tides.py
python NOAA_api_calls/fetch_wind.py
dbt run
```

---

Built as a hands-on portfolio project while transitioning from marketing analytics into analytics engineering. Feedback welcome, reach out at short.jeremy95@gmail.com

Thank you,
Jeremy
