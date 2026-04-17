# OpenET Agricultural Water Use Analysis Platform

A web-based platform for analyzing agricultural water usage using satellite evapotranspiration (ET) data from [OpenET](https://etdata.org/). Built as an extension of OpenET — adding geospatial analysis, anomaly detection, report generation, and an AI chatbot on top of existing OpenET data.

Developed as part of an M.Eng project at Cornell University in collaboration with Professor Yun Yang (School of Integrative Plant Science), with support from NASA-funded research.

---

## Current Status

**Active development — started April 2026**

### ✅ Completed
- FastAPI backend with OpenET API integration
- Interactive map (Leaflet.js) with click-to-chart ET data
- ET heatmap overlay showing intensity across a region
- Location search (type any city or address)
- Monthly time-series bar chart with anomaly color coding
- ML-based anomaly detection (z-score) with high/low classification
- CSV report generation with anomaly data, exported directly to Excel
- Anomaly markers on map (red = anomaly, green = normal)
- Polished dark UI with stats row (total ET, avg monthly, anomaly count)
- PostgreSQL 17 + PostGIS database with ET response caching and query logging

### 🔄 In Progress
- AI chatbot (ask questions about ET data in plain English)
- Cornell vineyard as default location
- UI polish and cleanup

### 📋 Planned
- NLCD and CDL data layers (land cover and crop type overlay)
- Multi-field comparison
- Cornell web hosting setup
- Pilot testing on Cornell campus vineyard (Summer 2026)

---

## Features

- **Interactive map** — Click anywhere to view ET data for that location. Anomalies highlighted with red markers directly on the map.
- **ET heatmap** — Color gradient overlay showing ET intensity across the visible region (blue = low, red = high).
- **Location search** — Type any location to jump there and load the heatmap.
- **Time-series chart** — Monthly ET bar chart with anomaly color coding (red = high anomaly, yellow = low anomaly).
- **Stats summary** — Total ET, average monthly ET, and anomaly count shown above the chart.
- **Anomaly detection** — ML-based z-score detection flags unusual spikes or drops in water use.
- **Report generation** — Export a CSV report with ET data, z-scores, and anomaly flags for any location and date range.
- **Database caching** — API responses cached in PostgreSQL to preserve monthly quota.
- **AI chatbot** *(coming soon)* — Ask questions about the data in plain English.

---

## Data Sources

- [OpenET API](https://openet-api.org/) — Satellite-based evapotranspiration data
- [NLCD](https://www.mrlc.gov/) — National Land Cover Database (USGS, .tif format) *(planned)*
- [CDL](https://www.nass.usda.gov/Research_and_Science/Cropland/CDLS.php) — Cropland Data Layer (USDA) *(planned)*

---

## Tech Stack

**Backend**
- Python + FastAPI
- PostgreSQL 17 + PostGIS
- SQLAlchemy + Alembic (ORM + migrations)

**Data & Analysis**
- Pandas / GeoPandas
- Rasterio / GDAL *(planned)*
- Xarray *(planned)*
- Scikit-learn (anomaly detection)

**Frontend**
- Leaflet.js (interactive map + heatmap)
- Chart.js (time-series charts)
- React *(planned)*

**AI**
- Claude API *(planned)*

**Infrastructure**
- ET response caching — API results stored in DB to preserve monthly quota
- Query logging — all API requests tracked in database
- Docker *(planned)*
- Cornell web hosting *(planned)*
- GitHub

---

## Project Structure

```
openet-platform/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── database.py          # SQLAlchemy models + DB setup
│   ├── routes/
│   │   ├── et_data.py       # OpenET data + anomaly detection + caching
│   │   ├── visualize.py     # Interactive map + chart UI
│   │   ├── reports.py       # CSV report generation
│   │   └── anomaly.py       # Anomaly endpoints (planned)
│   ├── .env                 # API keys (never committed)
│   └── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL 17
- PostGIS 3.x
- OpenET API key — get one at [account.etdata.org](https://account.etdata.org/settings/api)

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
OPENET_API_KEY=your_api_key_here
DATABASE_URL=postgresql://your_username@localhost:5432/openet_db
```

### 3. Set up the database

Make sure PostgreSQL is running:
```bash
brew services start postgresql@17
```

Create the database and enable PostGIS:
```bash
psql postgres -c "CREATE DATABASE openet_db;"
psql openet_db -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

Initialize the tables:
```bash
cd backend
python database.py
```

### 4. Set up the backend

```bash
cd backend
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### 5. Open the platform

Go to `http://localhost:8000/api/chart` in your browser.

---

## Usage

- **Search** a location (e.g. "Fresno CA", "Ithaca NY") and press Enter or click Go
- **Click** anywhere on the map to load ET data for that point
- **View** the monthly ET chart on the right — anomalies highlighted in red/yellow
- **Check stats** — total ET, average monthly ET, and anomaly count shown above the chart
- **Update Heatmap** to load the ET intensity overlay for the visible region
- **Download CSV Report** to export the data for the selected location

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/et/point` | GET | Get monthly ET data for a lat/lng point (cached) |
| `/api/reports/csv` | GET | Download CSV report for a location |
| `/api/chart` | GET | Open the interactive map UI |
| `/health` | GET | Check API status and key loading |
| `/docs` | GET | Interactive API documentation |

---

## Database Schema

| Table | Description |
|-------|-------------|
| `et_cache` | Cached OpenET API responses — avoids re-fetching same location |
| `query_log` | Logs all API requests with success/fail status |
| `saved_locations` | Saved named locations (planned feature) |
| `spatial_ref_sys` | PostGIS spatial reference system table |

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
