"""Initialize the SQLite database used by the Flask app.

Creates the tables for usage, generation, weather and the users table used
for authentication. When no user exists a default 'admin' account with
password 'admin' is created (password is hashed).
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_FILE = 'db/power_data.db'

# Create necessary directories
os.makedirs('db', exist_ok=True)
os.makedirs('logs', exist_ok=True)
os.makedirs('upload', exist_ok=True)

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

# Settings table for API keys and config
cur.execute('''
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
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

# Billing history (imported from SaskPower bill breakdown)
cur.execute('''
CREATE TABLE IF NOT EXISTS billing_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bill_date TEXT UNIQUE,
    usage_kwh REAL,
    total_charges REAL,
    electrical_charges REAL,
    carbon_charges REAL,
    taxes_fees REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# Solar ROI statistics
cur.execute('''
CREATE TABLE IF NOT EXISTS solar_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    period_start TEXT,
    period_end TEXT,
    usage_kwh REAL,
    generation_kwh REAL,
    self_consumption_kwh REAL,
    exported_kwh REAL,
    avoided_cost REAL,
    net_metering_credit REAL,
    actual_savings REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
