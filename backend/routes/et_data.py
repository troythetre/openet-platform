import json
import os
from collections import defaultdict
from datetime import datetime

import requests
from auth_utils import get_current_user, get_current_user_optional
from database import ComparisonSet, ETCache, QueryLog, SavedLocation, SearchHistory, SessionLocal, User
from fastapi import APIRouter, Depends, HTTPException, Request
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
    """Fetch raw ET time series for a point, using cache if available."""
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


def _log_history_if_authenticated(
    request: Request, lng: float, lat: float, start_date: str, end_date: str, db: Session
):
    """Best-effort history logging — silently skips if not logged in or
    if anything goes wrong, since this should never block the actual
    ET lookup from succeeding.
    """
    try:
        user = get_current_user_optional(request)
        if not user:
            return
        entry = SearchHistory(
            user_id=user.id,
            longitude=lng,
            latitude=lat,
            start_date=start_date,
            end_date=end_date,
        )
        db.add(entry)
        db.commit()
    except Exception:
        pass


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
    request: Request,
    longitude: float = -77.05,
    latitude: float = 42.66,
    start_date: str = "2022-01-01",
    end_date: str = "2023-12-31",
):
    db: Session = SessionLocal()
    try:
        data = fetch_et_series(longitude, latitude, start_date, end_date, db)
        _log_history_if_authenticated(request, longitude, latitude, start_date, end_date, db)
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
                    point.longitude, point.latitude, request.start_date, request.end_date, db
                )
                analyzed = detect_anomalies(raw)
                total = round(sum(d["et"] for d in analyzed), 2)
                avg = round(total / len(analyzed), 2) if analyzed else 0
                anomaly_count = sum(1 for d in analyzed if d["anomaly"])

                monthly_avg = defaultdict(list)
                for d in analyzed:
                    month = int(d["time"][5:7])
                    monthly_avg[month].append(d["et"])
                monthly_series = [
                    round(sum(monthly_avg.get(m, [0])) / max(len(monthly_avg.get(m, [1])), 1), 2)
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


# ---------- Saved fields (requires login) ----------


class SaveFieldRequest(BaseModel):
    name: str
    longitude: float
    latitude: float


@router.get("/fields")
def list_fields(user: User = Depends(get_current_user)):
    db: Session = SessionLocal()
    try:
        fields = (
            db.query(SavedLocation)
            .filter(SavedLocation.user_id == user.id)
            .order_by(SavedLocation.created_at.desc())
            .all()
        )
        return [
            {"id": f.id, "name": f.name, "longitude": f.longitude, "latitude": f.latitude}
            for f in fields
        ]
    finally:
        db.close()


@router.post("/fields")
def save_field(request: SaveFieldRequest, user: User = Depends(get_current_user)):
    db: Session = SessionLocal()
    try:
        field = SavedLocation(
            user_id=user.id,
            name=request.name,
            longitude=request.longitude,
            latitude=request.latitude,
        )
        db.add(field)
        db.commit()
        db.refresh(field)
        return {"id": field.id, "name": field.name, "longitude": field.longitude, "latitude": field.latitude}
    finally:
        db.close()


@router.delete("/fields/{field_id}")
def delete_field(field_id: int, user: User = Depends(get_current_user)):
    db: Session = SessionLocal()
    try:
        field = (
            db.query(SavedLocation)
            .filter(SavedLocation.id == field_id, SavedLocation.user_id == user.id)
            .first()
        )
        if not field:
            raise HTTPException(status_code=404, detail="Field not found")
        db.delete(field)
        db.commit()
        return {"deleted": True, "id": field_id}
    finally:
        db.close()


# ---------- Search history (requires login) ----------


@router.get("/history")
def list_history(user: User = Depends(get_current_user), limit: int = 50):
    db: Session = SessionLocal()
    try:
        entries = (
            db.query(SearchHistory)
            .filter(SearchHistory.user_id == user.id)
            .order_by(SearchHistory.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": h.id,
                "longitude": h.longitude,
                "latitude": h.latitude,
                "start_date": h.start_date,
                "end_date": h.end_date,
                "created_at": h.created_at.isoformat(),
            }
            for h in entries
        ]
    finally:
        db.close()


@router.delete("/history")
def clear_history(user: User = Depends(get_current_user)):
    db: Session = SessionLocal()
    try:
        db.query(SearchHistory).filter(SearchHistory.user_id == user.id).delete()
        db.commit()
        return {"cleared": True}
    finally:
        db.close()


# ---------- Comparison sets (requires login) ----------


class SaveComparisonSetRequest(BaseModel):
    name: str
    fields: list[ComparePoint]


@router.get("/comparison-sets")
def list_comparison_sets(user: User = Depends(get_current_user)):
    db: Session = SessionLocal()
    try:
        sets = (
            db.query(ComparisonSet)
            .filter(ComparisonSet.user_id == user.id)
            .order_by(ComparisonSet.created_at.desc())
            .all()
        )
        return [
            {
                "id": s.id,
                "name": s.name,
                "fields": json.loads(s.fields_json),
                "created_at": s.created_at.isoformat(),
            }
            for s in sets
        ]
    finally:
        db.close()


@router.post("/comparison-sets")
def save_comparison_set(request: SaveComparisonSetRequest, user: User = Depends(get_current_user)):
    db: Session = SessionLocal()
    try:
        cs = ComparisonSet(
            user_id=user.id,
            name=request.name,
            fields_json=json.dumps([f.dict() for f in request.fields]),
        )
        db.add(cs)
        db.commit()
        db.refresh(cs)
        return {"id": cs.id, "name": cs.name, "fields": [f.dict() for f in request.fields]}
    finally:
        db.close()


@router.delete("/comparison-sets/{set_id}")
def delete_comparison_set(set_id: int, user: User = Depends(get_current_user)):
    db: Session = SessionLocal()
    try:
        cs = (
            db.query(ComparisonSet)
            .filter(ComparisonSet.id == set_id, ComparisonSet.user_id == user.id)
            .first()
        )
        if not cs:
            raise HTTPException(status_code=404, detail="Comparison set not found")
        db.delete(cs)
        db.commit()
        return {"deleted": True, "id": set_id}
    finally:
        db.close()
