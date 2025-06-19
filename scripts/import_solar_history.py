import requests
import sqlite3
from datetime import datetime, timedelta

API_KEY = 'IXUDMK4ITGHOWWCORKCB4T1LTCBT7QVU'
SITE_ID = '2563089'
DB_FILE = '/home/scott/solar-monitor/db/power_data.db'

def fetch_day(start_time):
    end_time = start_time + timedelta(days=1)
    url = f'https://monitoringapi.solaredge.com/site/{SITE_ID}/energyDetails.json'
    params = {
        'api_key': API_KEY,
        'timeUnit': 'QUARTER_OF_AN_HOUR',
        'startTime': start_time.strftime('%Y-%m-%d %H:%M:%S'),
        'endTime': end_time.strftime('%Y-%m-%d %H:%M:%S'),
        'meters': 'Production'
    }
    r = requests.get(url, params=params)
    data = r.json()
    return data['energyDetails']['meters'][0]['values']

def save_to_db(records):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    for entry in records:
        ts = entry['date']
        value = entry.get('value', 0.0)
        try:
            cur.execute('INSERT INTO generation (timestamp, energy) VALUES (?, ?)', (ts, value))
        except sqlite3.IntegrityError:
            continue
    conn.commit()
    conn.close()

if __name__ == '__main__':
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=3*365)

    current = start_date
    total_imported = 0

    while current < end_date:
        print(f"Fetching {current}...")
        try:
            data = fetch_day(datetime.combine(current, datetime.min.time()))
            save_to_db(data)
            total_imported += len(data)
        except Exception as e:
            print(f"Failed on {current}: {e}")
        current += timedelta(days=1)

    print(f"Done. Total records imported: {total_imported}")
