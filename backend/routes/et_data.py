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

    monthly = defaultdict(list)
    for d in data:
        month = int(d["time"][5:7])
        monthly[month].append(d["et"])

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
        z_score = (d["et"] - mean) / std if std > 0 else 0
        anomaly = abs(z_score) > 1.0
        normalized = round((d["et"] / mean * 100), 1) if mean > 0 else 100.0
        result.append(
            {
                "time": d["time"],
                "et": d["et"],
                "mean": round(mean, 3),
                "z_score": round(z_score, 3),
                "normalized": normalized,
                "anomaly": anomaly,
                "anomaly_type": "high"
                if z_score > 1.0
                else "low"
                if z_score < -1.0
                else "normal",
            }
        )
    return result


@router.get("/et/cached")
def get_cached_locations(
    start_date: str = "2022-01-01",
    end_date: str = "2023-12-31",
):
    """Return all cached coordinates for a given date range."""
    db: Session = SessionLocal()
    try:
        cached = (
            db.query(ETCache.longitude, ETCache.latitude)
            .filter(
                ETCache.start_date == start_date,
                ETCache.end_date == end_date,
            )
            .distinct()
            .all()
        )
        return [{"longitude": c.longitude, "latitude": c.latitude} for c in cached]
    finally:
        db.close()


@router.get("/et/point")
def get_et_point(
    longitude: float = -77.05,
    latitude: float = 42.66,
    start_date: str = "2022-01-01",
    end_date: str = "2023-12-31",
):
    db: Session = SessionLocal()

    lng = round(longitude, 2)
    lat = round(latitude, 2)

    try:
        cached = (
            db.query(ETCache)
            .filter(
                ETCache.longitude == lng,
                ETCache.latitude == lat,
                ETCache.start_date == start_date,
                ETCache.end_date == end_date,
            )
            .first()
        )

        if cached:
            print(f"CACHE HIT: {lng}, {lat}")
            data = json.loads(cached.data)
            return detect_anomalies(data)

        headers = {
            "Authorization": os.getenv("OPENET_API_KEY"),
            "Content-Type": "application/json",
        }
        payload = {
            "date_range": [start_date, end_date],
            "interval": "monthly",
            "geometry": [lng, lat],
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

        log = QueryLog(
            longitude=lng,
            latitude=lat,
            start_date=start_date,
            end_date=end_date,
            success=response.status_code == 200,
        )
        db.add(log)
        db.commit()

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        data = response.json()
        print(f"API CALL: {lng}, {lat}")

        cache_entry = ETCache(
            longitude=lng,
            latitude=lat,
            start_date=start_date,
            end_date=end_date,
            data=json.dumps(data),
        )
        db.add(cache_entry)
        db.commit()

        return detect_anomalies(data)

    finally:
        db.close()
