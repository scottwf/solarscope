# SolarScope Roadmap

## 2025 Roadmap & Milestones

### ✅ Core Features
- Modular Flask backend (Blueprints, session auth)
- File upload and robust CSV import (SaskPower, ZIP/CSV)
- Usage data import and display
- Logging and error handling
- Chart.js v4 dashboard integration (usage & solar bar chart)
- Tailwind CSS responsive/mobile-first layout
- AJAX chart updates (date navigation, day/week toggle, summary cards)
- Dashboard chart, summary cards, and navigation are working and bug-free as of June 2025
- Admin page reorganized into **Settings** and **Functions & Tools** sections; see `docs/admin_refactor_instructions.md`
- **Admin UI/UX redesign (2025-06): grouped settings, inline help, improved error feedback, upload/download workflow**
- **Weather location validation and user feedback (2025-06)**
- **Automated SolarEdge background sync (2025-06)**
### 🔜 Next Steps
- [x] Add chartjs-plugin-zoom for mobile pinch/zoom
- [ ] Sticky summary card for daily totals (mobile UX)
- [x] Button group filters ("Today", "This Week", etc.)
- [ ] Live updating (HTMX or Flask-Sock)
- [ ] Enhanced error handling and user feedback (ongoing)
- [ ] Polish dashboard for mobile and desktop
- [ ] Sunrise/sunset and daylight info on dashboard
- [ ] Automated weather data import

### 💡 Ideas
- Weather overlay on usage/generation graphs
- Export graphs as images
- User settings and theme customization
---

## Tech Stack
- Flask (Python)
- Chart.js v4 (JS)
- Tailwind CSS
- AJAX/HTMX
- SQLite

---

## How to Contribute
- See README for setup and development instructions.
- PRs and issues welcome!


This project aims to provide a small web dashboard for viewing SaskPower usage
data alongside SolarEdge generation data. The following roadmap outlines
short‑term clean‑up tasks and longer term features.

## 1. Code Clean‑up (done)
- Remove truncated lines left over from terminal copies.
- Ensure all source files end with newlines.

## 2. Authentication
- Add simple username/password protection for all web routes.
- Store credentials in the database so the user can change them from the admin
  interface.
- Use hashed passwords (e.g. `werkzeug.security.generate_password_hash`).

## 3. CSV Upload & SolarEdge Settings
- Build an admin page with a form to upload SaskPower CSV or ZIP files.
- Allow entry of SolarEdge API key and site ID; store these in the database.
- After uploading usage data, automatically fetch matching solar generation via
the SolarEdge API and sunrise/sunset via Open‑Meteo.

## 4. Database Schema Updates
- Create a new `settings` table for API keys and login credentials.
- Add columns to `usage` for `peak_demand` and other metrics if required.

## 5. Dashboard Enhancements
- Display a combined graph of usage and generation on the home page.
- Add filters to switch between daily and weekly views.
- Show totals and simple statistics below the graph.

## 6. Historical Imports
- Provide scripts or cron jobs to backfill solar generation and weather data.

## 7. Packaging & Deployment
- Provide a setup script that installs Python dependencies (Flask, pandas,
  requests, etc.)
- Document how to run the Flask app via systemd or a process manager on a
  Raspberry Pi.

## 8. Future Ideas
- Add mobile friendly styling.
- Expose an API endpoint for exporting combined data as CSV.
- Consider caching SolarEdge requests to avoid rate limits.


