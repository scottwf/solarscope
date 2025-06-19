"""Main Flask application serving JSON APIs and the dashboard.

All routes are protected by a simple session based authentication system. The
"/login" route serves a small login form and stores the logged in user in the
session. Credentials are stored in the SQLite database with hashed passwords.
"""

from flask import (
    Flask, request, jsonify, send_from_directory,
    session, redirect, url_for
)
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

DB_FILE = '/home/scott/solar-monitor/db/power_data.db'

app = Flask(__name__)
app.secret_key = 'change-me'

def query_db(query, params=(), as_dict=True):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row if as_dict else None
    cur = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows] if as_dict else rows


def get_user(username):
    rows = query_db(
        "SELECT id, username, password_hash FROM users WHERE username=?",
        (username,),
    )
    return rows[0] if rows else None


def login_required(func):
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('login'))
        return func(*args, **kwargs)

    return wrapper


@app.before_request
def require_login():
    if request.endpoint in {'login', 'static'}:
        return
    if not session.get('user_id'):
        return redirect(url_for('login'))

# ========== USAGE DATA ==========

@app.route('/power-usage')
@login_required
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
@login_required
def summary_daily():
    query = """
    SELECT DATE(timestamp) AS date, ROUND(SUM(power), 2) AS total_power
    FROM usage
    GROUP BY DATE(timestamp)
    ORDER BY DATE(timestamp)
    """
    return jsonify(query_db(query))

@app.route('/summary/hourly')
@login_required
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
@login_required
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
@login_required
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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = get_user(username)
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        return 'Invalid credentials', 401
    return send_from_directory('static', 'login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/admin/change-password', methods=['POST'])
@login_required
def change_password():
    new_password = request.form.get('password')
    if not new_password:
        return jsonify({'error': 'password required'}), 400
    user_id = session['user_id']
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        'UPDATE users SET password_hash=? WHERE id=?',
        (generate_password_hash(new_password), user_id)
    )
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})


@app.route('/dashboard')
@login_required
def dashboard():
    return send_from_directory('static', 'dashboard.html')

# ========== RUN APP ==========
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
