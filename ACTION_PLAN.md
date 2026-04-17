# SolarScope - Action Plan (Post-Critical Fixes)

## ✅ Completed: Critical Fixes
- Removed duplicate routes from app.py (consolidated to routes.py)
- Moved hardcoded secret key to .env file
- Moved SolarEdge API key to settings table
- Implemented weather import stub function
- Created logs directory on app startup
- Initialized database and dependencies
- **App is now running successfully on http://localhost:5005**

---

## 🚀 Phase 1: Make App Fully Functional (HIGH PRIORITY)

### 1.1 Create Login Template
**Status:** NEEDED
- App currently requires `app/templates/login.html`
- Create simple form with username/password inputs
- **Files to create:** `app/templates/login.html`
- **Estimated effort:** 30 minutes

### 1.2 Fix Database Initialization Check
**Status:** NEEDED  
- Add check in `app/app.py` to detect if database is missing
- Guide user to run `scripts/init_db.py` if needed
- **Files to modify:** `app/app.py`
- **Estimated effort:** 15 minutes

### 1.3 Add Error Handling to Frontend
**Status:** NEEDED
- Dashboard JavaScript needs try/catch for API failures
- Add user-friendly error messages (no silent failures)
- **Files to modify:** `app/templates/dashboard.html` (JavaScript section)
- **Estimated effort:** 45 minutes

### 1.4 Add CSV Validation
**Status:** NEEDED
- Validate uploaded CSV files before import
- Check for required columns (Date/DateTime, Time, Power/Consumption)
- Reject invalid files with clear error messages
- **Files to modify:** `app/routes.py` (import_csv function)
- **Estimated effort:** 30 minutes

---

## 🔒 Phase 2: Security Hardening (MEDIUM PRIORITY)

### 2.1 Add CSRF Protection
**Status:** MISSING
- Install Flask-WTF: `pip install Flask-WTF`
- Add CSRF tokens to all forms
- Verify POST/PUT/DELETE requests
- **Files to modify:** `app/app.py`, templates
- **Estimated effort:** 1 hour
- **Why:** Admin panel endpoints vulnerable to cross-site attacks

