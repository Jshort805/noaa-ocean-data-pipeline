import requests
import duckdb
import json
from datetime import datetime, timedelta

STATION = "9411340"  #SB, CA
DB_PATH = "NOAA_Data.db"

def get_last_timestamp(con):
    """Check what's already in the DB to pull incrementally."""
    try:
        result = con.execute(
            "SELECT MAX(t) FROM bronze_water_data"
        ).fetchone()
        return result[0] if result[0] else None
    except duckdb.CatalogException:
        return None  # table doesn't exist yet, first run

def fetch_water_levels(begin_date, end_date):
    url = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
    params = {    
        "station": STATION,
        "product": "water_level",
        "begin_date": begin_date,
        "end_date": end_date,
        "datum": "MLLW",
        "time_zone": "lst_ldt",
        "units": "english",
        "format": "json"
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json().get("data", [])

def main():
    con = duckdb.connect(DB_PATH)
    last_ts = get_last_timestamp(con)

    if last_ts is None:
    # First run - load the last 7 days
        begin = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d %H:%M")
        print("First run: backfilling last 7 days...")
    else:
    # Future runs - only load newer data
        begin = last_ts.strftime("%Y%m%d %H:%M")
    print(f"Incremental load starting from {begin}")

    end = datetime.now().strftime("%Y%m%d %H:%M")

    records = fetch_water_levels(begin, end)
    print(f"Pulling {begin} -> {end}")
    print(f"Returned {len(records)} records")

    con.execute("""
    CREATE TABLE IF NOT EXISTS bronze_water_data (
        t TIMESTAMP,
        v DOUBLE,
        pulled_at TIMESTAMP
    )
    """)

    last_ts = get_last_timestamp(con)

    if not records:
        print("No new records")
        return

    now = datetime.now()
    for r in records:
        height = None if r.get("v") in ("", None) else float(r["v"])

        con.execute(
        "INSERT INTO bronze_water_data VALUES (?, ?, ?)",
        [r["t"], height, now]
    )
    print(f"{len(records)} new records")

if __name__ == "__main__":
    main()