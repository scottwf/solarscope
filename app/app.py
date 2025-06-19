from flask import Flask, request, jsonify, send_from_directory
import sqlite3

DB_FILE = '/home/scott/solar-monitor/db/power_data.db'

app = Flask(__name__)

def query_db(query, params=(), as_dict=True):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row if as_dict else None
    cur = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows] if as_dict else rows

# ========== USAGE DATA ==========

@app.route('/power-usage')
def power_usage():
    date = request.args.get('date')
    start = request.args.get('start')
    end = request.args.get('end')
    hour = request.args.get('hour')
    between = request.args.get('between')

    where = []
    params = []

    if date:
        where.append("DATE(timestamp) = DATE(?)")
        params.append(date)
    if start:
        where.append("timestamp >= ?")
        params.append(start)
    if end:
        where.append("timestamp <= ?")
        params.append(end)
    if hour:
        where.append("CAST(STRFTIME('%H', timestamp) AS INTEGER) = ?")
        params.append(int(hour))
    if between:
        try:
            t1, t2 = between.split('-')
            where.append("TIME(timestamp) BETWEEN TIME(?) AND TIME(?)")
            params += [t1.strip(), t2.strip()]
        except:
            pass

    clause = "WHERE " + " AND ".join(where) if where else ""
    query = f"SELECT timestamp, power FROM usage {clause} ORDER BY timestamp ASC"
    return jsonify(query_db(query, params))

@app.route('/summary/daily')
def summary_daily():
    query = """
    SELECT DATE(timestamp) AS date, ROUND(SUM(power), 2) AS total_power
    FROM usage
    GROUP BY DATE(timestamp)
    ORDER BY DATE(timestamp)
    """
    return jsonify(query_db(query))

@app.route('/summary/hourly')
def summary_hourly():
    query = """
    SELECT STRFTIME('%H', timestamp) AS hour, ROUND(AVG(power), 3) AS avg_power
    FROM usage
    GROUP BY STRFTIME('%H', timestamp)
    ORDER BY hour
    """
    return jsonify(query_db(query))

# ========== SOLAR GENERATION ==========

@app.route('/solar-generation')
def solar_generation():
    start = request.args.get('start')
    end = request.args.get('end')

    where = []
    params = []
    if start:
        where.append("timestamp >= ?")
        params.append(start)
    if end:
        where.append("timestamp <= ?")
        params.append(end)

    clause = "WHERE " + " AND ".join(where) if where else ""
    query = f"SELECT timestamp, energy FROM generation {clause} ORDER BY timestamp ASC"
    return jsonify(query_db(query, params))

# ========== WEATHER DATA ==========

@app.route('/weather')
def weather_data():
    start = request.args.get('start')
    end = request.args.get('end')

    if not start or not end:
        return jsonify({"error": "Missing start or end"}), 400
    query = """
    SELECT date, sunrise, sunset
    FROM weather
    WHERE date BETWEEN ? AND ?
    ORDER BY date
    """
    return jsonify(query_db(query, [start, end]))

# ========== DASHBOARD VIEW ==========

@app.route('/dashboard')
def dashboard():
    return send_from_directory('.', 'dashboard.html')

# ========== RUN APP ==========
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
