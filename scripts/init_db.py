"""Initialize the SQLite database used by the Flask app.

Creates the tables for usage, generation, weather and the users table used
for authentication. When no user exists a default 'admin' account with
password 'admin' is created (password is hashed).
"""

import sqlite3
from werkzeug.security import generate_password_hash

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

# Simple user table for authentication
cur.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
)
''')

# Create default admin user if none exists
cur.execute("SELECT COUNT(*) FROM users")
if cur.fetchone()[0] == 0:
    cur.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        ("admin", generate_password_hash("admin"))
    )

conn.commit()
conn.close()
print("Database initialized.")
