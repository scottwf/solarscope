# Routes and helper functions for the Solar Monitor Flask app.
# Provides endpoints for data upload and CSV/JSON APIs.
#
# Note: This file is now a Flask Blueprint to be registered in app.py.
# ========== Flask Setup ==========
from flask import Blueprint, request, jsonify

routes = Blueprint('routes', __name__)
import sqlite3
import os
import tempfile
import zipfile
import pandas as pd
from datetime import datetime, timedelta


# ========== Configuration ==========
DB_FILE = 'db/power_data.db'
UPLOAD_FOLDER = 'upload'
LOG_FILE = 'logs/activity.log'

# ========== Logging Function ==========
def log_event(message):
    """Log messages to a text file with timestamps"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{timestamp}] {message}\n")

# ========== Weather API Route ==========
@routes.route('/weather')
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
@routes.route('/upload', methods=['POST'])
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
                    result = import_csv(full_path)
                    if result is not None:
                        start, end = result
                        date_ranges.append((start, end))
                    else:
                        log_event(f"Skipped CSV (missing columns): {fname}")

        # Handle CSV uploads
        elif filename.endswith('.csv'):
            csv_path = os.path.join(tmp_dir, filename)
            uploaded_file.save(csv_path)
            log_event(f"Uploaded CSV file: {filename}")
            result = import_csv(csv_path)
            if result is not None:
                start, end = result
                date_ranges.append((start, end))
            else:
                log_event(f"Skipped CSV (missing columns): {filename}")

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
    try:
        df = pd.read_csv(path, delimiter=None)
    except Exception as e:
        log_event(f"CSV parsing failed: {e}")
        return None

    if df.empty:
        log_event("CSV file is empty")
        return None

    # Support both legacy and new SaskPower formats
    if 'Date' in df.columns and 'Time' in df.columns and 'Power (kW)' in df.columns:
        try:
            df['timestamp'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
            df['power'] = df['Power (kW)'].astype(float)
        except Exception as e:
            log_event(f"Failed to parse Date/Time format: {e}")
            return None
    elif 'DateTime' in df.columns and 'Consumption' in df.columns:
        try:
            df['timestamp'] = pd.to_datetime(df['DateTime'])
            df['power'] = df['Consumption'].astype(float)
        except Exception as e:
            log_event(f"Failed to parse DateTime format: {e}")
            return None
    else:
        log_event(f"CSV columns not recognized. Found: {list(df.columns)}")
        return None

    # Validate data
    if df['timestamp'].isna().any():
        log_event("CSV contains invalid timestamps")
        return None
    if df['power'].isna().any():
        log_event("CSV contains invalid power values")
        return None

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    for _, row in df.iterrows():
        try:
            cur.execute("""
                INSERT OR REPLACE INTO usage (timestamp, power)
                VALUES (?, ?)
            """, (row['timestamp'].strftime('%Y-%m-%d %H:%M:%S'), row['power']))
        except Exception as e:
            log_event(f"Failed to insert row: {e}")
            continue

    conn.commit()
    conn.close()

    log_event(f"CSV import successful: {len(df)} rows")
    return df['timestamp'].min().date(), df['timestamp'].max().date()

# ========== Log Viewer ==========
@routes.route('/log')
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
@routes.route('/power-usage')
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
@routes.route('/solar-generation')
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
@routes.route('/summary/daily')
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

# ========== Weekly Usage ==========
@routes.route('/summary/weekly')
def weekly_summary():
    """Return total usage and generation for a week given the start date"""
    start = request.args.get('start')
    if not start:
        return jsonify({"error": "Missing start"}), 400
    try:
        d0 = datetime.strptime(start, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"error": "Invalid date"}), 400
    end = d0 + timedelta(days=6)

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        "SELECT ROUND(SUM(power), 2) FROM usage WHERE DATE(timestamp) BETWEEN ? AND ?",
        (str(d0), str(end))
    )
    usage_total = cur.fetchone()[0] or 0.0
    cur.execute(
        "SELECT ROUND(SUM(energy)/1000.0, 2) FROM generation WHERE DATE(timestamp) BETWEEN ? AND ?",
        (str(d0), str(end))
    )
    gen_total = cur.fetchone()[0] or 0.0
    conn.close()
    return jsonify({
        "start": str(d0),
        "end": str(end),
        "total_usage_kWh": usage_total,
        "total_generation_kWh": gen_total
    })
    
# ========== Settings Helpers ==========
def get_setting(key):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

def set_setting(key, value):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

# ========== Settings API Endpoints ==========
from flask import request, jsonify

@routes.route('/admin/electricity-cost', methods=['GET', 'POST'])
def electricity_cost():
    if request.method == 'POST':
        cost = request.form.get('electricity_cost')
        try:
            if cost is not None:
                set_setting('electricity_cost', str(float(cost)))
                return jsonify({'status': 'Saved'})
            else:
                return jsonify({'error': 'No cost provided'}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    else:
        val = get_setting('electricity_cost') or ''
        return jsonify({'electricity_cost': val})

@routes.route('/admin/solar-settings', methods=['GET', 'POST'])
def solar_settings():
    if request.method == 'POST':
        api_key = request.form.get('api_key', '')
        site_id = request.form.get('site_id', '')
        set_setting('solaredge_api_key', api_key)
        set_setting('solaredge_site_id', site_id)
        return jsonify({'status': 'Saved'})
    else:
        return jsonify({
            'api_key': get_setting('solaredge_api_key') or '',
            'site_id': get_setting('solaredge_site_id') or ''
        })

import requests

# Geocode city to lat/lon using Nominatim
def geocode_city(city):
    try:
        url = f"https://nominatim.openstreetmap.org/search"
        params = {"q": city, "format": "json", "limit": 1}
        headers = {"User-Agent": "solarscope-app/1.0"}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            lat = data[0]['lat']
            lon = data[0]['lon']
            return float(lat), float(lon)
        else:
            return None
    except Exception as e:
        log_event(f"Geocoding failed for '{city}': {e}")
        return None

@routes.route('/admin/weather-settings', methods=['GET', 'POST'])
def weather_settings():
    if request.method == 'POST':
        location = request.form.get('location')
        start_date = request.form.get('weather_start_date')
        response = {'status': 'Saved'}
        if location is not None:
            set_setting('weather_location', location)
            # Geocode city to lat/lon
            coords = geocode_city(location)
            if coords:
                set_setting('weather_lat', str(coords[0]))
                set_setting('weather_lon', str(coords[1]))
                response['lat'] = coords[0]
                response['lon'] = coords[1]
            else:
                response['warning'] = 'Could not geocode city. Please check spelling.'
        if start_date is not None:
            set_setting('weather_start_date', start_date)
            response['weather_start_date'] = start_date
        return jsonify(response)
    else:
        return jsonify({
            'location': get_setting('weather_location') or '',
            'lat': get_setting('weather_lat') or '',
            'lon': get_setting('weather_lon') or '',
            'weather_start_date': get_setting('weather_start_date') or '2022-01-01'
        })

# ========== Weather Fetch Implementation ==========
from datetime import datetime, timedelta

def fetch_weather_for_dates(start_date, end_date):
    lat = get_setting('weather_lat')
    lon = get_setting('weather_lon')
    if not lat or not lon:
        log_event('Weather fetch failed: No coordinates set.')
        return False
    # Build date list
    d0 = datetime.strptime(str(start_date), '%Y-%m-%d')
    d1 = datetime.strptime(str(end_date), '%Y-%m-%d')
    days = [(d0 + timedelta(days=i)).date() for i in range((d1-d0).days+1)]
    for day in days:
        url = f"https://archive-api.open-meteo.com/v1/archive"
        params = {
            'latitude': lat,
            'longitude': lon,
            'start_date': str(day),
            'end_date': str(day),
            'daily': 'sunrise,sunset,weathercode',
            'timezone': 'auto'
        }
        try:
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()['daily']
            sunrise = data['sunrise'][0]
            sunset = data['sunset'][0]
            weathercode = data['weathercode'][0] # int code

            # Store in DB
            conn = sqlite3.connect(DB_FILE)
            cur = conn.cursor()
            cur.execute("""
                INSERT OR REPLACE INTO weather (timestamp, condition, daylight_minutes)
                VALUES (?, ?, ?)
            """, (str(day), f"code:{weathercode}", _daylight_minutes(sunrise, sunset)))
            conn.commit()
            conn.close()
            log_event(f"Weather for {day} saved: code={weathercode}")
        except Exception as e:
            log_event(f"Weather fetch failed for {day}: {e}")
    return True

def _daylight_minutes(sunrise, sunset):
    # sunrise/sunset: '2025-06-19T04:47', returns minutes
    try:
        t1 = datetime.strptime(sunrise, '%Y-%m-%dT%H:%M')
        t2 = datetime.strptime(sunset, '%Y-%m-%dT%H:%M')
        return int((t2-t1).total_seconds()//60)
    except:
        return None

@routes.route('/admin/fetch-weather', methods=['POST'])
def admin_fetch_weather():
    start = request.form.get('start_date')
    end = request.form.get('end_date')
    if not start or not end:
        return jsonify({'error': 'Missing start or end date'}), 400
    ok = fetch_weather_for_dates(start, end)
    return jsonify({'status': 'ok' if ok else 'failed'})

# ========== SolarEdge Data Import Endpoint ==========
@routes.route('/admin/fetch-solar', methods=['POST'])
def admin_fetch_solar():
    start = request.form.get('start_date')
    end = request.form.get('end_date')
    if not start or not end:
        return jsonify({'error': 'Missing start or end date'}), 400
    ok = import_generation_for_range(start, end)
    return jsonify({'status': 'ok' if ok else 'failed'})

# ========== SolarEdge Sync Status Endpoint ==========
@routes.route('/solar-sync-status')
def solar_sync_status():
    last_update = get_setting('solaredge_last_update')
    return jsonify({'last_update': last_update})

# ========== SolarEdge Batch Import Endpoint ==========
@routes.route('/admin/fetch-solar-batch', methods=['POST'])
def admin_fetch_solar_batch():
    start = request.form.get('start_date')
    end = request.form.get('end_date')
    if not start or not end:
        return jsonify({'error': 'Missing start or end date'}), 400
    ok = import_generation_for_range(start, end)
    return jsonify({'status': 'ok' if ok else 'failed', 'start_date': start, 'end_date': end})

# ========== Dashboard Summary Endpoints ==========
from datetime import date, timedelta

def get_period_range(period, data_start):
    today = date.today()
    # Use the later of data_start or the normal period start
    if period == 'year':
        period_start = today.replace(month=1, day=1)
    elif period == 'month':
        period_start = today.replace(day=1)
    elif period == 'week':
        period_start = today - timedelta(days=today.weekday())
    else:
        return None, None
    # Clamp start to data_start
    start = max(period_start, data_start)
    end = today
    return str(start), str(end)

@routes.route('/summary/totals/<period>')
def summary_totals(period):
    """period: year, month, week"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    # Find first and last usage date
    cur.execute("SELECT MIN(DATE(timestamp)), MAX(DATE(timestamp)) FROM usage")
    usage_minmax = cur.fetchone()
    usage_start = usage_minmax[0]
    usage_end = usage_minmax[1]
    # Find first and last generation date
    cur.execute("SELECT MIN(DATE(timestamp)), MAX(DATE(timestamp)) FROM generation")
    gen_minmax = cur.fetchone()
    gen_start = gen_minmax[0]
    gen_end = gen_minmax[1]
    # Compute the overlap for the period
    today = date.today()
    if period == 'year':
        period_start = today.replace(month=1, day=1)
    elif period == 'month':
        period_start = today.replace(day=1)
    elif period == 'week':
        period_start = today - timedelta(days=today.weekday())
    else:
        conn.close()
        return jsonify({'error': 'Invalid period'}), 400
    # Overlapping range: latest of period_start, usage_start, gen_start; earliest of today, usage_end, gen_end
    overlap_start = max(period_start,
                       date.fromisoformat(usage_start) if usage_start else period_start,
                       date.fromisoformat(gen_start) if gen_start else period_start)
    overlap_end = min(today,
                     date.fromisoformat(usage_end) if usage_end else today,
                     date.fromisoformat(gen_end) if gen_end else today)
    if (usage_start is None or usage_end is None or gen_start is None or gen_end is None or overlap_end < overlap_start):
        # No overlap
        conn.close()
        return jsonify({'period': period, 'start': None, 'end': None, 'total_usage': 0, 'total_generation': 0, 'usage_cost': 0, 'message': 'No overlapping data'}), 200
    start = str(overlap_start)
    end = str(overlap_end)
    # Query totals for overlap
    cur.execute("SELECT SUM(power) FROM usage WHERE DATE(timestamp) BETWEEN ? AND ?", (start, end))
    usage = cur.fetchone()[0] or 0.0
    cur.execute("SELECT SUM(energy) FROM generation WHERE DATE(timestamp) BETWEEN ? AND ?", (start, end))
    generation = cur.fetchone()[0] or 0.0
    # Get cost
    cost = get_setting('electricity_cost')
    cost = float(cost) if cost else None
    usage_cost = usage * cost if cost else None
    # Round values
    usage = round(usage)
    generation = round(generation)
    usage_cost = round(usage_cost) if usage_cost is not None else None
    conn.close()
    return jsonify({
        'period': period,
        'start': start,
        'end': end,
        'total_usage': usage,
        'total_generation': generation,
        'usage_cost': usage_cost
    })

