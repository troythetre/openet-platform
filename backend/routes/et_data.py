import json
import os
from collections import defaultdict
from datetime import datetime

import requests
from database import ETCache, QueryLog, SavedLocation, SessionLocal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
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


def fetch_et_series(
    lng: float, lat: float, start_date: str, end_date: str, db: Session
) -> list:
    """Fetch raw ET time series for a point, using cache if available.
    Shared by /et/point and /et/compare so both hit the same cache and
    the same OpenET quota accounting.
    """
    lng = round(lng, 2)
    lat = round(lat, 2)

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
        return json.loads(cached.data)

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

    return data


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
    try:
        data = fetch_et_series(longitude, latitude, start_date, end_date, db)
        return detect_anomalies(data)
    finally:
        db.close()


# ---------- Multi-field comparison ----------


class ComparePoint(BaseModel):
    label: str
    longitude: float
    latitude: float


class CompareRequest(BaseModel):
    points: list[ComparePoint]
    start_date: str = "2022-01-01"
    end_date: str = "2023-12-31"


@router.post("/et/compare")
def compare_fields(request: CompareRequest):
    """Fetch ET data for multiple fields at once for side-by-side comparison.
    Each field is fetched/cached independently via fetch_et_series, so
    fields already viewed individually will be cache hits here too.
    """
    if len(request.points) < 1:
        raise HTTPException(status_code=400, detail="At least one point is required")
    if len(request.points) > 8:
        raise HTTPException(status_code=400, detail="Maximum 8 fields per comparison")

    db: Session = SessionLocal()
    results = []
    try:
        for point in request.points:
            try:
                raw = fetch_et_series(
                    point.longitude,
                    point.latitude,
                    request.start_date,
                    request.end_date,
                    db,
                )
                analyzed = detect_anomalies(raw)
                total = round(sum(d["et"] for d in analyzed), 2)
                avg = round(total / len(analyzed), 2) if analyzed else 0
                anomaly_count = sum(1 for d in analyzed if d["anomaly"])

                # Average ET per calendar month across all years in range,
                # for a clean "typical year" comparison line
                monthly_avg = defaultdict(list)
                for d in analyzed:
                    month = int(d["time"][5:7])
                    monthly_avg[month].append(d["et"])
                monthly_series = [
                    round(
                        sum(monthly_avg.get(m, [0]))
                        / max(len(monthly_avg.get(m, [1])), 1),
                        2,
                    )
                    for m in range(1, 13)
                ]

                results.append(
                    {
                        "label": point.label,
                        "longitude": point.longitude,
                        "latitude": point.latitude,
                        "total_et": total,
                        "avg_monthly_et": avg,
                        "anomaly_count": anomaly_count,
                        "monthly_avg": monthly_series,
                        "data": analyzed,
                        "error": None,
                    }
                )
            except HTTPException as e:
                results.append(
                    {
                        "label": point.label,
                        "longitude": point.longitude,
                        "latitude": point.latitude,
                        "error": str(e.detail),
                    }
                )
        return {"fields": results}
    finally:
        db.close()


# ---------- Saved fields ----------


class SaveFieldRequest(BaseModel):
    name: str
    longitude: float
    latitude: float


@router.get("/fields")
def list_fields():
    db: Session = SessionLocal()
    try:
        fields = db.query(SavedLocation).order_by(SavedLocation.created_at.desc()).all()
        return [
            {
                "id": f.id,
                "name": f.name,
                "longitude": f.longitude,
                "latitude": f.latitude,
            }
            for f in fields
        ]
    finally:
        db.close()


@router.post("/fields")
def save_field(request: SaveFieldRequest):
    db: Session = SessionLocal()
    try:
        field = SavedLocation(
            name=request.name,
            longitude=request.longitude,
            latitude=request.latitude,
        )
        db.add(field)
        db.commit()
        db.refresh(field)
        return {
            "id": field.id,
            "name": field.name,
            "longitude": field.longitude,
            "latitude": field.latitude,
        }
    finally:
        db.close()


@router.delete("/fields/{field_id}")
def delete_field(field_id: int):
    db: Session = SessionLocal()
    try:
        field = db.query(SavedLocation).filter(SavedLocation.id == field_id).first()
        if not field:
            raise HTTPException(status_code=404, detail="Field not found")
        db.delete(field)
        db.commit()
        return {"deleted": True, "id": field_id}
    finally:
        db.close()