### 2.2 Add HTTPS/TLS Support
**Status:** MISSING
- Document proxy setup (nginx + Let's Encrypt)
- Add security headers (HSTS, X-Frame-Options, etc.)
- **Files to create:** Deployment guide
- **Estimated effort:** 1.5 hours
- **Why:** Auth tokens sent over HTTP (insecure)

### 2.3 Update Default Credentials
**Status:** WEAK  
- Force password change on first login
- Remove default admin/admin credentials from code
- **Files to modify:** `scripts/init_db.py`, `app/app.py`
- **Estimated effort:** 30 minutes

### 2.4 Implement Rate Limiting
**Status:** MISSING
- Add Flask-Limiter to prevent brute force attacks
- Limit login attempts, API calls
- **Files to modify:** `app/app.py`, `app/routes.py`
- **Estimated effort:** 45 minutes

---

## 🎨 Phase 3: UI/UX Polish (MEDIUM PRIORITY)

### 3.1 Implement Mobile Pinch/Zoom
**Status:** NOT DONE
- Add chartjs-plugin-zoom
- Enable touch-friendly gestures on charts
- **Files to modify:** `app/templates/dashboard.html`
- **Estimated effort:** 1 hour

### 3.2 Add Sticky Summary Card
**Status:** NOT DONE
- Sticky card showing daily totals (mobile UX)
- Visible while scrolling through charts
- **Files to modify:** `app/templates/dashboard.html`
- **Estimated effort:** 45 minutes

### 3.3 Sunrise/Sunset Overlay
**Status:** NOT DONE
- Display sunrise/sunset times on charts
- Use weather data already being imported
- **Files to modify:** `app/templates/dashboard.html` (JavaScript)
- **Estimated effort:** 1.5 hours

### 3.4 Live Data Updates
**Status:** NOT DONE (Roadmap item)
- Implement WebSocket or HTMX polling
- Auto-refresh dashboard every 5 minutes
- **Files to create:** WebSocket handler or HTMX template
- **Estimated effort:** 2 hours

---

## 🧹 Phase 4: Code Quality & Cleanup (LOW PRIORITY)

### 4.1 Remove Unused Static Files
**Status:** CLEANUP
- Delete `app/static/dashboard.html` (duplicated in templates/)
- Delete `app/static/login.html` (duplicated in templates/)
- Keep `.gitignore` rules for `/static/` assets only
- **Files to delete:** `app/static/dashboard.html`, `app/static/login.html`
- **Estimated effort:** 5 minutes

### 4.2 Add Database Existence Check
**Status:** NICE-TO-HAVE
- Detect if `db/power_data.db` exists on startup
- Auto-initialize if missing (call init_db.py logic)
- **Files to modify:** `app/app.py`
- **Estimated effort:** 20 minutes

### 4.3 Update Legacy Import Scripts
**Status:** DEPRECATE or FIX
- Mark `scripts/import_csv.py`, `scripts/import_solar.py` as deprecated
- Remove hardcoded paths/keys
- Update documentation to use CSV upload UI instead
- **Files to update:** `scripts/` (add deprecation notices)
- **Estimated effort:** 30 minutes

### 4.4 Add API Documentation
**Status:** MISSING
- Create OpenAPI/Swagger spec for all endpoints
- Generate interactive API docs at `/api/docs`
- **Files to create:** `api_spec.yaml`
- **Estimated effort:** 2 hours

---

## 📦 Phase 5: Deployment & Documentation (LOW PRIORITY)

### 5.1 Create Docker Configuration
**Status:** MISSING
- Write `Dockerfile` for containerized deployment
- Create `docker-compose.yaml` for easy local dev
- **Files to create:** `Dockerfile`, `docker-compose.yaml`
- **Estimated effort:** 1.5 hours

### 5.2 Create Systemd Service File
**Status:** MISSING
- Template for running on Raspberry Pi
- Auto-start on boot, auto-restart on crash
- **Files to create:** `solarscope.service` (in `docs/`)
- **Estimated effort:** 30 minutes

### 5.3 Write Deployment Guide
**Status:** MISSING
- Step-by-step setup for bare metal, Docker, RPI
- Configuration walkthrough (API keys, location, etc.)
- **Files to create:** `docs/DEPLOYMENT.md`
- **Estimated effort:** 1.5 hours

### 5.4 Create User Guide
**Status:** MISSING
- How to upload SaskPower CSVs
- How to configure SolarEdge API
- How to interpret dashboard
- **Files to create:** `docs/USER_GUIDE.md`
- **Estimated effort:** 1 hour

---

## 📊 Effort & Priority Matrix

| Phase | Priority | Total Effort | Blocking? |
|-------|----------|--------------|-----------|
| Phase 1 (Functional) | HIGH | ~2 hours | YES |
| Phase 2 (Security) | MEDIUM | ~4 hours | No (but important) |
| Phase 3 (UX Polish) | MEDIUM | ~5 hours | No |
| Phase 4 (Cleanup) | LOW | ~1 hour | No |
| Phase 5 (Deploy) | LOW | ~5 hours | No |
| **TOTAL** | — | **~17 hours** | — |

---

## 🎯 Recommended Execution Order

1. **Week 1:** Complete Phase 1 (make app fully functional)
   - Creates usable MVP
   - ~2 hours work

2. **Week 2:** Complete Phase 2 (security hardening)
   - Production-ready baseline
   - ~4 hours work

3. **Week 3:** Complete Phase 3 (UX polish)
   - Better mobile experience
   - ~5 hours work

4. **Ongoing:** Phase 4 & 5 as time permits
   - Cleanup and documentation
   - ~6 hours work

---

## 📝 Notes

- Database schema issue resolved (weather table schema is consistent)
- Legacy import scripts can remain as-is but should be documented as deprecated
- Secret key should be changed in production (.env file)
- CSRF protection and HTTPS are critical before public deployment
- All changes tracked in git with clear commit messages

---

## Quick Start for Testing

```bash
# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 scripts/init_db.py

# Run
python3 app/app.py
# Visit http://localhost:5005
# Login: admin / admin
```

---

**Last Updated:** 2026-04-17  
**Status:** App running, critical issues fixed, ready for Phase 1
