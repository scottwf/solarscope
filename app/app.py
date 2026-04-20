"""Main Flask application serving JSON APIs and the dashboard.

All routes are protected by a simple session based authentication system. The
"/login" route serves a small login form and stores the logged in user in the
session. Credentials are stored in the SQLite database with hashed passwords.
"""

from flask import (
    Flask, request, jsonify, send_from_directory,
    session, redirect, url_for, render_template
)
from functools import wraps
import sqlite3
import os
import logging
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

load_dotenv()

DB_FILE = os.getenv('DATABASE_URL', 'db/power_data.db')

os.makedirs('db', exist_ok=True)
os.makedirs('logs', exist_ok=True)
os.makedirs('upload', exist_ok=True)

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'change-me-in-production')

# Register routes Blueprint
from routes import routes, import_generation_for_range, set_setting
app.register_blueprint(routes)

# Background scheduler for automatic SolarEdge sync
def solar_sync_job():
    try:
        # Find the last record we have in the database
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("SELECT MAX(timestamp) FROM generation")
        last_record = cur.fetchone()[0]
        conn.close()

        # Determine the start date for sync
        if last_record:
            # Data exists: backfill from day of last record to today
            last_date = datetime.strptime(last_record[:10], '%Y-%m-%d').date()
            start_date = last_date.strftime('%Y-%m-%d')
        else:
            # No data: use solar installation date or default to 30 days ago
            install_date = get_setting('solar_install_date')
            if install_date:
                start_date = install_date
            else:
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

        end_date = datetime.now().strftime('%Y-%m-%d')

        # Only sync if there's a date range to fill
        if start_date <= end_date:
            if import_generation_for_range(start_date, end_date):
                set_setting('solaredge_last_update', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    except Exception as e:
        log_event(f"Solar sync job error: {e}")

scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(solar_sync_job, 'interval', minutes=15)
scheduler.start()

def get_user(username):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, username, password_hash FROM users WHERE username=?", (username,))
    rows = cur.fetchall()
    conn.close()
    return dict(rows[0]) if rows else None


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return wrapper


@app.before_request
def require_login():
    # Allow unauthenticated access to login page and static files
    # Allow authenticated API calls from dashboard
    if request.endpoint in {'login', 'static', 'routes.view_log'}:
        return
    if not session.get('user_id'):
        return redirect(url_for('login'))

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
        return render_template('login.html', error='Invalid credentials'), 401
    return render_template('login.html')


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


@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/admin')
@login_required
def admin():
    return render_template('admin.html')

# ========== RUN APP ==========
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=True)
