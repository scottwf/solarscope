import pandas as pd
import sqlite3
import os
import shutil
from datetime import datetime

DATA_DIR = '/home/scott/solar-monitor/data/'
ARCHIVE_DIR = '/home/scott/solar-monitor/archive/'
DB_FILE = '/home/scott/solar-monitor/db/power_data.db'

os.makedirs(ARCHIVE_DIR, exist_ok=True)

def import_csv_file(file_path):
    print(f"Importing: {file_path}")
    df = pd.read_csv(file_path)

    try:
        df['timestamp'] = pd.to_datetime(df['DateTime'], format='%Y-%b-%d %I:%M %p')
        df['consumption'] = df['Consumption'].astype(float)
        df['peak_demand'] = df['Peak Demand'].astype(float)
    except Exception as e:
        print(f"❌ Skipping {file_path}: {e}")
        return

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    for _, row in df.iterrows():
        try:
            cur.execute('''
                INSERT INTO usage (timestamp, power, peak_demand)
                VALUES (?, ?, ?)
            ''', (row['timestamp'].isoformat(), row['consumption'], row['peak_demand']))
        except sqlite3.IntegrityError:
            continue

    conn.commit()
    conn.close()
    print(f"✅ Imported: {file_path}")

    # Move to archive
    archived_path = os.path.join(ARCHIVE_DIR, os.path.basename(file_path))
    shutil.move(file_path, archived_path)
    print(f"📦 Archived to: {archived_path}")

if __name__ == '__main__':
    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".csv"):
            import_csv_file(os.path.join(DATA_DIR, filename))