# ========== Weather Data Summary Endpoint ==========
@routes.route('/admin/weather-summary')
def weather_summary():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT MIN(timestamp), MAX(timestamp), COUNT(*) FROM weather")
    row = cur.fetchone()
    conn.close()
    return jsonify({
        'first': row[0],
        'last': row[1],
        'count': row[2]
    })

# ========== Stubbed Import Functions ==========
def import_generation_for_range(start_date, end_date):
    """Import solar generation data from SolarEdge API for the given date range."""
    api_key = get_setting('solaredge_api_key')
    site_id = get_setting('solaredge_site_id')
    if not api_key or not site_id:
        log_event('SolarEdge import failed: Missing API key or Site ID.')
        return False
    try:
        # SolarEdge API: /site/{site_id}/energy
        url = f"https://monitoringapi.solaredge.com/site/{site_id}/energy"
        params = {
            'api_key': api_key,
            'timeUnit': 'QUARTER_OF_AN_HOUR',
            'startDate': start_date,
            'endDate': end_date
        }
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if 'energy' not in data or 'values' not in data['energy']:
            log_event(f"SolarEdge import failed: Unexpected API response for {start_date} to {end_date}.")
            return False
        values = data['energy']['values']
        # Insert each (date, value) into generation table
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        count = 0
        for entry in values:
            ts = entry.get('date')  # e.g., '2023-06-19 11:00:00'
            val = entry.get('value')
            if ts and val is not None:
                # Convert Wh to kWh (API returns Wh)
                kwh = float(val) / 1000.0
                cur.execute("""
                    INSERT OR REPLACE INTO generation (timestamp, energy)
                    VALUES (?, ?)
                """, (ts, kwh))
                count += 1
        conn.commit()
        conn.close()
        log_event(f"SolarEdge import: {count} records saved for {start_date} to {end_date}.")
        return True
    except Exception as e:
        log_event(f"SolarEdge import failed for {start_date} to {end_date}: {e}")
        return False


