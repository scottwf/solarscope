import requests
import sqlite3
from datetime import datetime, timedelta

API_KEY = 'IXUDMK4ITGHOWWCORKCB4T1LTCBT7QVU'
SITE_ID = '2563089'
DB_FILE = '/home/scott/solar-monitor/db/power_data.db'

def fetch_latest_generation():
    end = datetime.now()
    start = end - timedelta(hours=1)

    url = f'https://monitoringapi.solaredge.com/site/{SITE_ID}/energyDetails.json'
    params = {
        'api_key': API_KEY,
        'timeUnit': 'QUARTER_OF_AN_HOUR',
        'startTime': start.strftime('%Y-%m-%d %H:%M:%S'),
        'endTime': end.strftime('%Y-%m-%d %H:%M:%S'),
        'meters': 'Production'
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data['energyDetails']['meters'][0]['values']
    except Exception as e:
        print(f"Error fetching solar data: {e}")
        return []

def save_to_db(data):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    for entry in data:
        ts = entry['date']
        value = entry.get('value', 0.0)
        try:
            cur.execute('INSERT INTO generation (timestamp, energy) VALUES (?, ?)', (ts, value))
        except sqlite3.IntegrityError:
            continue  # Skip if already exists
    conn.commit()
    conn.close()

if __name__ == '__main__':
    records = fetch_latest_generation()
    save_to_db(records)
    print(f"Imported {len(records)} new solar records.")
