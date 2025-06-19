import sqlite3

DB_FILE = '/home/scott/solar-monitor/db/power_data.db'

conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

# Usage table (already used)
cur.execute('''
CREATE TABLE IF NOT EXISTS usage (
    timestamp TEXT PRIMARY KEY,
    power REAL
)
''')

# Solar generation data (from SolarEdge)
cur.execute('''
CREATE TABLE IF NOT EXISTS generation (
    timestamp TEXT PRIMARY KEY,
    energy REAL
)
''')

# Weather data (from iOS Shortcut)
cur.execute('''
CREATE TABLE IF NOT EXISTS weather (
    timestamp TEXT PRIMARY KEY,
    condition TEXT,
    daylight_minutes INTEGER
)
''')

conn.commit()
conn.close()
print("Database initialized.")