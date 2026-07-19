# Agricultural Water Use Analysis Platform

A web-based platform for analyzing agricultural water usage using satellite evapotranspiration (ET) data from OpenET. Built as an extension of OpenET — adding geospatial analysis, anomaly detection, multi-field comparison, user accounts, and report generation on top of the underlying OpenET data.

Developed as part of an M.Eng project at Cornell University in collaboration with Professor Yun Yang (School of Integrative Plant Science), with support from NASA-funded research.

Product name is still undecided — currently referred to internally as the "Water Use Analysis" platform.

---

## Current Status

**Active development — started April 2026**

### Completed

- FastAPI backend with OpenET API integration, response caching, and query logging
- Satellite imagery map (Esri World Imagery) with label overlay
- Interactive map — click any point or draw a polygon/rectangle to load ET data for that field
- Polygon size cap (5 km² max) to keep sampling meaningful and protect API quota
- Seasonal anomaly detection — compares each month's ET to that same calendar month across all years in range, not just an annual average
- Normalized anomaly display — shows percent of monthly baseline (e.g. "July 2022: 121.7% of average")
- Multi-year comparison chart (bar chart, one color per year, anomalous months highlighted)
- ET heatmap with two explicit modes: **Intensity** (total ET, raw water-use magnitude) and **Anomaly Severity** (worst z-score at each location) — built from cached data only, so it never touches OpenET quota
- NDVI vegetation layer (NASA GIBS MODIS Terra)
- USDA CDL crop-type layer (via CropScape WMS, rendered as a per-viewport image overlay to work around the service's EPSG:4326-only projection)
- U.S. Drought Monitor layer (NDMC/USDA/NOAA, via a tiled ArcGIS Online service) — shows current-week drought conditions
- Multi-field comparison mode — add several fields (by click, draw, or from saved fields/sets), then compare them on one overlaid monthly-average line chart plus a stats table
- User accounts — email/password signup and login, and Google Sign-In (Apple Sign-In was evaluated and intentionally skipped due to its $99/year developer program cost)
- Per-user saved fields, saved comparison sets, and automatic search history (click any past search to reload it)
- CSV report export (uses the same cache and anomaly logic as the live charts, so exports match what's on screen)
- Rule-based AI Assistant — three preset questions ("Summarize this field," "Explain anomalies," "Compare years") answered instantly from already-loaded chart data, entirely client-side, no external API or cost
- Redesigned frontend: a two-row header with an actual Map/Compare tab bar and a compact layer-toggle toolbar, replacing an earlier single row of buttons

### In Progress

- Pilot testing on the Cornell campus vineyard (Summer 2026)
- Data retention policy for cached and user data (open question, not yet decided)

### Planned

- Cornell web hosting deployment
- Revisiting a full conversational AI assistant if/when API credits are funded (a Claude-API-backed chatbot endpoint exists in the codebase but is not currently wired into the frontend, in favor of the free rule-based version above)

---

## Data Sources

- [OpenET API](https://openet-api.org/) — satellite-based evapotranspiration data
- NASA GIBS — MODIS Terra NDVI Monthly
- Esri World Imagery — satellite base map tiles
- USDA NASS CropScape — Cropland Data Layer (crop type)
- NDMC / USDA / NOAA — U.S. Drought Monitor

---

## Tech Stack

**Backend**
- Python + FastAPI
- PostgreSQL (SQLAlchemy ORM; schema changes applied manually via SQL, no migration framework yet)
- PyJWT + bcrypt — session tokens and password hashing
- google-auth — Google ID token verification

**Frontend**
- Vanilla HTML/CSS/JavaScript, served directly from FastAPI (no separate frontend build or framework)
- Leaflet.js + Leaflet.draw + Leaflet.heat — map, polygon drawing, heatmap
- Chart.js — monthly and comparison charts
- Google Identity Services — Sign in with Google button

**Infrastructure**
- ET response caching in Postgres — avoids re-fetching the same location/date range, preserving OpenET's monthly quota
- Query logging — all live OpenET API requests tracked with success/failure status
- GitHub

---

## Project Structure

```
openet-platform/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── database.py          # SQLAlchemy models (users, fields, history, comparison sets, cache)
│   ├── auth_utils.py        # Password hashing, JWT issuance/verification
│   ├── routes/
│   │   ├── auth.py          # Signup, login, Google sign-in
│   │   ├── et_data.py       # OpenET data, anomaly detection, caching, fields/history/comparison-set endpoints
│   │   ├── visualize.py     # Full interactive map UI (map, layers, auth, compare, history, AI assistant)
│   │   ├── reports.py       # CSV report generation
│   │   └── chatbot.py       # Claude-API chatbot endpoint (not currently used by the frontend)
│   ├── .env                 # API keys and secrets (never committed)
│   └── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL
- OpenET API key — get one at [account.etdata.org](https://account.etdata.org/settings/api)
- A Google Cloud OAuth Client ID (free) — required for Google Sign-In; see below

### 1. Clone the repo

```bash
git clone https://github.com/troythetre/openet-platform.git
cd openet-platform
```

### 2. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:
```
OPENET_API_KEY=your_openet_api_key
DATABASE_URL=postgresql://your_username@localhost:5432/openet_db
GOOGLE_CLIENT_ID=your_google_oauth_client_id
JWT_SECRET=a_long_random_string
```

Generate a `JWT_SECRET` with:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Set up Google Sign-In (free)

- Go to [console.cloud.google.com](https://console.cloud.google.com) → APIs & Services → Credentials
- Create an OAuth Client ID, type "Web application"
- Add `http://localhost:8000` as an authorized JavaScript origin
- Copy the Client ID into `.env` as `GOOGLE_CLIENT_ID`

### 4. Set up the database

Make sure PostgreSQL is running, then:
```bash
psql postgres -c "CREATE DATABASE openet_db;"
```

### 5. Set up the backend

```bash
cd backend
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install pyjwt bcrypt google-auth "pydantic[email]"
uvicorn main:app --reload
```

On first run, `init_db()` creates all tables automatically. If you're upgrading from an earlier version of this project that predates user accounts, run this once to add the required column to your existing data:
```bash
psql openet_db -c "ALTER TABLE saved_locations ADD COLUMN user_id INTEGER REFERENCES users(id);"
```

### 6. Open the platform

Go to `http://localhost:8000/api/chart` in your browser.

---

## Usage

- **Search** a location and press Enter or click Go
- **Click** any field on the map, or draw a polygon/rectangle, to load its ET data
- **Toggle layers** — NDVI, Crop Type, Drought, and Heatmap (with Intensity/Anomaly modes) — from the toolbar
- **Switch to the Compare tab** to add multiple fields and view them side by side on one chart
- **Sign in** to save fields, save comparison sets, and build up search history
- **Download CSV Report** to export the currently loaded field's data
- **Ask the AI Assistant** one of three preset questions about the loaded field — answered instantly, no API cost

### Key API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/et/point` | GET | Monthly ET data for a lat/lng point (cached) |
| `/api/et/compare` | POST | ET data and stats for multiple fields at once |
| `/api/fields` | GET/POST | List or save a named field (requires login) |
| `/api/history` | GET/DELETE | List or clear search history (requires login) |
| `/api/comparison-sets` | GET/POST | List or save a named comparison set (requires login) |
| `/api/auth/signup` `/api/auth/login` `/api/auth/google` | POST | Account creation and sign-in |
| `/api/reports/csv` | GET | Download a CSV report for a location |
| `/api/chart` | GET | Open the interactive map UI |
| `/health` | GET | Check API status and key loading |
| `/docs` | GET | Interactive API documentation |

---

## Database Schema

| Table | Description |
|-------|-------------|
| `et_cache` | Cached OpenET API responses — avoids re-fetching the same location/date range |
| `query_log` | Logs all live OpenET API requests with success/fail status |
| `users` | User accounts (email/password and/or linked Google account) |
| `saved_locations` | Named fields saved by a user |
| `search_history` | Every field a logged-in user has looked up |
| `comparison_sets` | Named, saved groups of fields for repeat multi-field comparison |

---

## Pilot Testing

The platform will be piloted on a vineyard on Cornell's campus in Summer 2026.

---

## Project Info

- **Student:** Troy Wu — M.Eng Computer Science, Cornell University
- **Advisor:** Professor Yun Yang, School of Integrative Plant Science, Cornell University
- **Enrollment:** CS 5999
- **Timeline:** May 2026 – August 2026
- **GitHub:** github.com/troythetre/openet-platform

---

## License

To be determined.
