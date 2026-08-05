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
            "SELECT MAX(t) FROM bronze_wind_data"
        ).fetchone()
        return result[0] if result[0] else None
    except duckdb.CatalogException:
        return None # table doesn't exist yet, first run

def fetch_wind_data(begin_date, end_date):
    url = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
    params = {
        "station": STATION,
        "product": "wind",
        "begin_date": begin_date,
        "end_date": end_date,
        "visibility": "visibility",
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

    records = fetch_wind_data(begin, end)
    print(f"Pulling {begin} -> {end}")
    print(f"Returned {len(records)} records")


# create or replace for testing, but should be create if not exists for production, CREATE TABLE IF NOT EXISTS
    con.execute("""
    CREATE TABLE IF NOT EXISTS bronze_wind_data (
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
        speed = None if r.get("s") in ("", None) else float(r["s"])

        con.execute(
        "INSERT INTO bronze_wind_data VALUES (?, ?, ?)",
        [r["t"], speed, now]
    )

    print(f"{len(records)} records processed")

if __name__ == "__main__":
    main()