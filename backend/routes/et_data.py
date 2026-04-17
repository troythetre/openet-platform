import json
import os
from datetime import datetime

import requests
from database import ETCache, QueryLog, SessionLocal
from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

router = APIRouter()

OPENET_BASE_URL = "https://openet-api.org"


def detect_anomalies(data: list) -> list:
    values = [d["et"] for d in data]
    mean = sum(values) / len(values)
    std = (sum((x - mean) ** 2 for x in values) / len(values)) ** 0.5

    result = []
    for d in data:
        z_score = (d["et"] - mean) / std if std > 0 else 0
        anomaly = abs(z_score) > 1.0
        result.append(
            {
                "time": d["time"],
                "et": d["et"],
                "mean": round(mean, 3),
                "z_score": round(z_score, 3),
                "anomaly": anomaly,
                "anomaly_type": "high"
                if z_score > 1.5
                else "low"
                if z_score < -1.5
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
    start_date: str = "2023-01-01",
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
