import json
import os
from collections import defaultdict
from datetime import datetime

import requests
from database import ETCache, QueryLog, SessionLocal
from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

router = APIRouter()

OPENET_BASE_URL = "https://openet-api.org"


def detect_anomalies(data: list) -> list:
    from collections import defaultdict

    # Group by month number (1-12)
    monthly = defaultdict(list)
    for d in data:
        month = int(d["time"][5:7])
        monthly[month].append(d["et"])

    # Calculate seasonal baseline per month
    baseline = {}
    for month, values in monthly.items():
        mean = sum(values) / len(values)
        std = (
            (sum((v - mean) ** 2 for v in values) / len(values)) ** 0.5
            if len(values) > 1
            else 0
        )
        baseline[month] = {"mean": mean, "std": std}

    result = []
    for d in data:
        month = int(d["time"][5:7])
        b = baseline[month]
        mean = b["mean"]
        std = b["std"]

        # Z-score for anomaly detection
        z_score = (d["et"] - mean) / std if std > 0 else 0
        anomaly = abs(z_score) > 1.0

        # Normalized ET — percentage of monthly baseline
        # 100% = exactly average, 150% = 50% above average, 50% = half the average
        normalized = round((d["et"] / mean * 100), 1) if mean > 0 else 100.0

        result.append(
            {
                "time": d["time"],
                "et": d["et"],
                "mean": round(mean, 3),
                "z_score": round(z_score, 3),
                "normalized": normalized,  # % of baseline
                "anomaly": anomaly,
                "anomaly_type": "high"
                if z_score > 1.0
                else "low"
                if z_score < -1.0
                else "normal",
            }
        )
    return result


def get_cache_key(longitude, latitude, start_date, end_date):
    return f"{round(longitude, 4)}_{round(latitude, 4)}_{start_date}_{end_date}"


@router.get("/et/point")
def get_et_point(
    longitude: float = -121.36322,
    latitude: float = 38.87626,
    start_date: str = "2021-01-01",
    end_date: str = "2023-12-31",
):
    db: Session = SessionLocal()

    try:
        # Check cache first
        cached = (
            db.query(ETCache)
            .filter(
                ETCache.longitude == round(longitude, 4),
                ETCache.latitude == round(latitude, 4),
                ETCache.start_date == start_date,
                ETCache.end_date == end_date,
            )
            .first()
        )

        if cached:
            print(f"CACHE HIT: {longitude}, {latitude}")
            data = json.loads(cached.data)
            return detect_anomalies(data)

        # Not in cache: fetch from OpenET API
        headers = {
            "Authorization": os.getenv("OPENET_API_KEY"),
            "Content-Type": "application/json",
        }
        payload = {
            "date_range": [start_date, end_date],
            "interval": "monthly",
            "geometry": [longitude, latitude],
            "model": "Ensemble",
            "variable": "ET",
            "reference_et": "gridMET",
            "units": "in",
            "file_format": "JSON",
        }
        response = requests.post(
            f"{OPENET_BASE_URL}/raster/timeseries/point",
            json=payload,
            headers=headers,
            timeout=60,
        )

        # Log the query
        log = QueryLog(
            longitude=round(longitude, 4),
            latitude=round(latitude, 4),
            start_date=start_date,
            end_date=end_date,
            success=response.status_code == 200,
        )
        db.add(log)
        db.commit()

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        data = response.json()
        print(f"API CALL: {longitude}, {latitude}")

        # Save to cache
        cache_entry = ETCache(
            longitude=round(longitude, 4),
            latitude=round(latitude, 4),
            start_date=start_date,
            end_date=end_date,
            data=json.dumps(data),
        )
        db.add(cache_entry)
        db.commit()

        return detect_anomalies(data)

    finally:
        db.close()
