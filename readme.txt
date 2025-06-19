python3 /home/scott/solar-monitor/app/app.py

Add links:
	https://www.saskpower.com/profile/my-dashboard/my-reports/download-data
	create an iOS shortcut to pull the data from here instead of SolarEdge
	
	
Check:
	Is the new data being pulled in on 
	Is the data correct because generation doesn't seem to line up with time of day


Solar Monitor Readme
Solar Monitor README

This project provides a solar monitoring dashboard for Raspberry Pi, combining:

Local power usage data (from SaskPower CSV files)
SolarEdge generation data (via API)
Weather and daylight overlays (from Open-Meteo)

It supports:
	Auto-import of CSV files for power usage
	Periodic solar generation import
	Sunrise/sunset shading
	A Flask-powered dashboard with daily/weekly views

🧰 System Requirements
Raspberry Pi 4 (recommended)
Raspberry Pi OS (Debian Bookworm or later)
Python 3.9+
Internet access (for API calls and setup)

📦 Install Dependencies
sudo apt update && sudo apt install -y \
  python3 python3-pip python3-venv sqlite3 cron unzip curl

📁 Folder Structure

/home/scott/solar-monitor/
├── app/                # Flask app & routes
│   ├── app.py
│   ├── routes.py
│   └── dashboard.html
├── scripts/            # CSV/solar/weather import scripts
│   ├── import_usage.py
│   ├── import_generation_history.py
│   ├── import_weather_history.py
│   └── watch_csv_folder.py
├── data/               # CSV drop folder
├── db/                 # Contains power_data.db
├── static/             # JS/CSS (if needed)
├── .env                # Environment variables for API keys (optional)
├── README.md           # You're reading it
🔧 Permissions and Setup

# Create directories and set permissions
mkdir -p /home/scott/solar-monitor/{data,db}
chmod +x /home/scott/solar-monitor/scripts/*.py

# Optional: ensure your user owns everything
sudo chown -R scott:scott /home/scott/solar-monitor

⚙️ Set Up the Database

sqlite3 /home/scott/solar-monitor/db/power_data.db < /home/scott/solar-monitor/scripts/init_db.sql
If needed, run table creation manually:

CREATE TABLE usage (timestamp TEXT PRIMARY KEY, power REAL);
CREATE TABLE generation (timestamp TEXT PRIMARY KEY, energy REAL);
CREATE TABLE weather (date TEXT PRIMARY KEY, sunrise TEXT, sunset TEXT);
🔁 Auto-Import CSV (watch folder)

Create this systemd service to auto-import files dropped into data/:

/etc/systemd/system/solar-csv-watcher.service
[Unit]
Description=Solar Monitor - Watch CSV Folder

[Service]
ExecStart=/usr/bin/python3 /home/scott/solar-monitor/scripts/watch_csv_folder.py
WorkingDirectory=/home/scott/solar-monitor/scripts/
Restart=always
User=scott

[Install]
WantedBy=multi-user.target
sudo systemctl daemon-reexec
sudo systemctl enable --now solar-csv-watcher.service

🕒 Set Up Cron Jobs
Edit with crontab -e and add:

# Pull SolarEdge generation data hourly
0 * * * * /usr/bin/python3 /home/scott/solar-monitor/scripts/import_generation_hourly.py >> /home/scott/solar-monitor/logs/gen.log 2>&1

# (Optional) Update weather overlay daily
@daily /usr/bin/python3 /home/scott/solar-monitor/scripts/import_weather_history.py --incremental

▶️ Run the Dashboard
cd /home/scott/solar-monitor/app
python3 app.py
Visit: http://<your-pi-ip>:5000/dashboard

🔐 API Keys and Environment Variables

Create a .env file in the root folder:

# .env file at /home/scott/solar-monitor/
SOLAREDGE_SITE_ID=2563089
SOLAREDGE_API_KEY=your_api_key_here
LATITUDE=52.1332
LONGITUDE=-106.67
TIMEZONE=America/Regina
Your scripts can then load these using:

from dotenv import load_dotenv
import os

load_dotenv()
site_id = os.getenv("SOLAREDGE_SITE_ID")
api_key = os.getenv("SOLAREDGE_API_KEY")
Install support:

pip install python-dotenv
🧪 Flask Developer Setup

For easier dev/testing:

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install flask python-dotenv requests

# Run Flask in dev mode
export FLASK_APP=app.py
export FLASK_ENV=development
flask run --host=0.0.0.0

✅ Final Checklist
Need help? Run logs and share:
   journalctl -u solar-csv-watcher.service --no-pager


