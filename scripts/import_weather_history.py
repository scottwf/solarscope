import requests
import sqlite3
from datetime import date, timedelta

DB_FILE = '/home/scott/solar-monitor/db/power_data.db'
LAT = 52.1332
LON = -106.67
TZ = 'America/Regina'
START_DATE = date(2022, 1, 1)  # your solar system start
END_DATE = date.today()

def already_imported(conn, d):
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM weather WHERE date = ?", (d.isoformat(),))
    return cur.fetchone() is not None

def fetch_weather(d):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LAT,
        "longitude": LON,
        "daily": "sunrise,sunset",
        "timezone": TZ,
        "start_date": d.isoformat(),
        "end_date": d.isoformat()
    }
    try:
        res = requests.get(url, params=params)
        res.raise_for_status()
        daily = res.json().get("daily", {})
        return daily["sunrise"][0], daily["sunset"][0]
    except Exception as e:
        print(f"{d}: Failed to fetch weather → {e}")
        return None, None

def main():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    d = START_DATE
    while d <= END_DATE:
        if not already_imported(conn, d):
            sunrise, sunset = fetch_weather(d)
            if sunrise and sunset:
                cur.execute("INSERT INTO weather (date, sunrise, sunset) VALUES (?, ?, ?)",
                            (d.isoformat(), sunrise, sunset))
                conn.commit()
                print(f"{d}: ✅ {sunrise} → {sunset}")
        d += timedelta(days=1)
    conn.close()

if __name__ == "__main__":
    main()
