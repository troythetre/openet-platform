# OpenET Agricultural Water Use Analysis Platform

A web-based platform for analyzing agricultural water usage using satellite evapotranspiration (ET) data from OpenET. Built as an extension of OpenET — adding geospatial analysis, anomaly detection, report generation, and an AI chatbot on top of existing OpenET data.
Developed as part of an M.Eng project at Cornell University in collaboration with Professor Yun Yang (School of Integrative Plant Science), with support from NASA-funded research.

---

## Current Status

**Active development — started April 2026**

### ✅ Completed
- FastAPI backend with OpenET API integration
- Satellite imagery map (Esri World Imagery) with street label overlay
- Interactive map with click-to-chart ET data
- Polygon and rectangle drawing tool — draw a custom area to sample ET data
- Multi-point polygon sampling — averages ET across 9 points inside drawn polygon
- ET heatmap overlay showing intensity across a region (blue = low, red = high)
- Location search (type any city or address)
- Multi-year comparison chart — 2021, 2022, 2023 side by side per month
- Seasonal anomaly detection — compares each month to same month across years
- Normalized anomaly display — shows % of monthly baseline (e.g. 161% = 61% above average)
- NDVI vegetation layer (NASA GIBS MODIS) — shows how green/vegetated each area is
- CSV report generation with anomaly data, exported directly to Excel
- Anomaly markers on map (red = anomaly, green = normal)
- Polished dark UI with stats row (total ET, avg monthly, anomaly count)
- PostgreSQL 17 + PostGIS database with ET response caching and query logging
- AI chatbot (Claude API) — built and integrated

### 🔄 In Progress
- AI chatbot billing credits (built, needs Anthropic credits to activate)
- Pilot testing on Cornell campus vineyard

### 📋 Planned
- NLCD and CDL data layers (land cover and crop type overlay)
- Multi-field comparison
- Cornell web hosting setup
- Pilot testing on Cornell campus vineyard (Summer 2026)

---

## Features

1. Satellite imagery — Real satellite map showing farmland, water, vineyards and vegetation clearly
2. Polygon drawing — Draw a custom polygon or rectangle on the map to analyze a specific area. ET is sampled at 9 points inside the polygon and averaged for accuracy
3. ET heatmap — Color gradient overlay showing ET intensity across the visible region
4. Location search — Type any location to jump there instantly
5. Multi-year chart — Monthly ET bar chart comparing 2021, 2022, 2023 side by side
6. Seasonal anomaly detection — Compares each month to the same month across all years (not just annual average)
7. Normalized anomalies — Shows percentage of monthly baseline (e.g. "July 2022: 121.7% of average")
8NDVI layer — Toggle NASA MODIS NDVI vegetation layer to see which areas are most vegetated
8. Stats summary — Total ET, average monthly ET, and anomaly count shown above the chart
9. Report generation — Export a CSV report with ET data, z-scores, normalized values, and anomaly flags
10. Database caching — API responses cached in PostgreSQL to preserve monthly quota
11. AI chatbot — Ask questions about the ET data in plain English (requires Anthropic credits)

---

## Data Sources

- [OpenET API](https://openet-api.org/) — Satellite-based evapotranspiration data
- NASA GIBS — MODIS Terra NDVI Monthly
- Esri World Imagery — Satellite base map tiles
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
- Leaflet.js (interactive map + heatmap + polygon drawing)
- Leaflet.draw (polygon/rectangle drawing tool)
- NASA GIBS NDVI tiles
- Esri satellite imagery tiles
- Chart.js (multi-year comparison charts)
- React *(planned)*

**AI**
- Claude API (Anthropic) — chatbot integration

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
│   │   ├── et_data.py       # OpenET data + seasonal anomaly detection + caching
│   │   ├── visualize.py     # Interactive map + satellite imagery + polygon drawing + NDVI
│   │   ├── reports.py       # CSV report generation
│   │   └── chatbot.py       # AI chatbot (Claude API)
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
