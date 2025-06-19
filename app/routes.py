# ========== Flask Setup ==========
from flask import Flask, request, jsonify
import sqlite3
import os
import tempfile
import zipfile
import pandas as pd
from datetime import datetime

app = Flask(__name__)

# ========== Configuration ==========
DB_FILE = '/home/scott/solar-monitor/db/power_data.db'
UPLOAD_FOLDER = '/home/scott/solar-monitor/data'
LOG_FILE = '/home/scott/solar-monitor/logs/activity.log'

# ========== Logging Function ==========
def log_event(message):
    """Log messages to a text file with timestamps"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{timestamp}] {message}\n")

# ========== Weather API Route ==========
@app.route('/weather')
def get_weather():
    """API endpoint to fetch sunrise/sunset for a date range"""
    start = request.args.get('start')
    end = request.args.get('end')

    if not start or not end:
        return jsonify({"error": "start and end required"}), 400

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT date, sunrise, sunset FROM weather
        WHERE date BETWEEN ? AND ?
        ORDER BY date
    """, (start, end))

    rows = cur.fetchall()
    conn.close()

    return jsonify([dict(row) for row in rows])

# ========== Upload Endpoint ==========
@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle uploaded .csv or .zip files from SaskPower"""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    uploaded_file = request.files['file']
    if uploaded_file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    filename = uploaded_file.filename
    tmp_dir = tempfile.mkdtemp()
    date_ranges = []

    try:
        # Handle ZIP uploads
        if filename.endswith('.zip'):
            zip_path = os.path.join(tmp_dir, filename)
            uploaded_file.save(zip_path)

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(tmp_dir)

            for fname in os.listdir(tmp_dir):
                if fname.endswith('.csv'):
                    full_path = os.path.join(tmp_dir, fname)
                    log_event(f"Processed CSV from ZIP: {fname}")
                    start, end = import_csv(full_path)
                    date_ranges.append((start, end))

        # Handle CSV uploads
        elif filename.endswith('.csv'):
            csv_path = os.path.join(tmp_dir, filename)
            uploaded_file.save(csv_path)
            log_event(f"Uploaded CSV file: {filename}")
            start, end = import_csv(csv_path)
            date_ranges.append((start, end))

        else:
            return jsonify({"error": "Unsupported file type"}), 400

        # After uploading, trigger solar + weather import for the uploaded dates
        if date_ranges:
            min_date = min(start for start, _ in date_ranges)
            max_date = max(end for _, end in date_ranges)

            # Stub functions – to be implemented
            import_generation_for_range(min_date, max_date)
            import_weather_for_range(min_date, max_date)
            log_event(f"Triggered solar and weather import for {min_date} to {max_date}")

        return jsonify({"status": "success"})

    except Exception as e:
        log_event(f"Upload failed: {e}")
        return jsonify({"error": str(e)}), 500

# ========== CSV Import Helper ==========
def import_csv(path):
    """Read a SaskPower CSV and insert usage into the database"""
    df = pd.read_csv(path)

    if 'Date' in df.columns and 'Time' in df.columns and 'Power (kW)' in df.columns:
        df['timestamp'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
        df['power'] = df['Power (kW)'].astype(float)

        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()

        for _, row in df.iterrows():
            cur.execute("""
                INSERT OR REPLACE INTO usage (timestamp, power)
                VALUES (?, ?)
            """, (row['timestamp'].strftime('%Y-%m-%d %H:%M:%S'), row['power']))

        conn.commit()
        conn.close()

        return df['timestamp'].min().date(), df['timestamp'].max().date()

# ========== Log Viewer ==========
@app.route('/log')
def view_log():
    """Simple web UI to view the last 300 lines of the log file"""
    if not os.path.exists(LOG_FILE):
        return "No logs yet."

    with open(LOG_FILE, 'r') as f:
        lines = f.readlines()[-300:]

    return (
        "<h1>Solar Monitor Log</h1><pre style='font-family:monospace'>" +
        "".join(lines) + "</pre>"
    )

# ========== Power Usage ==========    
@app.route('/power-usage')
def power_usage():
    """Fetch usage data with optional CSV output"""
    start = request.args.get('start')
    end = request.args.get('end')
    as_csv = request.args.get('csv', 'false').lower() == 'true'

    if not start or not end:
        return jsonify({"error": "Missing start or end"}), 400

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT timestamp, power FROM usage
        WHERE timestamp BETWEEN ? AND ?
        ORDER BY timestamp
    """, (start + " 00:00:00", end + " 23:59:59"))

    rows = cur.fetchall()
    conn.close()

    if as_csv:
        # Return CSV
        csv_data = "timestamp,power\n" + "\n".join(
            f"{row['timestamp']},{row['power']}" for row in rows
        )
        return csv_data, 200, {"Content-Type": "text/csv"}

    return jsonify([dict(row) for row in rows])

# ========== Solar Generation ==========
@app.route('/solar-generation')
def solar_generation():
    """Fetch solar generation with optional CSV output"""
    start = request.args.get('start')
    end = request.args.get('end')
    as_csv = request.args.get('csv', 'false').lower() == 'true'

    if not start or not end:
        return jsonify({"error": "Missing start or end"}), 400

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT timestamp, energy FROM generation
        WHERE timestamp BETWEEN ? AND ?
        ORDER BY timestamp
    """, (start + " 00:00:00", end + " 23:59:59"))

    rows = cur.fetchall()
    conn.close()

    if as_csv:
        csv_data = "timestamp,energy\n" + "\n".join(
            f"{row['timestamp']},{row['energy']}" for row in rows
        )
        return csv_data, 200, {"Content-Type": "text/csv"}

    return jsonify([dict(row) for row in rows])

# ========== Daily Usage ==========  
@app.route('/summary/daily')
def daily_summary():
    """Return total usage + generation for a single date"""
    date = request.args.get('date')
    if not date:
        return jsonify({"error": "Missing date"}), 400

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Usage
    cur.execute("""
        SELECT ROUND(SUM(power), 2) FROM usage
        WHERE DATE(timestamp) = ?
    """, (date,))
    usage_total = cur.fetchone()[0] or 0.0

    # Generation
    cur.execute("""
        SELECT ROUND(SUM(energy)/1000.0, 2) FROM generation
        WHERE DATE(timestamp) = ?
    """, (date,))
    generation_total = cur.fetchone()[0] or 0.0

    conn.close()

    return jsonify({
        "date": date,
        "total_usage_kWh": usage_total,
        "total_generation_kWh": generation_total
    })  
    
# ========== Stubbed Import Functions ==========
def import_generation_for_range(start_date, end_date):
    """Placeholder: Import solar data from SolarEdge API"""
    log_event(f"[stub] SolarEdge import from {start_date} to {end_date}")

def import_weather_for_range(start_date, end_date):
    """Placeholder: Import sunrise/sunset from Open-Meteo"""
    log_event(f"[stub] Weather import from {start_date} to {end_date}")
