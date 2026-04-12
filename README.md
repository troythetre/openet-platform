**OpenET Agricultural Water Use Analysis Platform**
A web-based platform for analyzing agricultural water usage using satellite evapotranspiration (ET) data from OpenET. Built as an extension of OpenET — adding geospatial analysis, anomaly detection, report generation, and an AI chatbot on top of existing OpenET data.
Developed as part of an M.Eng project at Cornell University in collaboration with Professor Yun Yang (School of Integrative Plant Science), with support from NASA-funded research.

**Features**
Interactive map: Visualize ET data across fields. Anomalies highlighted in red directly on the map.
Time-series analysis: Track water usage trends week by week, month by month, across seasons.
Anomaly detection: Automatically flag unusual spikes or drops in water use using ML. Includes classification to explain each alert.
Report generation: Export downloadable reports linked to OpenET data for a given field or time period.
AI chatbot: Ask questions about the data in plain English (e.g. "How much water did the vineyard use last month?").

**Data Sources**
OpenET API — Satellite-based evapotranspiration data
NLCD — National Land Cover Database (USGS, .tif format)
CDL — Cropland Data Layer (USDA)

Tech Stack

_Backend_
Python + FastAPI
PostgreSQL + PostGIS

_Data & Analysis_
Pandas / GeoPandas
Rasterio / GDAL
Xarray
Scikit-learn

_Frontend_
React
Leaflet.js
Chart.js

_AI_
LLM API (OpenAI / Claude)

_Infrastructure_
Docker
GitHub

**Project Structure**
openet-platform/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── routes/              # API route handlers
│   │   ├── et_data.py       # OpenET data endpoints
│   │   ├── anomaly.py       # Anomaly detection endpoints
│   │   └── reports.py       # Report generation endpoints
│   ├── services/            # Business logic
│   ├── models/              # Data models
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/      # React components
│       ├── pages/           # Page views
│       └── App.js
├── data/
│   └── samples/             # Sample data for testing (no large .tif files)
├── notebooks/               # Jupyter notebooks for exploration
├── .env.example             # Example env file (copy to .env and fill in)
├── .gitignore
├── docker-compose.yml
└── README.md