def import_weather_for_range(start_date, end_date):
    """Import sunrise/sunset from Open-Meteo"""
    return fetch_weather_for_dates(start_date, end_date)


# ========== Historical Billing Data Import ==========
def import_bill_breakdown(path):
    """Import SaskPower bill breakdown CSV"""
    try:
        df = pd.read_csv(path)
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()

        for _, row in df.iterrows():
            try:
                bill_date = pd.to_datetime(row['BillIssueDate']).strftime('%Y-%m-%d')
                usage = float(row['ConsumptionKwh'])
                total = float(row['TotalCharges'])
                electrical = float(row['ElectricalCharges'])
                carbon = float(row.get('FederalCarbonChargeTotal', 0) or 0)
                taxes = total - electrical - carbon

                cur.execute("""
                    INSERT OR REPLACE INTO billing_history
                    (bill_date, usage_kwh, total_charges, electrical_charges, carbon_charges, taxes_fees)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (bill_date, usage, total, electrical, carbon, taxes))
            except Exception as e:
                log_event(f"Failed to insert bill row: {e}")
                continue

        conn.commit()
        conn.close()
        log_event(f"Bill breakdown import successful: {len(df)} records")
        return True
    except Exception as e:
        log_event(f"Bill breakdown import failed: {e}")
        return False


def import_meter_history(path):
    """Import SaskPower meter read history CSV"""
    try:
        df = pd.read_csv(path)
        df = df.sort_values('Read Date').reset_index(drop=True)

        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()

        prev_reading = 0
        for _, row in df.iterrows():
            try:
                read_date = pd.to_datetime(row['Read Date']).strftime('%Y-%m-%d')
                current_reading = int(row['Meter Read'])

                # Skip invalid readings (reading shouldn't go backwards significantly)
                if current_reading < prev_reading:
                    if (prev_reading - current_reading) > 100:
                        log_event(f"Skipped invalid meter reading on {read_date}: {current_reading} (previous: {prev_reading})")
                        continue

                prev_reading = current_reading
            except Exception as e:
                log_event(f"Failed to process meter reading: {e}")
                continue

        conn.close()
        log_event(f"Meter history import processed: {len(df)} records")
        return True
    except Exception as e:
        log_event(f"Meter history import failed: {e}")
        return False


# ========== Admin Endpoints for Historical Data ==========
@routes.route('/admin/import-bill-breakdown', methods=['POST'])
def admin_import_bill_breakdown():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    uploaded_file = request.files['file']
    if uploaded_file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    try:
        tmp_dir = tempfile.mkdtemp()
        filepath = os.path.join(tmp_dir, uploaded_file.filename)
        uploaded_file.save(filepath)

        success = import_bill_breakdown(filepath)
        return jsonify({"status": "success" if success else "failed"})
    except Exception as e:
        log_event(f"Bill breakdown upload failed: {e}")
        return jsonify({"error": str(e)}), 500


@routes.route('/admin/import-meter-history', methods=['POST'])
def admin_import_meter_history():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    uploaded_file = request.files['file']
    if uploaded_file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    try:
        tmp_dir = tempfile.mkdtemp()
        filepath = os.path.join(tmp_dir, uploaded_file.filename)
        uploaded_file.save(filepath)

        success = import_meter_history(filepath)
        return jsonify({"status": "success" if success else "failed"})
    except Exception as e:
        log_event(f"Meter history upload failed: {e}")
        return jsonify({"error": str(e)}), 500


# ========== ROI Calculations ==========
@routes.route('/roi/summary')
def roi_summary():
    """Calculate total savings and ROI metrics"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Get solar installation date (earliest generation record)
    cur.execute("SELECT MIN(DATE(timestamp)) FROM generation")
    solar_start = cur.fetchone()[0]

    if not solar_start:
        conn.close()
        return jsonify({"error": "No solar data available"}), 400

    # Get billing data before and after solar
    cur.execute("""
        SELECT SUM(electrical_charges), SUM(usage_kwh)
        FROM billing_history
        WHERE bill_date < ?
    """, (solar_start,))
    pre_solar = cur.fetchone()

    cur.execute("""
        SELECT SUM(electrical_charges), SUM(usage_kwh)
        FROM billing_history
        WHERE bill_date >= ?
    """, (solar_start,))
    post_solar = cur.fetchone()

    # Get generation data
    cur.execute("""
        SELECT SUM(energy) FROM generation
        WHERE DATE(timestamp) >= ?
    """, (solar_start,))
    total_generation = cur.fetchone()[0] or 0

    conn.close()

    # Calculate metrics
    pre_cost = pre_solar[0] or 0
    pre_usage = pre_solar[1] or 0
    post_cost = post_solar[0] or 0
    post_usage = post_solar[1] or 0

    # Net metering: 50% credit on exported power (excess generation)
    net_metering_credit = (total_generation * 0.5) * 0.12  # Rough rate estimate

    # Avoided cost (usage reduction * rate)
    usage_reduction = max(0, pre_usage - post_usage)
    avoided_cost = usage_reduction * 0.12  # Rough rate estimate

    # Total savings (cost reduction + net metering credit)
    total_savings = max(0, pre_cost - post_cost) + net_metering_credit

    return jsonify({
        "solar_start_date": solar_start,
        "pre_solar_cost": round(pre_cost, 2),
        "post_solar_cost": round(post_cost, 2),
        "total_generation_kwh": round(total_generation, 2),
        "total_savings": round(total_savings, 2),
        "net_metering_credit": round(net_metering_credit, 2),
        "avoided_cost": round(avoided_cost, 2),
        "monthly_savings": round(total_savings / 12, 2) if total_savings > 0 else 0
    })


@routes.route('/roi/monthly-comparison')
def roi_monthly_comparison():
    """Get monthly pre/post solar comparison"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("SELECT MIN(DATE(timestamp)) FROM generation")
    solar_start = cur.fetchone()[0]

    if not solar_start:
        conn.close()
        return jsonify([]), 400

    cur.execute("""
        SELECT
            bill_date,
            usage_kwh,
            electrical_charges,
            (CASE WHEN bill_date < ? THEN 'pre' ELSE 'post' END) as period
        FROM billing_history
        ORDER BY bill_date
    """, (solar_start,))

    rows = cur.fetchall()
    conn.close()

    return jsonify([{
        "date": row[0],
        "usage_kwh": row[1],
        "cost": row[2],
        "period": row[3]
    } for row in rows])
