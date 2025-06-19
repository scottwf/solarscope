# SolarScope

A modern, mobile-friendly dashboard for visualizing and analyzing your solar and utility (SaskPower) data.

---

## 🛠️ Tech Stack
- **Backend:** Flask (Python)
- **Frontend Graphs:** Chart.js v4 (responsive, mobile-friendly)
- **Styling:** Tailwind CSS
- **Dynamic Data:** AJAX (vanilla JS or HTMX)
- **CSV Import:** Supports SaskPower 15-minute interval data
- **Optional:** chartjs-plugin-zoom for advanced touch/pinch/zoom

---

## 🚀 Quickstart
1. **Clone and install dependencies:**
   ```bash
   git clone https://github.com/yourusername/solarscope.git
   cd solarscope
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Initialize the database:**
   ```bash
   python3 scripts/init_db.py
   ```
3. **Run the server:**
   ```bash
   python3 app/app.py
   ```
4. **Visit:**
   - Dashboard: [http://localhost:5005/dashboard](http://localhost:5005/dashboard)
   - API: `/power-usage`, `/solar-generation`, `/summary/daily`, etc.

---

## 📊 Features
- **Interactive graphs** for power usage and solar generation
- **Mobile-first**: Responsive layout, touch-friendly graphs
- **Upload SaskPower CSV/ZIP**: Drag-and-drop or select your data file
- **Daily/weekly/monthly summaries**
- **Download your data as CSV**

---

## 🖼️ Architecture
- **Flask** serves HTML, API endpoints, and static files
- **Chart.js** renders graphs (line, bar, area)
- **Tailwind CSS** for layout, spacing, and mobile UX
- **AJAX/HTMX** fetches new data for charts when user changes date or toggles filters

---

## 🔧 Extending/Customizing
- Add new chart types: Edit the dashboard JS and add new Flask endpoints as needed
- Add new data sources: Implement new importers (see `routes.py`)
- Style tweaks: Edit Tailwind classes in the HTML

---

## 📱 Mobile UX Tips
- Use `w-full` and `h-64` on chart containers
- Add horizontal scroll (`overflow-x-auto`) for long time series
- Use sticky summary cards for quick daily totals
- Use button groups for quick date filters ("Today", "This Week", etc.)

---

## 📅 Roadmap (see ROADMAP.md for details)
- [x] Modular Flask backend
- [x] File upload and CSV import
- [x] Chart.js v4 integration
- [ ] SolarEdge API integration
- [ ] Enhanced mobile dashboard
- [ ] Live updating (HTMX or Flask-Sock)

---

## License
MIT
2025-04-10 06:15:00,72.3